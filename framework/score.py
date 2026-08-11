"""CLI-owned formula scoring: R, D, V* with explicit provenance."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from theory import formula as F

from framework.adapters.github_diff import (
    opacity_from_diff_stats,
    provisional_v_star,
)
from framework.provenance import measured, scoring_block, unwrap_value


def _activities_from_record(rec: dict[str, Any]) -> dict[str, float]:
    activities: dict[str, float] = {}
    factors = rec.get("factor_activity") or rec.get("factors") or {}
    if isinstance(factors, dict):
        for k, v in factors.items():
            if isinstance(v, (int, float)):
                activities[k] = float(v)
            elif v is True:
                activities[k] = 1.0
            elif v is False:
                activities[k] = 0.0
    if not activities:
        activities = {
            n: 1.0 for n in F.CORE_FITTED_FACTORS if n != "review_bot"
        }
    return {k: v for k, v in activities.items() if k in F.REGISTRY_BY_NAME}


def _decay_inputs_from_record(rec: dict[str, Any]) -> tuple[F.DecayInputs | None, bool]:
    proxies = rec.get("decay_proxies") or rec.get("proxies") or {}

    def _val(key: str) -> float | None:
        raw = proxies.get(key, rec.get(key))
        return unwrap_value(raw, None)

    entropy = _val("entropy")
    opacity = _val("opacity")
    blast = _val("blast_radius")
    spec = _val("spec_ambiguity")
    has_any = any(v is not None for v in (entropy, opacity, blast, spec))
    if not has_any:
        return None, False
    return F.DecayInputs(
        entropy=entropy if entropy is not None else 0.3,
        opacity=opacity if opacity is not None else 0.3,
        blast_radius=blast if blast is not None else 0.2,
        spec_ambiguity=spec if spec is not None else 0.3,
    ), True


def _decay_inputs_from_intake_pr(pr: dict[str, Any]) -> tuple[F.DecayInputs | None, bool]:
    files = pr.get("files_changed") or 0
    lines = pr.get("lines_changed") or 0
    signals = pr.get("formula_signals") or {}

    opacity_mv = opacity_from_diff_stats(float(lines), int(files))
    opacity = unwrap_value(opacity_mv, None)

    entropy = None
    notes = (signals.get("entropy_notes") or "").lower()
    if "debug" in notes or "fail" in notes:
        entropy = 0.8
    elif notes:
        entropy = 0.5

    blast = None
    if "shared" in (signals.get("blast_radius_notes") or "").lower():
        blast = 0.7

    spec = None
    if "vague" in (signals.get("spec_ambiguity_notes") or "").lower():
        spec = 0.6
    elif not pr.get("acceptance_criteria"):
        spec = 0.5

    if not notes and not files and not lines:
        return None, False

    return F.DecayInputs(
        entropy=entropy if entropy is not None else 0.3,
        opacity=opacity if opacity is not None else 0.3,
        blast_radius=blast if blast is not None else 0.2,
        spec_ambiguity=spec if spec is not None else 0.3,
    ), True


def score_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Score a single run-record or intake pseudo-record."""
    activities = _activities_from_record(rec)
    decay, has_inputs = _decay_inputs_from_record(rec)

    r_val = F.recovery_rate(activities)
    d_val = F.decay_rate(decay, form=F.DecayForm.HYBRID) if decay else None
    v_star = (
        F.equilibrium_validity(r_val, d_val)
        if d_val is not None
        else None
    )

    proxies_out: dict[str, Any] = {}
    if decay:
        proxies_out["entropy"] = measured(
            decay.entropy, source="observed", confidence="medium", method="record_proxy"
        )
        proxies_out["opacity"] = measured(
            decay.opacity, source="observed", confidence="medium", method="record_proxy"
        )
        proxies_out["blast_radius"] = measured(
            decay.blast_radius, source="observed", confidence="medium", method="record_proxy"
        )
        proxies_out["spec_ambiguity"] = measured(
            decay.spec_ambiguity, source="observed", confidence="medium", method="record_proxy"
        )

    return {
        "run_id": rec.get("run_id"),
        "record_kind": rec.get("record_kind", "run_record"),
        "R": measured(
            r_val,
            source="observed" if activities else "imputed",
            confidence="medium" if activities else "low",
            method="recovery_rate",
            weight_source="placeholder",
        ),
        "D": measured(
            d_val,
            source="observed" if has_inputs else "missing",
            confidence="medium" if has_inputs else "none",
            method="decay_rate_hybrid" if d_val is not None else "missing_inputs",
            weight_source="placeholder" if d_val is not None else "none",
            notes=None if has_inputs else "decay proxies missing; D not computed",
        ),
        "V_star": measured(
            v_star,
            source="observed" if v_star is not None else "missing",
            confidence="medium" if v_star is not None else "none",
            method="equilibrium_validity",
            weight_source="placeholder" if v_star is not None else "none",
            notes=None if v_star is not None else "cannot compute V* without decay proxies",
        ),
        "decay_proxies": proxies_out,
        "recovery_activities": activities,
    }


def score_intake_pr(pr: dict[str, Any]) -> dict[str, Any]:
    """Score a single PR from user-intake."""
    signals = pr.get("formula_signals") or {}
    recovery = signals.get("recovery_seen") or []
    activities = {name: 1.0 for name in recovery if name in F.REGISTRY_BY_NAME}
    if not activities:
        activities = {n: 0.4 for n in ("agentic_qa", "fix_loop") if n in F.REGISTRY_BY_NAME}

    decay, has_inputs = _decay_inputs_from_intake_pr(pr)

    r_val = F.recovery_rate(activities)
    d_val = F.decay_rate(decay, form=F.DecayForm.HYBRID) if decay else None
    v_star = F.equilibrium_validity(r_val, d_val) if d_val is not None else None

    return {
        "pr": pr.get("url_or_number"),
        "record_kind": "intake_pseudo",
        "R": measured(
            r_val,
            source="heuristic",
            confidence="low",
            method="recovery_rate_from_intake_signals",
            weight_source="placeholder",
        ),
        "D": measured(
            d_val,
            source="heuristic" if has_inputs else "missing",
            confidence="low" if has_inputs else "none",
            method="decay_rate_hybrid_from_intake",
            weight_source="placeholder" if d_val is not None else "none",
        ),
        "V_star": measured(
            v_star,
            source="heuristic" if v_star is not None else "missing",
            confidence="low" if v_star is not None else "none",
            method="equilibrium_validity",
            weight_source="placeholder" if v_star is not None else "none",
            notes="intake-derived; not live telemetry",
        ),
    }


def build_score_pack(
    *,
    records: list[dict[str, Any]] | None = None,
    intake_prs: list[dict[str, Any]] | None = None,
    repo: str = "",
) -> dict[str, Any]:
    """Build a score pack from run records and/or intake PRs."""
    scored_runs = [score_record(r) for r in (records or [])]
    scored_prs = [score_intake_pr(pr) for pr in (intake_prs or [])]

    v_stars = [
        unwrap_value(s["V_star"])
        for s in scored_runs + scored_prs
        if unwrap_value(s["V_star"]) is not None
    ]
    aggregate_v_star = (
        round(sum(v_stars) / len(v_stars), 4) if v_stars else None
    )

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formula_version": F.FORMULA_VERSION,
        "repo": repo,
        "scoring": scoring_block(
            scoring_method="formula_equilibrium",
            evidence_status=F.EVIDENCE_STATUS,
            formula_used=True,
            weight_source="placeholder",
        ),
        "runs": scored_runs,
        "intake_prs": scored_prs,
        "aggregate": {
            "V_star": measured(
                aggregate_v_star,
                source="observed" if aggregate_v_star is not None else "missing",
                confidence="medium" if aggregate_v_star is not None else "none",
                method="mean_equilibrium_validity",
                weight_source="placeholder" if aggregate_v_star is not None else "none",
            ),
            "n_scored": len(scored_runs) + len(scored_prs),
        },
        "claim_warnings": [
            f"formula {F.FORMULA_VERSION} weight_source=placeholder (not repo-fitted)",
            "AI owns metric judgments; CLI owns R/D/V* numbers here",
            "Do not treat intake PR scores as live harness telemetry",
        ],
    }


def load_input(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Load run records or intake from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    repo = data.get("repo", "")

    if "prs" in data:
        return [], data.get("prs") or [], repo

    if isinstance(data, list):
        return data, [], repo

    if "runs" in data or "final_v_obs" in data or "run_id" in data:
        if "run_id" in data:
            return [data], [], repo
        return data.get("runs") or [data], [], repo

    return [], [], repo


def write_score_pack(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
