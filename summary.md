Here is the complete summary, end to end.

---

## 1. The original formula (from your research outline)

You started with two things written down but not derived:

**Static formula** — how much to trust a single PR:
\[ V = \left(\prod_{i=1}^{n} p_i\right) \times C \times \max\left(0, 1 - \frac{O_A}{O_M}\right) \]

- Multiply the success probability of every tool call the agent makes (compounding error)
- Multiply by consistency C (how repeatable the result is)
- Multiply by a review-economics gate (validity is zero if reviewing the PR costs more than doing the work manually)

**Dynamic formula** — how trust evolves during a run:
\[ \frac{dV}{dt} = (1-V)\cdot(\alpha T + \beta M + \gamma\rho\iota) - V\cdot(C \cdot \sigma_{spec} \cdot H_c \cdot O) \]

The problem: α, β, γ were free letters with no values. The decay term was multiplicative (meaning any single factor being zero switched off all decay, which is implausible). Proxies like O(t) were unbounded, making the product's magnitude arbitrary. Nothing was observable or fittable.

---

## 2. What we derived to reach v0

Starting from first principles, the chain is:

**Step 1 — Discrete compounding.** Each agent step succeeds with probability `p`. After `n` steps: `P_valid(n) = (1-ε)^n ≈ e^{-εn}`. This is the mathematical basis for why long-horizon agents fail — it's not an opinion, it's exponential decay.

**Step 2 — Continuous limit.** At λ steps per unit time, `dV/dt = -D·V` where `D = λε`. This is the "bare agent with no safety nets" model.

**Step 3 — Recovery term.** Tests, QA agents, fix loops repair broken work. Only invalid work can be repaired (capacity `1-V`). Only valid work can decay (mass `V`). So:
\[ \frac{dV}{dt} = (1 - V)\cdot R(t) - V\cdot D(t) \]

**Step 4 — The payoff.** Set `dV/dt = 0` to find where validity stabilises:
\[ V^* = \frac{R}{R + D} \]

This single line is the whole paper's core claim in one equation: **the strictness of your setup (R) must scale proportionally with the task pressure (D) to hold a given trust level**. The original static formula is just the equilibrium special case.

**Step 5 — Key upgrades from the original:**
- All proxies normalized to `[0,1]` (unbounded scales were broken)
- `αT + βM + γρι` replaced by a **factor registry** `R = Σ w_f·f(t)` — so any setup addition (MCP, rules file, QA gate, review bot) has a slot, and its weight comes from data, not assumption
- Three candidate decay forms declared (multiplicative, additive, hybrid) instead of assuming multiplicative — the data picks between them
- Delivered validity separated out: `V_delivered = V(t_end) · pass^k · max(0, 1 - O_A/O_M)`

---

## 3. Formula iterations: v0 → v1 → v2 (pending)

**v0** (July 19): Structured form above, all factor weights equal (0.10 each, deliberately meaningless placeholders). The decay form defaults to multiplicative for backward compatibility. This is "structure assumed, constants TBD."

**v1** (July 19, same day — from simulation): We ran 540 synthetic trajectories through a Monte Carlo agent model, fit the ODE, and ran Sobol sensitivity analysis. Key findings that changed the formula's operating assumptions:
- Nothing is inert — all 9 parameters move the outcome (no terms dropped)
- But jointly-fitted weights are collinear when factors are always-on together — so the **primary estimand switches from weight values to arm contrasts** (ΔV* between factor-ON and factor-OFF runs)
- Default decay form changes to HYBRID (additive + one interaction term) — the multiplicative form is kept only as a model-comparison baseline
- ODE fits the micro-simulation at RMSE ≈ 0.054, validating the two-rate structure

**v2** (pending — waiting for real run data): The fitting pipeline `analysis/fit.py` is fully built and dry-run validated. Once the real campaign data lands, v2 gets: fitted weights from actual runs, the AIC/BIC-selected decay form, measured per-factor values ("Modus MCP = +X validity on medium tasks"), and the re-tested hypotheses.

---

## 4. What we're doing right now with the agents — matching factors to observables

The live experiment is the mechanism for measuring the factor registry values. Here is how each formula factor maps to what the automations are actually doing:

| Formula factor | What it is in the pipeline | How it gets measured |
|---------------|---------------------------|---------------------|
| `spec_refinement` | Issue Scaffolding automation — structures raw issue into acceptance criteria | ON arm: issue goes through scaffolding. OFF arm: raw one-liner seeded directly. ΔV* is the measured value of structured specs |
| `agentic_qa` | QA Agent automation | ON: runs after every PR open. OFF: disabled. Difference in merge rate and fix iterations |
| `fix_loop` | Fix Agent automation (3-iteration cap) | ON: runs on `qa-failed`. The structured QA REPORT (new) lowers the agent's context entropy H_c, reducing iteration count |
| `ci_gate` | `merge-gate.yml` core check (lint + build + tests) | ON: required check in branch protection. Iteration count and failure patterns |
| `mcp_context` | Modus in-repo MCP server (`mcp/` directory) | ON: `.cursor/mcp.json` points at it. OFF: file removed. Measures how much component docs help the agent |
| `figma_mcp` | Figma MCP added to Dev Agent automation | ON: agent can fetch design specs. Particularly measurable on design-system issues |
| `rules_context` | `.cursor/rules/code-guidelines.mdc` in the repo | ON by default; ablation arm removes it |
| `qa_playwright` | Playwright MCP + `playwright-e2e.yml` CI workflow (merged today) | ON: QA Agent extracts computed CSS, verifies behavior in real browser. The delta from `npm test` passing but Playwright catching something is the measured value |
| `qa_visual` | `visual-regression.yml` CI (Lost Pixel, merged today) | Style-only PRs route here; screenshot diff catches regressions |
| `qa_a11y` | `a11y-check.yml` as a blocking gate (updated today) | Regression-baseline: only new violations block |

**The two issues currently running (#30 end-icon slot, #33 button contrast) are round 1 — the "before" measurement** with the baseline setup. After they complete:

1. Run `python harness/collect_run1.py` to snapshot telemetry
2. Merge the Tier-1 hardening (already on `main` now after PR #32)
3. Re-run the same issues as round 2 — the ΔV* between round 1 and round 2 is the measured validity value of the entire QA hardening stage

That before/after number is the headline experiment result that goes in the paper alongside the formula.