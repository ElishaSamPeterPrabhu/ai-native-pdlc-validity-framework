"""Diff / opacity adapter (Level 0 observe)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from theory import formula as F


def opacity_from_diff_stats(
    delta_loc: float,
    files_touched: int,
    delta_cc: float = 0.0,
) -> dict[str, Any]:
    """Build a measuredValue for opacity from universally available PR stats."""
    if files_touched <= 0 and delta_loc <= 0:
        return {
            "value": None,
            "source": "missing",
            "confidence": "none",
            "notes": "no diff stats available",
        }
    value = F.opacity_proxy(delta_loc, delta_cc, max(1, files_touched))
    confidence = "high" if delta_cc > 0 else "medium"
    return {
        "value": round(value, 4),
        "source": "observed",
        "confidence": confidence,
        "raw": {
            "delta_loc": delta_loc,
            "delta_cc": delta_cc,
            "files_touched": files_touched,
        },
    }


def blast_radius_from_counts(
    dependents_of_changed: int | None,
    dependents_total: int | None,
) -> dict[str, Any]:
    if dependents_of_changed is None or dependents_total is None or dependents_total <= 0:
        return {
            "value": None,
            "source": "missing",
            "confidence": "none",
            "notes": "dependency graph not available",
        }
    value = F.blast_radius_proxy(dependents_of_changed, dependents_total)
    return {
        "value": round(value, 4),
        "source": "observed",
        "confidence": "high",
        "raw": {
            "dependents_of_changed": dependents_of_changed,
            "dependents_total": dependents_total,
        },
    }


def ci_gate_activity(ci_passed: bool | None, required: bool) -> dict[str, Any]:
    if not required:
        return {"value": 0.0, "source": "declared", "confidence": "high"}
    if ci_passed is None:
        return {
            "value": None,
            "source": "missing",
            "confidence": "none",
            "notes": "CI status unknown",
        }
    return {
        "value": 1.0 if ci_passed else 0.5,
        "source": "observed",
        "confidence": "high",
        "raw": {"ci_passed": ci_passed},
    }


def provisional_v_star(
    recovery_activities: dict[str, float],
    decay_inputs: F.DecayInputs,
) -> float:
    """Directional equilibrium using placeholder weights (not repo-fitted)."""
    r = F.recovery_rate(recovery_activities)
    d = F.decay_rate(decay_inputs, form=F.DecayForm.HYBRID)
    return F.equilibrium_validity(r, d)


def bootstrap_mean_ci(values: list[float], n_boot: int = 500, seed: int = 0):
    if not values:
        return (None, None)
    import numpy as np

    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = [float(np.mean(rng.choice(arr, arr.size))) for _ in range(n_boot)]
    return (
        round(float(np.percentile(means, 2.5)), 4),
        round(float(np.percentile(means, 97.5)), 4),
    )


def saturate_commit_cadence(commits_per_hour: float) -> float:
    return min(1.0, max(0.0, commits_per_hour / 4.0))


def safe_rate(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return num / den


def entropy_from_tokens(
    tokens_current: float | None,
    tokens_max: float | None,
    tool_calls_failed: float | None,
    tool_calls_total: float | None,
) -> dict[str, Any]:
    if tokens_current is None or tokens_max is None:
        return {
            "value": 0.5,
            "source": "imputed",
            "confidence": "low",
            "notes": "token telemetry unavailable; imputed mid entropy",
        }
    failed = tool_calls_failed or 0.0
    total = tool_calls_total or 0.0
    value = F.entropy_proxy(tokens_current, tokens_max, failed, total)
    return {
        "value": round(value, 4),
        "source": "observed",
        "confidence": "high" if total > 0 else "medium",
        "raw": {
            "tokens_current": tokens_current,
            "tokens_max": tokens_max,
            "tool_calls_failed": failed,
            "tool_calls_total": total,
        },
    }


# Silence unused import lint for math in some environments
_ = math
