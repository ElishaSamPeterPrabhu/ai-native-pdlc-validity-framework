"""Round-over-round validity deltas for AI-guided improvement.

CLI computes what worsened (facts). AI uses metric-playbooks.json to explain
why and suggest the next single intervention.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from framework.provenance import scoring_block

_PLAYBOOKS = Path(__file__).resolve().parent / "catalog" / "metric-playbooks.json"

IMPROVE_PROMPT = """A setup was rated, then a later round got worse.

Using ONLY this delta pack and metric-playbooks.json (domain-agnostic top-level metrics):

1. Map every failure/success signal to the nearest top-level metric
   (V_obs, V_star, Hc, O, Cb, sigma_spec, R_recovery, pass_at_1).
   Cite the evidence snippet. Do not invent stack-specific metrics.
2. List which of those metrics worsened (before → after).
3. For each worsened metric, explain what it means generically and how it
   applies in THIS team's workflow.
4. Propose ONE next change for the dominant metric: prefer a control_class,
   then a concrete intervention if available. State raise-R vs lower-D and retest.
5. If nothing fits, propose a trial-and-error candidate and how to measure it.
6. Suggest review depth until recovery (human review never zero).

Ownership:
- CLI intake_heuristic_scores are NON-AUTHORITATIVE hints only (not R/D/V*).
- YOU (AI) own the authoritative metric assessment in diagnosis.json /
  improvement-plan.json — cite evidence; human approval on apply is required,
  not on every metric judgment.
- When citing R, D, or V*, quote `python -m framework score` output only;
  never invent formula equilibria or fitted weights.

One change per round.
"""


def load_playbooks() -> dict[str, Any]:
    return json.loads(_PLAYBOOKS.read_text(encoding="utf-8"))


def _stratum_means(report: dict[str, Any]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for stratum, row in (report.get("by_stratum") or {}).items():
        out[stratum] = row.get("mean_v_obs")
    return out


def _safe_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def compare_reports(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    before_label: str = "round_good",
    after_label: str = "round_failed",
) -> dict[str, Any]:
    """Compare two validity-report style documents."""
    worsened: list[dict[str, Any]] = []
    improved: list[dict[str, Any]] = []

    b_means = _stratum_means(before)
    a_means = _stratum_means(after)
    for stratum in sorted(set(b_means) | set(a_means)):
        b, a = b_means.get(stratum), a_means.get(stratum)
        if b is None or a is None:
            continue
        entry = {
            "metric": "V_obs",
            "stratum": stratum,
            "before": b,
            "after": a,
            "delta": round(a - b, 4),
        }
        if a < b - 1e-9:
            worsened.append(entry)
        elif a > b + 1e-9:
            improved.append(entry)

    for key, label in (
        ("n_runs", "n_runs"),
        ("evidence_status", "evidence_status"),
    ):
        if before.get(key) != after.get(key):
            # informational only
            pass

    playbooks = load_playbooks()
    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "delta_kind": "validity_report",
        "before_label": before_label,
        "after_label": after_label,
        "scoring": scoring_block(
            scoring_method="report_stratum_delta",
            evidence_status="observed",
            formula_used=False,
        ),
        "worsened": worsened,
        "improved": improved,
        "dominant_worsened_metric": (
            min(worsened, key=lambda e: e["delta"])["metric"] if worsened else None
        ),
        "playbooks_path": "framework/catalog/metric-playbooks.json",
        "ai_mapping_rule": playbooks.get("ai_mapping_rule", {}),
        "failure_to_metric_hints": playbooks.get("failure_to_metric_hints", []),
        "trial_and_error": playbooks.get("trial_and_error", {}),
        "improve_instructions": IMPROVE_PROMPT,
        "claim_warnings": [
            "Delta facts are CLI-owned; intervention choice is AI-owned",
            "Change one control per round; retest same stratum",
            "Report deltas compare V_obs strata only; AI owns other metric judgments",
        ],
    }


def compare_intake_rounds(
    before_intake: dict[str, Any],
    after_intake: dict[str, Any],
    *,
    before_label: str = "round_good",
    after_label: str = "round_failed",
) -> dict[str, Any]:
    """Qualitative delta from two user-intake PR bundles."""
    playbooks = load_playbooks()
    worsened_metrics: list[dict[str, Any]] = []

    def _pr_fail_score(pr: dict[str, Any]) -> dict[str, Any]:
        score = {
            "V_obs": 1.0,
            "Hc": 0.0,
            "O": 0.0,
            "Cb": 0.0,
            "sigma_spec": 0.0,
            "R_recovery": 1.0,
            "pass_at_1": 1.0,
        }
        if pr.get("ci_status") == "fail" or pr.get("what_failed_or_surprised"):
            score["V_obs"] = 0.0
        if pr.get("agent_claimed_done") and pr.get("what_failed_or_surprised"):
            score["V_obs"] = 0.0
            score["R_recovery"] = 0.3
            score["pass_at_1"] = 0.0
        signals = pr.get("formula_signals") or {}
        if "debug" in (signals.get("entropy_notes") or "").lower() or "fail" in (
            signals.get("entropy_notes") or ""
        ).lower():
            score["Hc"] = 0.8
        if (pr.get("files_changed") or 0) >= 8 or (pr.get("lines_changed") or 0) >= 200:
            score["O"] = 0.6
        if "shared" in (signals.get("blast_radius_notes") or "").lower():
            score["Cb"] = 0.7
        if "vague" in (signals.get("spec_ambiguity_notes") or "").lower() or not pr.get(
            "acceptance_criteria"
        ):
            score["sigma_spec"] = 0.6
        if not (signals.get("recovery_seen") or []):
            score["R_recovery"] = min(score["R_recovery"], 0.4)
        if (pr.get("fix_iterations") or 0) >= 1:
            score["pass_at_1"] = 0.0
        return score

    def _avg(prs: list[dict]) -> dict[str, float]:
        if not prs:
            return {}
        keys = ["V_obs", "Hc", "O", "Cb", "sigma_spec", "R_recovery", "pass_at_1"]
        acc = {k: 0.0 for k in keys}
        for pr in prs:
            s = _pr_fail_score(pr)
            for k in keys:
                acc[k] += s[k]
        n = float(len(prs))
        return {k: round(acc[k] / n, 4) for k in keys}

    b = _avg(before_intake.get("prs") or [])
    a = _avg(after_intake.get("prs") or [])
    # For decay metrics Hc/O/Cb/sigma, higher = worse. For V_obs/R/pass_at_1, lower = worse.
    decay_ids = {"Hc", "O", "Cb", "sigma_spec"}
    for metric, bv in b.items():
        av = a.get(metric)
        if av is None:
            continue
        if metric in decay_ids:
            delta = round(av - bv, 4)
            worse = av > bv + 1e-9
        else:
            delta = round(av - bv, 4)
            worse = av < bv - 1e-9
        entry = {"metric": metric, "before": bv, "after": av, "delta": delta}
        if worse:
            worsened_metrics.append(entry)

    # Narrative failures from after PRs
    failure_notes = []
    for pr in after_intake.get("prs") or []:
        if pr.get("what_failed_or_surprised"):
            failure_notes.append(
                {
                    "pr": pr.get("url_or_number"),
                    "note": pr.get("what_failed_or_surprised"),
                    "agent_claimed_done": pr.get("agent_claimed_done"),
                    "fix_iterations": pr.get("fix_iterations"),
                }
            )

    # Hint match
    hints_hit = []
    blob = " ".join(n["note"].lower() for n in failure_notes)
    for hint in playbooks.get("failure_to_metric_hints", []):
        # rough keyword overlap with pattern words
        words = [w for w in hint["pattern"].lower().split() if len(w) > 3]
        if sum(1 for w in words if w in blob) >= max(1, len(words) // 2):
            hints_hit.append(hint)

    dominant = None
    if worsened_metrics:
        # prefer largest harmful move
        def harm(e: dict) -> float:
            if e["metric"] in decay_ids:
                return e["delta"]
            return -e["delta"]

        dominant = max(worsened_metrics, key=harm)["metric"]

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "delta_kind": "intake_heuristic",
        "before_label": before_label,
        "after_label": after_label,
        "scoring": scoring_block(
            scoring_method="intake_keyword_heuristic",
            evidence_status="unmeasured",
            formula_used=False,
        ),
        "intake_heuristic_scores_before": b,
        "intake_heuristic_scores_after": a,
        "worsened": worsened_metrics,
        "dominant_worsened_metric": dominant,
        "failure_notes": failure_notes,
        "matched_failure_hints": hints_hit,
        "playbooks_path": "framework/catalog/metric-playbooks.json",
        "ai_mapping_rule": playbooks.get("ai_mapping_rule", {}),
        "top_level_metrics": playbooks.get("top_level_metrics", []),
        "control_classes": playbooks.get("control_classes", {}),
        "trial_and_error": playbooks.get("trial_and_error", {}),
        "improve_instructions": IMPROVE_PROMPT,
        "claim_warnings": [
            "intake_heuristic_scores are keyword hints only — NOT R/D/V* formula outputs",
            "AI owns authoritative metric assessment; may override these hints with evidence",
            "Run `python -m framework score` for CLI-owned R/D/V* when proxies exist",
        ],
        "next_user_steps": [
            "Run Cursor skill validity-improve-from-delta (or validity-diagnose) on this pack",
            "Approve ONE intervention",
            "Retest same stratum; save a new intake/report as the next after=",
            "If a new failure mode appears, log trial_and_error.record_template",
        ],
    }


def write_delta(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
