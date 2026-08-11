"""Sobol global sensitivity analysis over the micro-process parameters.

Question answered: which parameters actually move the outcomes (final validity,
pass^k) on medium/high tasks? Parameters with negligible total-order indices get
dropped or fixed in formula v1, and do not earn real-run ablation arms.
"""

from __future__ import annotations

import json
import os

import numpy as np
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample

from trajectory import HIGH, MEDIUM, MicroParams, SetupConfig, simulate_run

PROBLEM = {
    "num_vars": 9,
    "names": [
        "refinement_ambiguity_cut",
        "mcp_error_mult",
        "rules_error_mult",
        "entropy_error_gain",
        "ambiguity_error_gain",
        "ci_catch_prob",
        "qa_catch_prob",
        "fix_success_prob",
        "steps_per_commit",
    ],
    "bounds": [
        [0.2, 0.9],   # refinement_ambiguity_cut
        [0.5, 1.0],   # mcp_error_mult (1.0 = MCP does nothing)
        [0.6, 1.0],   # rules_error_mult
        [0.0, 0.15],  # entropy_error_gain
        [0.0, 0.12],  # ambiguity_error_gain
        [0.3, 0.95],  # ci_catch_prob
        [0.3, 0.95],  # qa_catch_prob
        [0.3, 0.95],  # fix_success_prob
        [4, 24],      # steps_per_commit
    ],
}


def _params_from_row(row: np.ndarray) -> MicroParams:
    return MicroParams(
        refinement_ambiguity_cut=float(row[0]),
        mcp_error_mult=float(row[1]),
        rules_error_mult=float(row[2]),
        entropy_error_gain=float(row[3]),
        ambiguity_error_gain=float(row[4]),
        ci_catch_prob=float(row[5]),
        qa_catch_prob=float(row[6]),
        fix_success_prob=float(row[7]),
        steps_per_commit=int(round(row[8])),
    )


def evaluate(row: np.ndarray, task, reps: int, seed: int) -> float:
    """Outcome metric: mean final V_obs across reps (full pipeline enabled)."""
    rng = np.random.default_rng(seed)
    params = _params_from_row(row)
    config = SetupConfig()
    finals = [
        simulate_run(task, config, params, rng).checkpoints[-1].v_obs
        for _ in range(reps)
    ]
    return float(np.mean(finals))


def run(n_base: int = 256, reps: int = 12, seed: int = 42, out_dir: str = "data"):
    """Run Sobol analysis on MEDIUM and HIGH strata; write indices to JSON."""
    samples = sobol_sample.sample(PROBLEM, n_base, calc_second_order=False, seed=seed)
    results = {}
    for task in (MEDIUM, HIGH):
        y = np.array([
            evaluate(row, task, reps, seed + i) for i, row in enumerate(samples)
        ])
        si = sobol_analyze.analyze(
            PROBLEM, y, calc_second_order=False, print_to_console=False, seed=seed
        )
        results[task.name] = {
            "S1": dict(zip(PROBLEM["names"], np.round(si["S1"], 4).tolist())),
            "ST": dict(zip(PROBLEM["names"], np.round(si["ST"], 4).tolist())),
            "ST_conf": dict(zip(PROBLEM["names"], np.round(si["ST_conf"], 4).tolist())),
            "y_mean": float(np.mean(y)),
            "y_std": float(np.std(y)),
        }
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "sobol_indices.json")
    with open(path, "w") as fh:
        json.dump(results, fh, indent=2)
    return results, path


if __name__ == "__main__":
    results, path = run()
    for stratum, res in results.items():
        ranked = sorted(res["ST"].items(), key=lambda kv: -kv[1])
        print(f"\n[{stratum}] outcome mean={res['y_mean']:.3f} sd={res['y_std']:.3f}")
        for name, st in ranked:
            print(f"  ST={st:6.3f}  (±{res['ST_conf'][name]:.3f})  {name}")
    print(f"\nwritten: {path}")
