"""Completion-guard hook ablation: hook-off vs hook-on across setups and strata.

Protocol (see data/hooks_predictions.json):
  1. Predictions are registered before this script runs.
  2. hook_detect_prob is swept; no single assumed detection rate is claimed.
  3. Measured JSON output is the only source of reportable numbers.

Run from the research workspace:
    .venv/bin/python -m sim.hooks_experiment
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Ensure theory/ is importable the same way as other sim modules.
_SIM_DIR = Path(__file__).resolve().parent
_ROOT = _SIM_DIR.parent
_THEORY_DIR = _ROOT / "theory"
if str(_THEORY_DIR) not in sys.path:
    sys.path.insert(0, str(_THEORY_DIR))
if str(_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(_SIM_DIR))

from trajectory import (  # noqa: E402
    HIGH,
    MEDIUM,
    MicroParams,
    SetupConfig,
    arm_pass_hat_k,
    simulate_arm,
)

SEED = 20260727
N_TASKS = 20
K = 3
DETECT_GRID = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
STRATA = {"medium": MEDIUM, "high": HIGH}

DATA_DIR = _ROOT / "data"
FIG_DIR = DATA_DIR / "figures"
PRED_PATH = DATA_DIR / "hooks_predictions.json"
OUT_PATH = DATA_DIR / "hooks_ablation.json"
FIG_PATH = FIG_DIR / "fig4_hook_ablation.png"


def _setups() -> dict[str, SetupConfig]:
    return {
        "full_pipeline": SetupConfig(),
        "fix_cap_1": SetupConfig(fix_iteration_cap=1),
        "no_agentic_qa": SetupConfig(agentic_qa=False, fix_loop=False),
    }


def _summarize(results: list, k: int) -> dict[str, float]:
    finals = [r.checkpoints[-1].v_obs for r in results]
    return {
        "mean_v_obs": float(np.mean(finals)),
        "sd_v_obs": float(np.std(finals)),
        "pass_at_1": float(np.mean([r.final_pass for r in results])),
        "pass_hat_k": float(arm_pass_hat_k(results, k)),
        "mean_hook_interventions": float(
            np.mean([r.hook_interventions for r in results])
        ),
        "mean_fix_iterations": float(
            np.mean([r.fix_iterations_used for r in results])
        ),
        "n_runs": len(results),
    }


def _prediction_match(
    expected_range: list[float],
    measured_delta: float,
) -> str:
    lo, hi = expected_range
    if lo <= measured_delta <= hi:
        return "agree"
    if measured_delta < lo:
        return "below_predicted_range"
    return "above_predicted_range"


def run_experiment() -> dict:
    if not PRED_PATH.exists():
        raise FileNotFoundError(
            f"Predictions must be registered before the run: {PRED_PATH}"
        )
    predictions = json.loads(PRED_PATH.read_text())
    pred_by_key = {
        (p["arm"], p["stratum"]): p for p in predictions["predictions"]
    }

    setups = _setups()
    cells: list[dict] = []

    for detect_prob in DETECT_GRID:
        params = MicroParams(hook_detect_prob=detect_prob)
        for arm_name, base_cfg in setups.items():
            for stratum_name, task in STRATA.items():
                digest = hashlib.blake2b(
                    f"{SEED}|{detect_prob}|{arm_name}|{stratum_name}".encode(),
                    digest_size=8,
                ).hexdigest()
                cell_seed = int(digest, 16) % (2**31 - 1)

                off_cfg = replace(base_cfg, completion_guard_hook=False)
                on_cfg = replace(base_cfg, completion_guard_hook=True)

                off = simulate_arm(
                    task, off_cfg, k=K, n_tasks=N_TASKS, params=params, seed=cell_seed
                )
                on = simulate_arm(
                    task, on_cfg, k=K, n_tasks=N_TASKS, params=params, seed=cell_seed
                )

                off_s = _summarize(off, K)
                on_s = _summarize(on, K)
                delta_v = on_s["mean_v_obs"] - off_s["mean_v_obs"]
                delta_p1 = on_s["pass_at_1"] - off_s["pass_at_1"]
                delta_pk = on_s["pass_hat_k"] - off_s["pass_hat_k"]

                pred = pred_by_key[(arm_name, stratum_name)]
                cells.append(
                    {
                        "arm": arm_name,
                        "stratum": stratum_name,
                        "hook_detect_prob": detect_prob,
                        "seed": cell_seed,
                        "hook_off": off_s,
                        "hook_on": on_s,
                        "delta_v_obs": delta_v,
                        "delta_pass_at_1": delta_p1,
                        "delta_pass_hat_k": delta_pk,
                        "prediction": {
                            "expected_direction": pred["expected_direction"],
                            "expected_delta_v_obs_range": pred[
                                "expected_delta_v_obs_range"
                            ],
                            "match": _prediction_match(
                                pred["expected_delta_v_obs_range"], delta_v
                            ),
                        },
                    }
                )

    # Aggregate claimable ranges across the detect-prob sweep per arm/stratum.
    aggregates: list[dict] = []
    for arm_name in setups:
        for stratum_name in STRATA:
            subset = [
                c
                for c in cells
                if c["arm"] == arm_name and c["stratum"] == stratum_name
            ]
            deltas = [c["delta_v_obs"] for c in subset]
            pred = pred_by_key[(arm_name, stratum_name)]
            p1_deltas = [c["delta_pass_at_1"] for c in subset]
            pk_deltas = [c["delta_pass_hat_k"] for c in subset]
            aggregates.append(
                {
                    "arm": arm_name,
                    "stratum": stratum_name,
                    "delta_v_obs_min": float(min(deltas)),
                    "delta_v_obs_max": float(max(deltas)),
                    "delta_v_obs_mean": float(np.mean(deltas)),
                    "delta_pass_at_1_min": float(min(p1_deltas)),
                    "delta_pass_at_1_max": float(max(p1_deltas)),
                    "delta_pass_at_1_mean": float(np.mean(p1_deltas)),
                    "delta_pass_hat_k_min": float(min(pk_deltas)),
                    "delta_pass_hat_k_max": float(max(pk_deltas)),
                    "delta_pass_hat_k_mean": float(np.mean(pk_deltas)),
                    "prediction_match_counts": {
                        "agree": sum(
                            1 for c in subset if c["prediction"]["match"] == "agree"
                        ),
                        "below_predicted_range": sum(
                            1
                            for c in subset
                            if c["prediction"]["match"] == "below_predicted_range"
                        ),
                        "above_predicted_range": sum(
                            1
                            for c in subset
                            if c["prediction"]["match"] == "above_predicted_range"
                        ),
                    },
                    "expected_delta_v_obs_range": pred["expected_delta_v_obs_range"],
                    "direction_correct": float(np.mean(deltas)) >= 0.0,
                }
            )

    payload = {
        "seed": SEED,
        "n_tasks": N_TASKS,
        "k": K,
        "detect_prob_grid": DETECT_GRID,
        "arms": list(setups.keys()),
        "strata": list(STRATA.keys()),
        "total_runs": len(cells) * N_TASKS * K,
        "predictions_path": str(PRED_PATH.relative_to(_ROOT)),
        "cells": cells,
        "aggregates": aggregates,
    }
    return payload


def write_figure(payload: dict) -> str:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    aggregates = payload["aggregates"]
    labels = [f"{a['arm']}\n{a['stratum']}" for a in aggregates]
    x = np.arange(len(labels))

    # Recompute pass@1 sweep ranges from cells for the second panel.
    p1_means, p1_mins, p1_maxs = [], [], []
    for a in aggregates:
        deltas = [
            c["delta_pass_at_1"]
            for c in payload["cells"]
            if c["arm"] == a["arm"] and c["stratum"] == a["stratum"]
        ]
        p1_means.append(float(np.mean(deltas)))
        p1_mins.append(float(min(deltas)))
        p1_maxs.append(float(max(deltas)))

    v_means = [a["delta_v_obs_mean"] for a in aggregates]
    v_mins = [a["delta_v_obs_min"] for a in aggregates]
    v_maxs = [a["delta_v_obs_max"] for a in aggregates]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, means, mins, maxs, ylabel, title in (
        (
            axes[0],
            v_means,
            v_mins,
            v_maxs,
            "Δ mean V_obs (hook on − off)",
            "Validity delta",
        ),
        (
            axes[1],
            p1_means,
            p1_mins,
            p1_maxs,
            "Δ pass@1 (hook on − off)",
            "Pass@1 delta",
        ),
    ):
        yerr = [
            [m - lo for m, lo in zip(means, mins)],
            [hi - m for m, hi in zip(means, maxs)],
        ]
        colors = [
            "#4C78A8" if m > 0.01 else ("#F58518" if m >= 0 else "#E45756")
            for m in means
        ]
        ax.bar(x, means, color=colors, yerr=yerr, capsize=3, alpha=0.9)
        ax.axhline(0.0, color="gray", lw=0.8, ls="--")
        ax.set_xticks(x, labels, fontsize=7)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

    fig.suptitle(
        "Completion-guard hook ablation "
        f"(min/max over hook_detect_prob ∈ {DETECT_GRID[0]}–{DETECT_GRID[-1]})",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(FIG_PATH, dpi=150)
    plt.close(fig)
    return str(FIG_PATH)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = run_experiment()
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    fig = write_figure(payload)
    print(f"written: {OUT_PATH}")
    print(f"written: {fig}")
    print(f"total_runs: {payload['total_runs']}")
    print("\nAggregate ΔV_obs (mean [min, max] over detect-prob sweep):")
    for a in payload["aggregates"]:
        print(
            f"  {a['arm']:16s} {a['stratum']:6s}  "
            f"{a['delta_v_obs_mean']:+.4f}  "
            f"[{a['delta_v_obs_min']:+.4f}, {a['delta_v_obs_max']:+.4f}]  "
            f"matches={a['prediction_match_counts']}"
        )


if __name__ == "__main__":
    main()
