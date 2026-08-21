"""Generate v1.1 formula equation and legend PNGs for the TTC abstracts.

Run from the research workspace:
    .venv/bin/python paper/figures/formula/generate.py

Outputs land next to this script so they can be embedded as:
    ![label](figures/formula/<name>.png)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


OUTPUT_DIR = Path(__file__).resolve().parent


def _blank(figsize: tuple[float, float] = (11.0, 4.8)) -> tuple[plt.Figure, plt.Axes]:
    figure, axes = plt.subplots(figsize=figsize, dpi=200)
    figure.patch.set_facecolor("white")
    axes.set_facecolor("white")
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)
    axes.axis("off")
    return figure, axes


def _save(figure: plt.Figure, name: str) -> None:
    path = OUTPUT_DIR / name
    figure.savefig(path, bbox_inches="tight", facecolor="white", pad_inches=0.3)
    plt.close(figure)
    print(f"wrote {path.name}")


def write_eq_ode() -> None:
    figure, axes = _blank((11.0, 3.6))
    axes.text(
        0.5,
        0.72,
        "Validity dynamics",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.38,
        r"$dV/dt = (1 - V)\,R(t) - V\,D(t)$",
        ha="center",
        va="center",
        fontsize=32,
    )
    _save(figure, "eq-ode.png")


def write_eq_vobs() -> None:
    figure, axes = _blank((11.0, 3.8))
    axes.text(
        0.5,
        0.76,
        "Observed validity",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.42,
        r"$V_{\mathrm{obs}}(t) ="
        r"\dfrac{\text{verifier checks passing}}"
        r"{\text{total verifier checks}}$",
        ha="center",
        va="center",
        fontsize=26,
    )
    axes.text(
        0.5,
        0.12,
        "Measured at each lifecycle checkpoint (for example, each agent commit).",
        ha="center",
        va="center",
        fontsize=13,
        style="italic",
    )
    _save(figure, "eq-vobs.png")


def write_eq_decay() -> None:
    figure, axes = _blank((12.5, 3.8))
    axes.text(
        0.5,
        0.78,
        "Hybrid decay rate (v1.1 default)",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.40,
        r"$D(t)=d_0+d_h H_c+d_o O+d_c C_b+d_s\sigma_{\mathrm{spec}}"
        r"+d_{cs}(C_b\,\sigma_{\mathrm{spec}})$",
        ha="center",
        va="center",
        fontsize=22,
    )
    _save(figure, "eq-decay.png")


def write_eq_recovery() -> None:
    figure, axes = _blank((11.0, 3.6))
    axes.text(
        0.5,
        0.74,
        "Recovery rate from the factor registry",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.38,
        r"$R(t)=\sum_{f\,\in\,\mathrm{enabled}} w_f\,f_f(t)$",
        ha="center",
        va="center",
        fontsize=30,
    )
    _save(figure, "eq-recovery.png")


def write_eq_vstar() -> None:
    figure, axes = _blank((11.0, 4.0))
    axes.text(
        0.5,
        0.78,
        "Equilibrium validity",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    axes.text(
        0.5,
        0.48,
        r"$V^{*}=\dfrac{R}{R+D}$",
        ha="center",
        va="center",
        fontsize=40,
    )
    axes.text(
        0.5,
        0.16,
        "If R = D, V* = 0.5.  If R = 3D, V* = 0.75.",
        ha="center",
        va="center",
        fontsize=15,
    )
    _save(figure, "eq-vstar.png")


def write_legend_decay() -> None:
    figure, axes = _blank((12.0, 6.2))
    axes.text(
        0.5,
        0.93,
        "Decay terms in plain language",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    entries = [
        (r"$d_0$", "Residual baseline decay not explained by the named proxies."),
        (r"$H_c$", "Contextual entropy: context saturation amplified by failed tool calls."),
        (r"$O$", "Diff opacity: hard-to-review changes (size, complexity, files touched)."),
        (r"$C_b$", "Blast radius / coupling: how widely a mistake in changed files can spread."),
        (
            r"$\sigma_{\mathrm{spec}}$",
            "Specification ambiguity: disagreement among independent interpretations of done.",
        ),
        (
            r"$C_b\sigma_{\mathrm{spec}}$",
            "Interaction: broad change under a vague specification is especially risky.",
        ),
        (r"$d_*$", "Fitted (or placeholder) weights for each decay contribution."),
    ]
    for index, (symbol, meaning) in enumerate(entries):
        y = 0.78 - index * 0.10
        axes.text(0.06, y, symbol, ha="left", va="center", fontsize=16)
        axes.text(0.22, y, meaning, ha="left", va="center", fontsize=13)
    _save(figure, "legend-decay.png")


def write_legend_recovery() -> None:
    figure, axes = _blank((12.0, 6.4))
    axes.text(
        0.5,
        0.93,
        "Recovery families in plain language",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    entries = [
        ("Spec refinement", "Turn a raw issue into checkable acceptance criteria."),
        ("Repo / MCP / rules", "Give the agent durable repository and coding-rule context."),
        ("Checkpointing", "Small reversible commits that bound how far an error spreads."),
        ("CI gates", "Deterministic tests that must pass before work advances."),
        ("Agentic QA", "QA agent checks (including browser, visual, a11y where used)."),
        ("Repair / fix loop", "Bounded repair attempts after QA or verifier failure."),
        ("Review gates", "Review-bot and human-alignment signals before merge."),
        (
            "Completion-guard hook",
            "Blocks false “done” until acceptance evidence exists (simulation-only until live telemetry).",
        ),
    ]
    for index, (title, meaning) in enumerate(entries):
        y = 0.80 - index * 0.085
        axes.text(0.06, y, title, ha="left", va="center", fontsize=13, fontweight="bold")
        axes.text(0.34, y, meaning, ha="left", va="center", fontsize=12.5)
    axes.text(
        0.5,
        0.06,
        r"Each enabled factor contributes $w_f\,f_f(t)$ to $R(t)$.",
        ha="center",
        va="center",
        fontsize=13,
        style="italic",
    )
    _save(figure, "legend-recovery.png")


def write_story_compounding() -> None:
    figure, axes = _blank((12.5, 5.2))
    axes.text(
        0.5,
        0.92,
        "How the formula was built",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    boxes = [
        (0.13, "Per-step\nerror compounds\n$P\\approx(1-\\varepsilon)^n$"),
        (0.38, "Continuous\ndecay hazard\n$dV/dt=-D\\,V$"),
        (0.63, "Add recovery\nfrom CI / QA /\nrepair / review"),
        (0.88, "Full ODE\n$(1-V)R-VD$\nand $V^*=R/(R+D)$"),
    ]
    for x, label in boxes:
        axes.add_patch(
            plt.Rectangle(
                (x - 0.11, 0.28),
                0.22,
                0.48,
                fill=True,
                facecolor="#F4F7FB",
                edgecolor="#1F3A5F",
                linewidth=1.5,
            )
        )
        axes.text(x, 0.52, label, ha="center", va="center", fontsize=12)
    for x in (0.24, 0.49, 0.74):
        axes.annotate(
            "",
            xy=(x + 0.03, 0.52),
            xytext=(x - 0.03, 0.52),
            arrowprops=dict(arrowstyle="->", color="#1F3A5F", lw=1.8),
        )
    axes.text(
        0.5,
        0.12,
        "Long agent runs lose correctness unless lifecycle safeguards restore it faster than decay erodes it.",
        ha="center",
        va="center",
        fontsize=13,
        style="italic",
    )
    _save(figure, "story-compounding.png")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_eq_ode()
    write_eq_vobs()
    write_eq_decay()
    write_eq_recovery()
    write_eq_vstar()
    write_legend_decay()
    write_legend_recovery()
    write_story_compounding()
    print(f"Formula assets written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
