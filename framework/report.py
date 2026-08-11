"""Build setup-validity profiles and validity reports from run records."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from theory import formula as F

from framework.adapters.github_diff import bootstrap_mean_ci, provisional_v_star
from framework.factor_catalog import LAYER_BY_FACTOR
from framework.provenance import measured, unwrap_value


def load_metrics_jsonl(path: str | Path, *, exclude_synthetic: bool = True) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if exclude_synthetic and rec.get("synthetic"):
                continue
            records.append(rec)
    return records


def _pass_hat_k_for_group(passes: list[bool]) -> float:
    return F.pass_hat_k(sum(1 for p in passes if p), len(passes)) if passes else 0.0


def review_lane_for_stratum(mean_v: float | None, n: int, evidence_status: str) -> str:
    if n <= 0 or mean_v is None:
        return "insufficient-evidence"
    if evidence_status in {"unmeasured", "observed"} and n < 3:
        return "insufficient-evidence"
    if mean_v >= 0.85:
        return "minimal"
    if mean_v >= 0.55:
        return "high-level"
    return "deep"


def diagnose_layers(records: list[dict], manifest: dict | None = None) -> dict[str, Any]:
    """Non-authoritative keyword heuristic for smoke tests only.

    Authoritative diagnosis belongs to the AI skill layer
    (``.cursor/skills/validity-diagnose``) reading an evidence pack from
    ``python -m framework evidence``.
    """
    scores = {"harness": 0.0, "loop": 0.0, "graph": 0.0}
    reasons: list[str] = []
    controls: list[str] = []

    if manifest:
        for gap in manifest.get("measurement_gaps", []):
            gl = gap.lower()
            if (
                gl.startswith("harness")
                or "mcp" in gl
                or ".cursor/rules" in gl
                or gl.startswith("rules_context")
            ):
                scores["harness"] += 1.0
                reasons.append(gap)
            elif (
                gl.startswith("loop")
                or "completion_guard" in gl
                or "ci_gate" in gl
                or "ci/" in gl
                or "workflow gate" in gl
                or "agentic_qa" in gl
                or "fix_loop" in gl
                or "verifier" in gl
            ):
                scores["loop"] += 1.0
                reasons.append(gap)
            elif (
                gl.startswith("graph")
                or "spec_refinement" in gl
                or "review_bot" in gl
                or "handoff" in gl
                or "label" in gl
            ):
                scores["graph"] += 1.0
                reasons.append(gap)
            else:
                scores["graph"] += 0.5
                reasons.append(gap)

    # Outcome pressure: if high stratum fails more, prioritize loop recovery.
    by_stratum: dict[str, list[float]] = defaultdict(list)
    for r in records:
        v = r.get("final_v_obs")
        if v is not None:
            by_stratum[r.get("stratum", "unknown")].append(float(v))
    high = by_stratum.get("high") or by_stratum.get("medium")
    low = by_stratum.get("low")
    if high and low and (float(np.mean(high)) + 0.15 < float(np.mean(low))):
        scores["loop"] += 1.5
        reasons.append("validity drops sharply on harder strata → strengthen recovery loop")
        controls.extend(["agentic_qa", "fix_loop", "completion_guard_hook", "ci_gate"])

    # Disabled factors in ablation arms are a weak secondary signal only.
    # Prefer manifest gaps and outcome strata; ignore synthetic-only noise.
    real_records = [r for r in records if not r.get("synthetic")]
    disabled_counts: dict[str, int] = defaultdict(int)
    for r in real_records:
        if r.get("arm") in {None, "baseline"}:
            continue
        factors = r.get("factors") or r.get("factor_state") or {}
        if isinstance(factors, dict):
            for name, enabled in factors.items():
                if enabled is False:
                    disabled_counts[name] += 1
    for name, count in sorted(disabled_counts.items(), key=lambda kv: -kv[1])[:5]:
        layer = LAYER_BY_FACTOR.get(name, "unknown")
        if layer in scores:
            scores[layer] += min(1.0, 0.05 * count)

    if not any(scores.values()):
        return {
            "weakest_layer": "unknown",
            "rationale": "insufficient evidence to attribute weakness to a layer",
            "recommended_controls": ["instrument Level 1 collectors", "run baseline tasks"],
        }

    weakest = max(scores, key=scores.get)
    layer_defaults = {
        "harness": ["rules_context", "mcp_context", "checkpointing"],
        "loop": ["ci_gate", "agentic_qa", "fix_loop", "completion_guard_hook"],
        "graph": ["spec_refinement", "review_bot", "label-handoff instrumentation"],
    }
    controls = list(layer_defaults.get(weakest, []))
    for name, _count in sorted(disabled_counts.items(), key=lambda kv: -kv[1])[:3]:
        if LAYER_BY_FACTOR.get(name) == weakest:
            controls.insert(0, name)

    return {
        "weakest_layer": weakest,
        "rationale": "; ".join(reasons[:5]) or f"highest gap score on {weakest}",
        "recommended_controls": list(dict.fromkeys(controls))[:8],
    }


def _provisional_v_star_for_group(group: list[dict]) -> dict[str, Any]:
    """Compute V* from group records when decay proxies exist; else missing."""
    v_stars: list[float] = []
    for r in group:
        proxies = r.get("decay_proxies") or r.get("proxies") or {}
        activities = r.get("factor_activity") or r.get("factors") or {}
        act: dict[str, float] = {}
        if isinstance(activities, dict):
            for k, v in activities.items():
                if isinstance(v, (int, float)):
                    act[k] = float(v)
                elif v is True:
                    act[k] = 1.0
        if not act:
            act = {n: 1.0 for n in F.CORE_FITTED_FACTORS if n != "review_bot"}

        def _proxy(key: str) -> float | None:
            raw = proxies.get(key, r.get(key))
            return unwrap_value(raw, None)

        entropy = _proxy("entropy")
        opacity = _proxy("opacity")
        blast = _proxy("blast_radius")
        spec = _proxy("spec_ambiguity")
        if all(v is None for v in (entropy, opacity, blast, spec)):
            continue
        inputs = F.DecayInputs(
            entropy=entropy if entropy is not None else 0.3,
            opacity=opacity if opacity is not None else 0.3,
            blast_radius=blast if blast is not None else 0.2,
            spec_ambiguity=spec if spec is not None else 0.3,
        )
        v_stars.append(provisional_v_star(act, inputs))

    if not v_stars:
        return measured(
            None,
            source="missing",
            confidence="none",
            method="equilibrium_validity",
            weight_source="none",
            notes="decay proxies missing; V* not computed (never aliased to mean_v_obs)",
        )
    mean_v_star = round(float(np.mean(v_stars)), 4)
    return measured(
        mean_v_star,
        source="observed",
        confidence="medium",
        method="equilibrium_validity",
        weight_source="placeholder",
        notes=f"aggregated from {len(v_stars)} runs with proxies",
    )


def build_validity_report(
    records: list[dict],
    *,
    repo: str = "",
    manifest: dict | None = None,
    include_synthetic_warning: bool = True,
) -> dict[str, Any]:
    evidence_status = F.EVIDENCE_STATUS
    if records and all(r.get("synthetic") for r in records):
        evidence_status = "simulation-calibrated"

    by_stratum: dict[str, Any] = {}
    for stratum in ("low", "medium", "high"):
        group = [r for r in records if r.get("stratum") == stratum]
        vs = [float(r["final_v_obs"]) for r in group if r.get("final_v_obs") is not None]
        passes = [bool(r.get("final_pass")) for r in group if "final_pass" in r]
        by_task: dict[str, list[bool]] = defaultdict(list)
        for r in group:
            if "final_pass" in r:
                by_task[r.get("task", "unknown")].append(bool(r["final_pass"]))
        pk = [_pass_hat_k_for_group(g) for g in by_task.values()]
        mean_v = round(float(np.mean(vs)), 4) if vs else None
        by_stratum[stratum] = {
            "n": len(group),
            "mean_v_obs": mean_v,
            "v_obs_ci": list(bootstrap_mean_ci(vs)),
            "pass_at_1": round(float(np.mean(passes)), 4) if passes else None,
            "pass_hat_k": round(float(np.mean(pk)), 4) if pk else None,
            "provisional_v_star": _provisional_v_star_for_group(group),
            "review_lane": review_lane_for_stratum(mean_v, len(group), evidence_status),
        }

    warnings = [
        f"formula {F.FORMULA_VERSION} evidence_status={evidence_status}",
        "placeholder weights are not Modus-fitted factory calibration",
        "human review is never removed; lanes scale depth only",
    ]
    if include_synthetic_warning and not records:
        warnings.append(
            "no non-synthetic run records found; report is structure-only / observe-level"
        )
    if "completion_guard_hook" in F.SIMULATION_ONLY_FACTORS:
        warnings.append("completion_guard_hook effects are simulation-only until live telemetry")

    coverage = {
        "final_v_obs": _coverage(records, "final_v_obs"),
        "stages": _coverage_stages(records),
        "opacity": _coverage_nested(records, "opacity"),
    }

    warnings.append(
        "layer diagnosis and final review policy are AI-owned; "
        "run `python -m framework evidence` then validity-diagnose skill"
    )

    return {
        "schema_version": "1.0.0",
        "formula_version": F.FORMULA_VERSION,
        "evidence_status": evidence_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "n_runs": len(records),
        "synthetic_runs_excluded": True,
        "evidence_coverage": coverage,
        "by_stratum": by_stratum,
        "layer_diagnosis": {
            "status": "deferred_to_ai",
            "instruction": (
                "Use Cursor skill validity-diagnose on the evidence pack from "
                "`python -m framework evidence`. Do not treat script heuristics as truth."
            ),
            "optional_heuristic": diagnose_layers(records, manifest),
        },
        "review_policy": {
            "human_review_never_removed": True,
            "status": "provisional_mechanical_lanes",
            "lanes": {
                "deep": "major / high-risk / low measured trust",
                "high_level": "medium trust and medium task risk",
                "minimal": "small low-risk work with high measured trust (nonzero)",
            },
            "notes": (
                "by_stratum.review_lane values are mechanical V_obs thresholds only. "
                "AI diagnosis confirms or overrides using task risk and evidence quality."
            ),
        },
        "claim_warnings": warnings,
    }


def _coverage(records: list[dict], key: str) -> dict[str, float]:
    if not records:
        return {"observed_fraction": 0.0, "imputed_fraction": 0.0, "missing_fraction": 1.0}
    n = len(records)
    obs = sum(1 for r in records if r.get(key) is not None)
    return {
        "observed_fraction": round(obs / n, 4),
        "imputed_fraction": 0.0,
        "missing_fraction": round(1.0 - obs / n, 4),
    }


def _coverage_stages(records: list[dict]) -> dict[str, float]:
    if not records:
        return {"observed_fraction": 0.0, "imputed_fraction": 0.0, "missing_fraction": 1.0}
    n = len(records)
    obs = sum(1 for r in records if r.get("stages") or r.get("stage_transitions"))
    return {
        "observed_fraction": round(obs / n, 4),
        "imputed_fraction": 0.0,
        "missing_fraction": round(1.0 - obs / n, 4),
    }


def _coverage_nested(records: list[dict], key: str) -> dict[str, float]:
    if not records:
        return {"observed_fraction": 0.0, "imputed_fraction": 0.0, "missing_fraction": 1.0}
    n = len(records)
    obs = 0
    for r in records:
        proxies = r.get("decay_proxies") or r.get("proxies") or {}
        if isinstance(proxies, dict) and proxies.get(key) is not None:
            obs += 1
        elif r.get(key) is not None:
            obs += 1
    return {
        "observed_fraction": round(obs / n, 4),
        "imputed_fraction": 0.0,
        "missing_fraction": round(1.0 - obs / n, 4),
    }


def write_report(report: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return out
