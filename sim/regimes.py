"""Regime maps: paper figures showing what the ODE predicts qualitatively.

Figure 1: equilibrium validity V* as a function of decay pressure for several
          recovery strengths (the "strictness must scale with complexity" curve).
Figure 2: time-to-collapse (V drops below 0.5) vs task decay rate, with and
          without the recovery loop.
Figure 3: simulated pass@1 and pass^3 per complexity stratum, full pipeline vs
          bare agent (Monte Carlo, not ODE) — the headline motivation figure.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import formula as F
from trajectory import STRATA, SetupConfig, arm_pass_hat_k, simulate_arm

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "figures")

BARE = SetupConfig(
    spec_refinement=False, agentic_qa=False, fix_loop=False, ci_gate=False,
    mcp_context=False, rules_context=False, checkpointing=False,
)


def fig_equilibrium() -> str:
    decay = np.linspace(0.0, 1.0, 200)
    plt.figure(figsize=(7, 4.5))
    for r in (0.05, 0.15, 0.3, 0.6):
        v_star = [F.equilibrium_validity(r, d) for d in decay]
        plt.plot(decay, v_star, label=f"R = {r}")
    plt.axhline(0.5, color="gray", lw=0.8, ls="--")
    plt.xlabel("decay rate D (task pressure: blast radius x ambiguity x entropy)")
    plt.ylabel("equilibrium validity V*")
    plt.title("V* = R / (R + D): recovery must scale with task pressure")
    plt.legend()
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "fig1_equilibrium.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def fig_time_to_collapse() -> str:
    decays = np.linspace(0.05, 1.0, 60)
    plt.figure(figsize=(7, 4.5))
    for r, label in ((0.0, "no recovery (bare agent)"), (0.2, "with recovery loop")):
        times = []
        for d in decays:
            v_star = F.equilibrium_validity(r, d)
            if v_star >= 0.5:
                times.append(np.inf)
                continue
            # Solve V(t) = 0.5 from V(0)=1: t = ln((1-V*)/(0.5-V*)) / (R+D)
            times.append(np.log((1 - v_star) / (0.5 - v_star)) / (r + d))
        times = np.array(times)
        finite = np.isfinite(times)
        plt.plot(decays[finite], times[finite], label=label)
    plt.xlabel("decay rate D")
    plt.ylabel("time until V(t) < 0.5 (normalized run time)")
    plt.title("Time-to-collapse: recovery buys survival on hard tasks")
    plt.legend()
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "fig2_time_to_collapse.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def fig_pipeline_value(n_tasks: int = 20, k: int = 3, seed: int = 11) -> str:
    labels, full_p1, full_pk, bare_p1, bare_pk = [], [], [], [], []
    for name, prof in STRATA.items():
        full = simulate_arm(prof, SetupConfig(), k=k, n_tasks=n_tasks, seed=seed)
        bare = simulate_arm(prof, BARE, k=k, n_tasks=n_tasks, seed=seed)
        labels.append(name)
        full_p1.append(np.mean([r.final_pass for r in full]))
        full_pk.append(arm_pass_hat_k(full, k))
        bare_p1.append(np.mean([r.final_pass for r in bare]))
        bare_pk.append(arm_pass_hat_k(bare, k))

    x = np.arange(len(labels))
    width = 0.2
    plt.figure(figsize=(8, 4.5))
    plt.bar(x - 1.5 * width, full_p1, width, label="full pipeline pass@1")
    plt.bar(x - 0.5 * width, full_pk, width, label=f"full pipeline pass^{k}")
    plt.bar(x + 0.5 * width, bare_p1, width, label="bare agent pass@1")
    plt.bar(x + 1.5 * width, bare_pk, width, label=f"bare agent pass^{k}")
    plt.xticks(x, labels)
    plt.ylim(0, 1.05)
    plt.xlabel("task complexity stratum")
    plt.ylabel("success probability")
    plt.title("Simulated value of the recovery pipeline (Monte Carlo)")
    plt.legend(fontsize=8)
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "fig3_pipeline_value.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


if __name__ == "__main__":
    os.makedirs(FIG_DIR, exist_ok=True)
    for fn in (fig_equilibrium, fig_time_to_collapse, fig_pipeline_value):
        print("written:", fn())
