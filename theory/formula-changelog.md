# Formula Changelog

Every revision of the validity model is recorded here with the evidence that forced it.
The formula is a living hypothesis: v0 is the starting structure, not the conclusion.

## v0 — 2026-07-19 — Initial structure (assumed, not fitted)

Source: the research outline ("Measuring Autonomous Agent Validity") formalized in
`derivation.md` and made executable in `formula.py`.

- Core ODE: `dV/dt = (1 − V)·R(t) − V·D(t)`, derived from per-step Bernoulli success
  via the hazard-rate continuous limit (assumptions A1–A6 in derivation.md §7).
- Changes vs the raw outline:
  - All decay proxies normalized to [0, 1] (the outline's O(t) and H_c were unbounded,
    making the decay product's magnitude unit-dependent).
  - Recovery generalized from hardcoded `αT + βM + γρι` to a factor registry
    `R = Σ w_f·f(t)` so any setup addition (MCP, rules, QA gate, review bot) can be
    valued by ablation. The original three terms are registry entries.
  - Three candidate decay forms declared (multiplicative / additive / hybrid) instead
    of assuming the outline's multiplicative form; selection deferred to data (Phase D).
  - Delivered validity separated from trajectory validity:
    `V_delivered = V(t_end) · pass^k · max(0, 1 − O_A/O_M)`.
- All weights are placeholders (deliberately equal across factors) — meaningless until
  Phase B (simulation pruning) and Phase D (fitting).

## v1 — 2026-07-19 — Phase B (simulation) decisions

Evidence: `sim/FINDINGS.md`, `data/sobol_indices.json`, `data/identifiability.json`.

- No parameter is inert (all Sobol total-order indices materially > 0 on medium/high
  strata): every proxy and registry factor survives into v1.
- ODE structure validated against the micro-simulation: piecewise-constant fit
  achieves RMSE ≈ 0.054 on V_obs across 540 synthetic trajectories.
- Identifiability caveat adopted into the analysis plan: jointly fitted factor
  weights are collinear when activities are constant within an arm, so the primary
  estimand is the **arm contrast** (ΔV*, Δpass^k between ON/OFF arms); joint weight
  fitting is secondary. QA-agent and fix-loop are reported as a combined factor
  unless a separating arm is run.
- Default decay form for fitting: HYBRID; multiplicative v0 form kept only as a
  model-comparison baseline.
- Campaign design constraints: include bare and single-factor-off arms (outcome
  variance vanishes at full pipeline), and ensure High tasks are genuinely hard.

## v1.1.1 — 2026-08-04 — Publish contract alignment (no new fit)

Evidence: `framework/CONTRACT.md`, research-preview packaging.

- `FORMULA_VERSION` string aligned to **v1.1** (was still `"v0"` in code).
- Default `decay_rate(..., form=)` switched to **HYBRID** to match Phase-B / fitting plan;
  MULTIPLICATIVE remains for AIC/BIC comparison only.
- Exported `CORE_FITTED_FACTORS`, `SIMULATION_ONLY_FACTORS`, `EVIDENCE_STATUS`,
  and `DEFAULT_DECAY_FORM_NAME` for the portable framework package.
- Claim boundary restated: synthetic `data/fit_results.json` is not factory calibration;
  completion-guard remains simulation-only until live telemetry.

## v1.1 — 2026-07-27 — Completion-guard hook as a recovery factor (simulation)

Evidence: `sim/FINDINGS.md` (hook ablation section), `data/hooks_ablation.json`,
`data/hooks_predictions.json` (predictions registered before the run).

- Added registry factor `completion_guard_hook` (stage: review). Activity is 1 only
  at the completion-validation boundary; contribution enters `R(t)` and does not
  alter `D(t)` directly.
- Mechanism under test: without the hook, an agent may terminate with unmet
  verifier checks; with the hook, completion is challenged when acceptance
  criteria, targeted-test results, or QA evidence are missing, triggering one
  bounded repair attempt through the existing fix success probability.
- Status: **simulation-only**. No live `.cursor/hooks.json` or hook telemetry yet.
  Measured arm-contrast deltas from the detect-prob sweep are provisional
  contributions, not fitted Modus campaign weights.
- Claim discipline: predictions were registered before the run; results report
  agreement and disagreement with those predictions. Negligible or negative
  deltas are reported as-is.

## v2 — pending real campaign data (machinery ready)

The Phase-D pipeline (`analysis/fit.py`) is built and validated end-to-end on
synthetic collector-shaped data: arm contrasts with bootstrap CIs, joint ODE fits
per decay form, AIC/BIC model comparison, and telemetry-form hypothesis tests.
Dry-run result on synthetic data (not evidence, pipeline validation only): the
additive/hybrid decay forms beat the v0 multiplicative form on AIC, consistent
with the derivation's fragility argument (derivation.md §4).

v2 ships when the real campaign lands: fitted weights, the data-selected decay
form, measured factor values (Δ per ablation — the MCP experiment), and re-tested
hypotheses, all written into `formula.py` with this entry updated.
