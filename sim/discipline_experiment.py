"""Discipline-factor ablation: ON/OFF contrasts for the v1.3 factors.

Factors under test (see theory/formula-changelog.md v1.3):
  red_first_discipline, reviewer_independence, evidence_freshness,
  doctrine_reinjection.

Protocol (mirrors sim/hooks_experiment.py):
  1. Predictions are registered in data/discipline_predictions.json before
     this script runs; the run refuses to start without them.
  2. Each factor is contrasted ON vs OFF with the other three discipline
     factors OFF and only its own mechanism knobs nonzero.
  3. Measured JSON output is the only source of reportable numbers.
  4. All results are simulation-only; no live effect claims.

Run from the research workspace:
    .venv/bin/python -m sim.discipline_experiment
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

SEED = 20260830
N_TASKS = 20
K = 3
STRATA = {"medium": MEDIUM, "high": HIGH}

DATA_DIR = _ROOT / "data"
FIG_DIR = DATA_DIR / "figures"
PRED_PATH = DATA_DIR / "discipline_predictions.json"
OUT_PATH = DATA_DIR / "discipline_ablation.json"
FIG_PATH = FIG_DIR / "fig5_discipline_ablation.png"

# Each factor: the SetupConfig toggle plus the MicroParams knobs that arm its
# mechanism. Knobs are fixed for round 1 (no sweep); values documented in the
# predictions file.
FACTORS: dict[str, dict] = {
    "red_first_discipline": {"params": {"vacuous_green_prob": 0.35}},
    "reviewer_independence": {
        "params": {"review_catch_anchored": 0.25, "review_catch_independent": 0.75}
    },
    "evidence_freshness": {"params": {"stale_evidence_prob": 0.12}},
    "doctrine_reinjection": {"params": {"drift_ramp": 0.8}},
}


def _setups() -> dict[str, SetupConfig]:
    return {
        "full_pipeline": SetupConfig(),
        "no_agentic_qa": SetupConfig(agentic_qa=False, fix_loop=False),
    }


def _summarize(results: list, k: int) -> dict[str, float]:
    finals = [r.checkpoints[-1].v_obs for r in results]
    pass_at_1 = float(np.mean([r.final_pass for r in results]))
    self_claimed = float(np.mean([r.self_claimed_pass for r in results]))
    return {
        "mean_v_obs": float(np.mean(finals)),
        "sd_v_obs": float(np.std(finals)),
        "pass_at_1": pass_at_1,
        "pass_hat_k": float(arm_pass_hat_k(results, k)),
        "self_claimed_pass": self_claimed,
        "calibration_gap": self_claimed - pass_at_1,
        "mean_fix_iterations": float(
            np.mean([r.fix_iterations_used for r in results])
        ),
        "mean_vacuous_greens": float(np.mean([r.vacuous_greens for r in results])),
        "mean_stale_breaks": float(np.mean([r.stale_breaks for r in results])),
        "mean_review_repairs": float(np.mean([r.review_repairs for r in results])),
        "n_runs": len(results),
    }


def _prediction_match(expected_range: list[float], measured_delta: float) -> str:
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
        (p["factor"], p["arm"], p["stratum"]): p
        for p in predictions["predictions"]
    }

    setups = _setups()
    cells: list[dict] = []

    for factor_name, spec in FACTORS.items():
        params = MicroParams(**spec["params"])
        for arm_name, base_cfg in setups.items():
            for stratum_name, task in STRATA.items():
                digest = hashlib.blake2b(
                    f"{SEED}|{factor_name}|{arm_name}|{stratum_name}".encode(),
                    digest_size=8,
                ).hexdigest()
                cell_seed = int(digest, 16) % (2**31 - 1)

                off_cfg = replace(base_cfg, **{factor_name: False})
                on_cfg = replace(base_cfg, **{factor_name: True})

                off = simulate_arm(
                    task, off_cfg, k=K, n_tasks=N_TASKS, params=params, seed=cell_seed
                )
                on = simulate_arm(
                    task, on_cfg, k=K, n_tasks=N_TASKS, params=params, seed=cell_seed
                )

                off_s = _summarize(off, K)
                on_s = _summarize(on, K)
                delta_v = on_s["mean_v_obs"] - off_s["mean_v_obs"]

                pred = pred_by_key[(factor_name, arm_name, stratum_name)]
                cells.append(
                    {
                        "factor": factor_name,
                        "arm": arm_name,
                        "stratum": stratum_name,
                        "mechanism_knobs": spec["params"],
                        "seed": cell_seed,
                        "factor_off": off_s,
                        "factor_on": on_s,
                        "delta_v_obs": delta_v,
                        "delta_pass_at_1": on_s["pass_at_1"] - off_s["pass_at_1"],
                        "delta_pass_hat_k": on_s["pass_hat_k"] - off_s["pass_hat_k"],
                        "delta_calibration_gap": (
                            on_s["calibration_gap"] - off_s["calibration_gap"]
                        ),
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

    payload = {
        "seed": SEED,
        "n_tasks": N_TASKS,
        "k": K,
        "factors": list(FACTORS.keys()),
        "arms": list(setups.keys()),
        "strata": list(STRATA.keys()),
        "total_runs": len(cells) * 2 * N_TASKS * K,
        "predictions_path": str(PRED_PATH.relative_to(_ROOT)),
        "evidence_status": "simulation-only; no live telemetry",
        "cells": cells,
    }
    return payload


def write_figure(payload: dict) -> str:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    cells = payload["cells"]
    labels = [
        f"{c['factor'].replace('_', chr(10))}\n{c['arm'][:7]}-{c['stratum'][:3]}"
        for c in cells
    ]
    labels = [
        f"{c['factor']}\n{c['arm']}\n{c['stratum']}".replace("_", " ")
        for c in cells
    ]
    x = np.arange(len(labels))

    fig, axes = plt.subplots(2, 1, figsize=(14, 8.5), sharex=True)
    for ax, key, ylabel in (
        (axes[0], "delta_v_obs", "Δ mean V_obs (on − off)"),
        (axes[1], "delta_calibration_gap", "Δ calibration gap (on − off)"),
    ):
        vals = [c[key] for c in cells]
        colors = [
            "#4C78A8" if v > 0.01 else ("#F58518" if v >= -0.01 else "#E45756")
            for v in vals
        ]
        ax.bar(x, vals, color=colors, alpha=0.9)
        ax.axhline(0.0, color="gray", lw=0.8, ls="--")
        ax.set_ylabel(ylabel)
    axes[1].set_xticks(x, labels, fontsize=6)
    axes[0].set_title(
        "Discipline-factor ablation (v1.3): validity delta and calibration-gap delta"
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
    print("\nΔV_obs / Δpass@1 / Δcalibration-gap per cell:")
    for c in payload["cells"]:
        print(
            f"  {c['factor']:22s} {c['arm']:14s} {c['stratum']:6s}  "
            f"dV={c['delta_v_obs']:+.4f}  dp1={c['delta_pass_at_1']:+.4f}  "
            f"dcal={c['delta_calibration_gap']:+.4f}  "
            f"pred={c['prediction']['match']}"
        )


if __name__ == "__main__":
    main()
