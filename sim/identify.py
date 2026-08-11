"""Identifiability check: can the ODE's weights be recovered from data shaped like
the Phase-C harness output?

Procedure:
1. Simulate arms with the Monte Carlo generator (ground truth is the micro-process,
   NOT the ODE — so this also tests whether the ODE approximates the micro-process).
2. Fit the ODE (piecewise-constant segments between checkpoints, exact per-segment
   solution from theory/formula.py) to the V_obs trajectories by nonlinear least
   squares over the factor weights w_f and decay weights.
3. Report: fit RMSE, and whether ablation arms recover the right ordering (e.g. the
   MCP-off arm shows lower fitted recovery / higher decay than MCP-on).

The verdict feeds formula v1: weights that cannot be pinned down at the planned
sample size (~30 trajectories per arm) must be merged, fixed, or dropped.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

import formula as F
from trajectory import (
    HIGH,
    LOW,
    MEDIUM,
    MicroParams,
    RunResult,
    SetupConfig,
    simulate_arm,
)

# Factor weights fitted (subset that varies across our planned arms).
FITTED_FACTORS = [
    "spec_refinement",
    "agentic_qa",
    "fix_loop",
    "ci_gate",
    "mcp_context",
    "rules_context",
    "checkpointing",
]
# Decay weights fitted (HYBRID form).
DECAY_KEYS = ["baseline", "entropy", "opacity", "blast_radius", "spec_ambiguity",
              "interaction_cs"]


def predict_trajectory(run: RunResult, theta: np.ndarray) -> np.ndarray:
    """ODE-predicted V at each checkpoint given parameter vector theta."""
    w = dict(zip(FITTED_FACTORS, theta[: len(FITTED_FACTORS)]))
    dw = F.DecayWeights(
        baseline=theta[len(FITTED_FACTORS) + 0],
        entropy=theta[len(FITTED_FACTORS) + 1],
        opacity=theta[len(FITTED_FACTORS) + 2],
        blast_radius=theta[len(FITTED_FACTORS) + 3],
        spec_ambiguity=theta[len(FITTED_FACTORS) + 4],
        interaction_cs=theta[len(FITTED_FACTORS) + 5],
    )
    cps = run.checkpoints
    preds = [cps[0].v_obs]
    v = cps[0].v_obs
    for prev, cur in zip(cps, cps[1:]):
        dt = max(1e-6, cur.t - prev.t)
        recovery = sum(
            w.get(name, 0.0) * act for name, act in prev.activities.items()
        )
        decay = F.decay_rate(
            F.DecayInputs(
                entropy=prev.entropy,
                opacity=prev.opacity,
                blast_radius=prev.blast_radius,
                spec_ambiguity=prev.spec_ambiguity,
            ),
            weights=dw,
            form=F.DecayForm.HYBRID,
        )
        v_star = F.equilibrium_validity(recovery, decay)
        rate = recovery + decay
        v = v_star + (v - v_star) * math.exp(-rate * dt)
        preds.append(v)
    return np.asarray(preds)


def fit_arms(runs: list[RunResult], seed: int = 0):
    """Fit shared theta across all runs (arms differ via activities telemetry)."""
    rng = np.random.default_rng(seed)

    def residuals(theta: np.ndarray) -> np.ndarray:
        res = []
        for run in runs:
            obs = np.array([c.v_obs for c in run.checkpoints])
            res.append(predict_trajectory(run, theta) - obs)
        return np.concatenate(res)

    n = len(FITTED_FACTORS) + len(DECAY_KEYS)
    best = None
    for _ in range(4):  # multi-start against local minima
        x0 = rng.uniform(0.05, 1.0, size=n)
        sol = least_squares(residuals, x0, bounds=(0.0, 10.0), method="trf")
        if best is None or sol.cost < best.cost:
            best = sol
    rmse = float(np.sqrt(np.mean(best.fun**2)))
    theta = best.x
    return {
        "rmse": rmse,
        "factor_weights": dict(
            zip(FITTED_FACTORS, np.round(theta[: len(FITTED_FACTORS)], 4).tolist())
        ),
        "decay_weights": dict(
            zip(DECAY_KEYS, np.round(theta[len(FITTED_FACTORS):], 4).tolist())
        ),
    }


@dataclass(frozen=True)
class Arm:
    name: str
    config: SetupConfig


ARMS = [
    Arm("full", SetupConfig()),
    Arm("no_mcp", SetupConfig(mcp_context=False)),
    Arm("no_qa_fix", SetupConfig(agentic_qa=False, fix_loop=False)),
    Arm("no_spec_refinement", SetupConfig(spec_refinement=False)),
    Arm("no_ci", SetupConfig(ci_gate=False)),
    Arm(
        "bare",
        SetupConfig(
            spec_refinement=False, agentic_qa=False, fix_loop=False, ci_gate=False,
            mcp_context=False, rules_context=False, checkpointing=False,
        ),
    ),
]


def run_study(
    n_tasks: int = 10,
    k: int = 3,
    params: MicroParams = MicroParams(),
    seed: int = 7,
    out_dir: str = "data",
):
    """Simulate the planned campaign shape and fit; write the verdict to JSON."""
    all_runs: list[RunResult] = []
    arm_stats = {}
    for arm in ARMS:
        runs = []
        for i, task in enumerate((LOW, MEDIUM, HIGH)):
            runs += simulate_arm(task, arm.config, k=k, n_tasks=n_tasks,
                                 params=params, seed=seed + i)
        all_runs += runs
        arm_stats[arm.name] = {
            "pass_at_1": float(np.mean([r.final_pass for r in runs])),
            "final_v_mean": float(np.mean([r.checkpoints[-1].v_obs for r in runs])),
            "n_runs": len(runs),
        }

    fit = fit_arms(all_runs, seed=seed)

    # Ablation deltas implied by the fit vs observed directly.
    result = {
        "arm_stats": arm_stats,
        "fit": fit,
        "n_trajectories": len(all_runs),
        "verdict_notes": [],
    }

    # Sanity ordering checks the fit must reproduce.
    checks = [
        ("full > bare (observed)",
         arm_stats["full"]["final_v_mean"] > arm_stats["bare"]["final_v_mean"]),
        ("full > no_qa_fix (observed)",
         arm_stats["full"]["final_v_mean"] > arm_stats["no_qa_fix"]["final_v_mean"]),
        ("fit RMSE < 0.15", fit["rmse"] < 0.15),
    ]
    for label, ok in checks:
        result["verdict_notes"].append({"check": label, "ok": bool(ok)})

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "identifiability.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=2)
    return result, path


if __name__ == "__main__":
    result, path = run_study()
    print(json.dumps(result["arm_stats"], indent=2))
    print("fit RMSE:", result["fit"]["rmse"])
    print("factor weights:", result["fit"]["factor_weights"])
    for note in result["verdict_notes"]:
        print(("PASS " if note["ok"] else "FAIL ") + note["check"])
    print("written:", path)
