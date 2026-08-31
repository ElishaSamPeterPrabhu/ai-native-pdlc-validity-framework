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

## Discipline-factor ablation (2026-08-30, formula v1.3)

Outputs: `data/discipline_predictions.json` (registered before the run),
`data/discipline_ablation.json`, `data/figures/fig5_discipline_ablation.png`.
Protocol: seed 20260830, 1,920 runs (4 factors × 2 arms × 2 strata × ON/OFF ×
20 tasks × 3 repeats), fixed mechanism knobs (no sweep in round 1).
Simulation-only; no live telemetry. Design source for the mechanisms:
TDD-enforcing harness practice (llama-leash "conductor").

### Mechanisms under test

- `red_first_discipline`: without it, 35% of successful repairs are vacuously
  green (test-after theater) — actually broken but masked from CI, QA,
  self-repair, the completion guard, and anchored review.
- `reviewer_independence`: terminal review catches actually-broken checks at
  0.75 in a fresh context (including masked/stale) vs 0.25 anchored
  (visible checks only).
- `evidence_freshness`: trailing polish edits invalidate green checks at 0.12
  after the last verify; freshness forces a terminal re-verify plus one
  bounded repair pass.
- `doctrine_reinjection`: without it, per-step error ramps to 1.8× by end of
  run (process amnesia).

New telemetry: `self_claimed_pass` per run, giving a **calibration gap**
(self-claimed − objective pass rate) per arm.

### Measured results (ΔV_obs / Δpass@1 / Δcalibration-gap, ON − OFF)

| Factor | Arm | Stratum | ΔV_obs | Δpass@1 | Δcal-gap | Pred. match |
| --- | --- | --- | --- | --- | --- | --- |
| red_first_discipline | full_pipeline | medium | +0.006 | +0.050 | −0.050 | below range |
| red_first_discipline | full_pipeline | high | +0.061 | +0.533 | −0.550 | agree |
| red_first_discipline | no_agentic_qa | medium | +0.002 | +0.017 | −0.017 | agree |
| red_first_discipline | no_agentic_qa | high | +0.036 | +0.317 | −0.350 | agree |
| reviewer_independence | full_pipeline | medium | +0.000 | +0.000 | +0.000 | agree |
| reviewer_independence | full_pipeline | high | +0.003 | +0.033 | +0.000 | agree |
| reviewer_independence | no_agentic_qa | medium | +0.000 | +0.000 | +0.000 | below range |
| reviewer_independence | no_agentic_qa | high | +0.010 | +0.083 | +0.000 | below range |
| evidence_freshness | full_pipeline | medium | +0.085 | +0.367 | −0.583 | agree |
| evidence_freshness | full_pipeline | high | +0.058 | +0.317 | −0.633 | agree |
| evidence_freshness | no_agentic_qa | medium | +0.077 | +0.283 | −0.500 | agree |
| evidence_freshness | no_agentic_qa | high | +0.078 | +0.250 | −0.617 | agree |
| doctrine_reinjection | full_pipeline | medium | +0.000 | +0.000 | +0.000 | agree |
| doctrine_reinjection | full_pipeline | high | +0.003 | +0.033 | +0.000 | agree |
| doctrine_reinjection | no_agentic_qa | medium | +0.010 | +0.050 | +0.000 | below range |
| doctrine_reinjection | no_agentic_qa | high | +0.022 | +0.100 | +0.000 | below range |

Prediction agreement: 11/16 cells inside the pre-registered ΔV_obs range;
5 below range (all reported as-is); direction non-negative in 16/16.

### Reading the results (claim discipline applies)

- `evidence_freshness` is the strongest and most uniform factor in round 1
  (ΔV_obs +0.058 to +0.085 in every cell) and produces the largest
  calibration-gap reductions (−0.50 to −0.63): stale terminal evidence is a
  large, arm-independent source of false "done" claims under this mechanism.
- `red_first_discipline` dominates on high-complexity work (Δpass@1 +0.53 on
  the full pipeline) because vacuous greens are unrecoverable by every
  downstream stage. The magnitude is conditional on the assumed
  `vacuous_green_prob=0.35`; treat it as mechanism-conditional, not a fitted
  effect size.
- `reviewer_independence` under-performed its prediction. Round 1 isolated it
  from the dishonest-evidence mechanisms (vacuous/stale knobs off in its
  cells), so the independent reviewer's unique ability — seeing masked and
  stale checks — was never exercised. A round-2 interaction arm
  (red-first OFF × independent review ON) is the right test, not a bigger
  catch probability.
- `doctrine_reinjection` deltas were positive but below range on the weakened
  arm: commit-time self-repair absorbs more drift breakage than predicted.
- Calibration gap is measurable and moves as predicted for the two
  evidence-honesty factors; it is the simulation counterpart of the live
  `agent_claimed_done` vs QA-outcome signal already collected in intake.

### Claim boundaries

- All numbers are synthetic ablation contrasts under stated mechanism knobs;
  none are live effect sizes or fitted weights.
- The four factors stay `simulation-only` in the registry until live telemetry
  exists (same tier as `completion_guard_hook`).
- Sobol and identifiability re-runs including the new mechanisms are deferred
  to a later round.

### External cross-check target (llama-leash, 2026-08-30)

Level 0 verification artifacts live in `data/external/llama-leash/`
(inspect setup-manifest, documented-setup intake, score pack, factor mapping).

- `inspect` reported 12 measurement gaps: conductor's controls live in a
  TypeScript plugin, not `.cursor`/`.github` conventions — the intake path
  covers them as declared (`reported`) evidence.
- `score` on the documented setup returned **n_scored=0, V\* missing**: no run
  telemetry exists, so the framework refused to produce a number. This is the
  intended insufficient-data behavior, exercised on a real external repo.
- All four v1.3 discipline factors are live, mechanically enforced controls in
  that harness; under the v1.1 registry the setup would have been
  indistinguishable from a plain tests-exist pipeline.
- **Measured round 1 closed (local Mac, 2026-08-31):** benchmark calibration
  `self_score − objective` observed at **0.0** on ornith-9b Q4_K_M
  (merge-ranges, author-default preset); see
  `data/external/llama-leash/benchmark-results.json`. T0 three-arm conductor
  bench stopped at **8/30 cells** — baseline 3/3 hidden pass, doctrine 2/3.
  The **conductor arm is not_computable** on this stack: llama.cpp Jinja
  (Qwen/ornith) allows only one system message, and only as `messages[0]`;
  conductor appends doctrine as extra system entries. Preflight 2026-08-31
  reproduced a first-turn Jinja 500 in seconds; `opencode run --agent
  conductor-orchestrator` produced zero tokens in 90s. Remaining T0 cells
  were not run. Cross-check vs `data/discipline_ablation.json` is in
  `cross-check.json` (`round_1_closed`): no magnitude claims, no sim
  direction claim confirmed or refuted. `score` on this intake still returns
  **n_scored=0, V\* missing** (no run telemetry). Unblocking conductor is a
  separate llama-leash/serving change, not this round.
