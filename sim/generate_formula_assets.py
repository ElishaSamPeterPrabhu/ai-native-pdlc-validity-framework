"""Generate presentation-ready formula legend assets.

Run from the research workspace:
    .venv/bin/python sim/generate_formula_assets.py

The generated PNG files are intentionally simple, high-contrast, and suitable for
inserting into the TTC abstract or a slide without relying on Markdown math rendering.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "figures"


def save_figure(filename: str) -> tuple[plt.Figure, plt.Axes]:
    figure, axes = plt.subplots(figsize=(12, 5.8), dpi=180)
    figure.patch.set_facecolor("white")
    axes.set_facecolor("white")
    axes.axis("off")
    figure.savefig(
        OUTPUT_DIR / filename,
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.25,
    )
    return figure, axes


def write_recovery() -> None:
    figure, axes = save_figure("formula_recovery_terms.png")
    axes.text(
        0.5,
        0.89,
        "Systematic Recovery",
        ha="center",
        va="center",
        fontsize=25,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.72,
        r"$R(t) = \alpha T(t) + \beta M(t) + \gamma\rho(t)\,\iota$",
        ha="center",
        va="center",
        fontsize=26,
    )
    entries = [
        (r"$T(t)$", "Deterministic testing coverage: unit, integration, accessibility, and visual checks."),
        (r"$M(t)$", "Human-alignment opportunity: a clarification or needs-human escalation."),
        (r"$\rho(t)$", "Checkpointing frequency: small, reversible commits that bound error scope."),
        (r"ι (iota)", "Tool idempotency: retrying a tool action does not corrupt the environment."),
        (r"$\alpha,\ \beta,\ \gamma$", "Fitted weights: the measured recovery value of each safeguard."),
    ]
    for index, (symbol, meaning) in enumerate(entries):
        y = 0.52 - index * 0.105
        axes.text(0.08, y, symbol, ha="left", va="center", fontsize=20)
        axes.text(0.2, y, meaning, ha="left", va="center", fontsize=13.5)
    figure.savefig(
        OUTPUT_DIR / "formula_recovery_terms.png",
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.25,
    )
    plt.close(figure)


def write_decay() -> None:
    figure, axes = save_figure("formula_decay_terms.png")
    axes.text(
        0.5,
        0.89,
        "Systematic Decay",
        ha="center",
        va="center",
        fontsize=25,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.72,
        r"$D(t) = C \cdot \sigma_{\mathrm{spec}} \cdot H_c(t) \cdot O(t)$",
        ha="center",
        va="center",
        fontsize=26,
    )
    entries = [
        (r"$C$", "Blast radius: dependency coupling and reach of the files changed."),
        (r"$\sigma_{\mathrm{spec}}$", "Specification ambiguity: how much independently generated plans disagree."),
        (r"$H_c(t)$", "Contextual entropy: context saturation amplified by tool failures and error loops."),
        (r"$O(t)$", "Diff opacity: review burden from change size, complexity, and file spread."),
    ]
    for index, (symbol, meaning) in enumerate(entries):
        y = 0.50 - index * 0.12
        axes.text(0.08, y, symbol, ha="left", va="center", fontsize=20)
        axes.text(0.2, y, meaning, ha="left", va="center", fontsize=13.5)
    axes.text(
        0.5,
        0.07,
        "Higher task complexity increases decay pressure unless recovery scales with it.",
        ha="center",
        va="center",
        fontsize=14,
        style="italic",
    )
    figure.savefig(
        OUTPUT_DIR / "formula_decay_terms.png",
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.25,
    )
    plt.close(figure)


def write_equilibrium() -> None:
    figure, axes = save_figure("formula_equilibrium.png")
    axes.text(
        0.5,
        0.79,
        "Equilibrium Validity",
        ha="center",
        va="center",
        fontsize=27,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.55,
        r"$V^{*} = \frac{R}{R + D}$",
        ha="center",
        va="center",
        fontsize=42,
    )
    axes.text(
        0.5,
        0.29,
        "At equilibrium, recovery strength R must scale with decay pressure D\n"
        "to maintain a target level of trust.",
        ha="center",
        va="center",
        fontsize=18,
    )
    axes.text(
        0.5,
        0.09,
        "A stronger model is useful; a sufficiently strong surrounding setup is necessary.",
        ha="center",
        va="center",
        fontsize=14,
        style="italic",
    )
    figure.savefig(
        OUTPUT_DIR / "formula_equilibrium.png",
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.25,
    )
    plt.close(figure)


def write_rate_decomposition() -> None:
    figure, axes = save_figure("formula_rate_decomposition.png")
    axes.text(
        0.5,
        0.86,
        "Recovery and Decay Rates",
        ha="center",
        va="center",
        fontsize=27,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.65,
        r"$D(t)=d_0+d_hH_c+d_oO+d_cC_b+d_s\sigma_{\mathrm{spec}}"
        r"+d_{cs}(C_b\sigma_{\mathrm{spec}})$",
        ha="center",
        va="center",
        fontsize=25,
    )
    axes.text(
        0.5,
        0.46,
        r"$R(t)=\sum_{f\in\mathrm{enabled}} w_f\,f_f(t)$",
        ha="center",
        va="center",
        fontsize=29,
    )
    axes.text(
        0.5,
        0.25,
        "Multiple measurable factors combine into one decay rate D(t)\n"
        "and one recovery rate R(t) at each lifecycle checkpoint.",
        ha="center",
        va="center",
        fontsize=17,
    )
    axes.text(
        0.5,
        0.08,
        "Higher D lowers validity; higher R detects, constrains, or repairs invalid work.",
        ha="center",
        va="center",
        fontsize=14,
        style="italic",
    )
    figure.savefig(
        OUTPUT_DIR / "formula_rate_decomposition.png",
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.25,
    )
    plt.close(figure)


def write_validity_definition() -> None:
    figure, axes = save_figure("formula_validity_definition.png")
    axes.text(
        0.5,
        0.80,
        "Observed Validity",
        ha="center",
        va="center",
        fontsize=27,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.56,
        r"$V_{\mathrm{obs}}(t) = \frac{\mathrm{verifier\ checks\ passing}}"
        r"{\mathrm{total\ verifier\ checks}}$",
        ha="center",
        va="center",
        fontsize=31,
    )
    axes.text(
        0.5,
        0.28,
        "Measured at each agent commit. This converts trust from a subjective opinion\n"
        "into a time series that can be fitted against recovery and decay factors.",
        ha="center",
        va="center",
        fontsize=17,
    )
    figure.savefig(
        OUTPUT_DIR / "formula_validity_definition.png",
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.25,
    )
    plt.close(figure)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_recovery()
    write_decay()
    write_rate_decomposition()
    write_equilibrium()
    write_validity_definition()
    print(f"Formula assets written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
