"""Shared pilot exit criteria for Level 2 calibrate / fit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PILOT_CRITERIA = {
    "terminal_runs_min": 6,
    "require_v_obs_variation": True,
    "require_stage_transitions": True,
    "synthetic_allowed": False,
}


def load_metrics_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def check_pilot_exit(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate whether non-synthetic metrics meet Level 2 pilot exit criteria."""
    criteria = PILOT_CRITERIA
    real = [r for r in records if not r.get("synthetic")]
    terminal = [
        r
        for r in real
        if r.get("final_v_obs") is not None or r.get("final_pass") is not None
    ]
    v_obs_values = [
        float(r["final_v_obs"])
        for r in terminal
        if r.get("final_v_obs") is not None
    ]
    has_variation = len(set(round(v, 3) for v in v_obs_values)) >= 2 if v_obs_values else False
    has_stages = any(
        r.get("stages") or r.get("stage_transitions") for r in terminal
    )

    checks = {
        "terminal_runs_min": len(terminal) >= criteria["terminal_runs_min"],
        "v_obs_variation": has_variation if criteria["require_v_obs_variation"] else True,
        "stage_transitions": has_stages if criteria["require_stage_transitions"] else True,
        "no_synthetic_only": len(real) > 0,
    }
    blocked_reasons: list[str] = []
    if not checks["terminal_runs_min"]:
        blocked_reasons.append(
            f"need ≥{criteria['terminal_runs_min']} terminal non-synthetic runs "
            f"(have {len(terminal)})"
        )
    if not checks["v_obs_variation"]:
        blocked_reasons.append("V_obs must vary across runs (not all identical)")
    if not checks["stage_transitions"]:
        blocked_reasons.append("at least one run must have stage_transitions or stages")
    if not checks["no_synthetic_only"]:
        blocked_reasons.append("no non-synthetic records found")

    return {
        "ok": all(checks.values()),
        "checks": checks,
        "n_total": len(records),
        "n_real": len(real),
        "n_terminal": len(terminal),
        "n_v_obs": len(v_obs_values),
        "blocked_reasons": blocked_reasons,
        "criteria": criteria,
    }
