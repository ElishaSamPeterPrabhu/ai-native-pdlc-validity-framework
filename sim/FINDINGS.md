# Phase B Findings (simulation lab)

Outputs: `data/sobol_indices.json`, `data/identifiability.json`, `data/figures/fig1–3`.
These findings define formula v1 and constrain the Phase-C campaign design.

## Headline results

1. **The pipeline's simulated value is large and concentrated on hard tasks.**
   Full pipeline vs bare agent (Monte Carlo, k=3, n=20 tasks/stratum):
   Low ≈ 1.00/0.93 pass@1, Medium ≈ 1.00/0.83, High ≈ 0.93/0.23. The recovery loop
   matters most exactly where decay pressure is highest — the ODE's central
   qualitative prediction, reproduced by the micro-simulation (fig3).

2. **ODE fits the micro-process well.** Piecewise-constant ODE fitted to 540
   simulated trajectories: RMSE ≈ 0.054 on V_obs. The two-rate structure
   (recovery vs decay) is an adequate macro-model of the step-level process.

3. **Identifiability warning (design-critical).** With activities constant within
   an arm, several factor weights are collinear: the fit recovered `ci_gate` and
   `mcp_context` but drove `agentic_qa`/`fix_loop`/`spec_refinement` to zero while
   still fitting well — their effect was absorbed by correlated terms. Consequences
   for Phase C:
   - Ablation arms MUST be analyzed as arm-level contrasts (ΔV*, Δpass^k between
     ON/OFF arms), not only via joint weight fitting.
   - Factors that toggle together in the pipeline (QA agent and fix loop) should
     get at least one arm separating them, or be reported as a combined factor.
   - Within-run activity variation (fix-loop budget decaying, entropy growing)
     is what makes weights separable — the collectors must capture it faithfully.

4. **Ceiling effect at full pipeline.** With everything enabled, final V_obs
   variance is tiny (sd ≈ 0.007–0.014): the setup saturates the outcome on our
   simulated task mix. Campaign implication: include the bare and single-factor-off
   arms (where variance lives), and make High tasks genuinely hard, otherwise the
   data cannot rank factors.

5. **Sobol ranking (total-order, HIGH stratum):** commit cadence
   (`steps_per_commit`) dominates, then `fix_success_prob`,
   `refinement_ambiguity_cut`, `ci_catch_prob`, context multipliers, `qa_catch_prob`.
   On MEDIUM, `qa_catch_prob` and cadence lead. Reading: checkpoint frequency and
   repair effectiveness are the highest-leverage real-world measurements; all nine
   parameters are non-inert (none can be dropped outright in v1), but confidence
   intervals are wide — treat ranks, not magnitudes, as the signal.

## Formula v1 decisions (recorded in theory/formula-changelog.md)

- Keep all decay proxies and registry factors (nothing inert).
- Primary estimand switches from "jointly fitted w_f" to "arm-contrast Δ metrics",
  with joint fitting as a secondary analysis.
- QA-agent and fix-loop reported jointly unless the campaign includes the arm that
  separates them.
- Default decay form for fitting: HYBRID (additive + C×σ interaction); the
  multiplicative v0 form is retained only as an AIC/BIC baseline.

## Completion-guard hook ablation (2026-07-27)

Outputs: `data/hooks_predictions.json` (registered before the run),
`data/hooks_ablation.json`, `data/figures/fig4_hook_ablation.png`.
Protocol: seed 20260727, 2160 runs, `hook_detect_prob` swept over
{0.5, 0.6, 0.7, 0.8, 0.9, 0.95}. Simulation-only; no live hook telemetry.

### Mechanism under test

`completion_guard_hook` is a terminal recovery factor in `R(t)`. When the agent
stops with broken verifier checks, the guard detects missing evidence per check
with probability `hook_detect_prob` and forces one bounded repair pass through the
existing `fix_success_prob`. It cannot catch semantic misreads that leave checks
green.

### Measured results (mean [min, max] over the detect-prob sweep)

| Arm | Stratum | ΔV_obs | Δ pass@1 | Δ pass^3 | Pred. ΔV match |
| --- | --- | --- | --- | --- | --- |
| full_pipeline | medium | +0.000 [0.000, +0.002] | +0.003 [0.000, +0.017] | +0.006 | agree (near-zero) |
| full_pipeline | high | +0.002 [0.000, +0.006] | +0.025 [0.000, +0.067] | +0.049 | agree (near-zero/small) |
| fix_cap_1 | medium | +0.001 [0.000, +0.004] | +0.011 [0.000, +0.033] | +0.024 | below predicted ΔV range |
| fix_cap_1 | high | +0.005 [+0.003, +0.008] | +0.053 [+0.033, +0.083] | +0.104 | below predicted ΔV range |
| no_agentic_qa | medium | +0.003 [0.000, +0.008] | +0.025 [0.000, +0.067] | +0.049 | below predicted ΔV range |
| no_agentic_qa | high | +0.012 [+0.003, +0.022] | +0.092 [+0.017, +0.167] | +0.164 | below predicted ΔV range |

### Prediction check

- Direction was correct: every aggregate mean ΔV_obs is ≥ 0.
- Full-pipeline near-zero ceiling effect matched the pre-registered prediction.
- Degraded-arm ΔV_obs magnitudes were smaller than predicted. The micro-simulation
  already leaves high mean validity even without agentic QA, so absolute V deltas
  stay modest. The stronger measured signal is pass@1 / pass^3, especially on
  `no_agentic_qa` / high (+9.2 pp mean pass@1; up to +16.7 pp at detect=0.9).
- Claim for the abstract: across the plausible detect-prob range, adding the
  completion guard to a high-complexity setup without agentic QA raises pass@1 by
  about +2 to +17 percentage points and mean V_obs by about +0.003 to +0.022.
  On a saturated full pipeline the validity gain is near zero.

### Method fixes discovered during the run

- Arm RNG streams must be per-run, not shared across an arm, or later runs inherit
  randomness consumed by earlier hook interventions and break ON/OFF pairing.
- A true terminal checkpoint is required before the guard: trailing steps after the
  last commit can leave stale V_obs and fabricate negative deltas.
