# Paper skeleton: Measuring Autonomous Agent Validity

Working structure for the full paper/presentation. Each section lists its source
material in this workspace.

## 1. Introduction: the review bottleneck
- Industry shift: writing → reviewing (Thewhy.md §1; arXiv 2607.01904 anchors).
- Trust decays during execution; static benchmarks can't see it (Thewhy.md §2).
- Contribution list (to our knowledge, in combination): (a) fitted dynamical trust model, (b) factor valuation by
  ablation, (c) the serverless label-handoff pipeline as instrument, (d) review
  economics inside the validity score.
- Source: `research/related-work.md` §3.

## 2. Related work
- Benchmarks: τ-bench (pass^k), METR (time horizons), DeepSWE (verifiers),
  SWE-Marathon / LH-Terminal-Bench (long horizon, dense grading).
- Review-overhead studies (2607.01904, 2606.22721, 2601.00753).
- Review-bot benchmark disagreement motivating neutral ablation.
- Source: `research/related-work.md` (full matrix + threats table).

## 3. The system: a serverless autonomous pipeline
- Architecture: Issue Scaffolding → Dev → QA → Fix, label/comment handoff bus;
  production stats (~2,750 runs/7d, 91.8%).
- Every transition is a timestamped GitHub event → instrument = system.
- Source: plan §System architecture; `harness/RETARGET-RUNBOOK.md` (operational
  detail); screenshots of the automations.

## 4. The model: from compounding error to a validity ODE
- Derivation: per-step Bernoulli → hazard rate → dV/dt = (1−V)R − VD;
  equilibrium V* = R/(R+D); static formula as equilibrium special case.
- Normalized proxies (entropy, opacity, blast radius, ambiguity).
- Factor registry: R = Σ w_f·f(t); ablation as the valuation method.
- Delivered validity: V(t_end) · pass^k · review-economics gate.
- Assumptions ledger (A1–A6) → threats-to-validity section.
- Source: `theory/derivation.md`, `theory/formula.py`, `theory/formula-changelog.md`.

## 5. Simulation: structure checks before spend
- Monte Carlo micro-process vs ODE macro-model (RMSE ≈ 0.054).
- Sobol sensitivity: commit cadence + repair effectiveness dominate; nothing inert.
- Identifiability: arm contrasts as primary estimand (collinearity warning).
- Figures: fig1 equilibrium, fig2 time-to-collapse, fig3 pipeline value.
- Source: `sim/`, `sim/FINDINGS.md`, `data/figures/`.

## 6. Experiments on Modus Web Components
- **Console Automations pilot (done):** diagnose/improve on Dev/QA/Fix —
  medium PR #34 (open loop) → Dev PRE-OPEN PR GATE + QA/Fix wiring →
  medium PR #42 (closed QA pass). Source:
  `paper/modus-pilot-abstract-summary.md`. Scores are placeholder /
  `intake_pseudo` (not repo-fitted).
- **Harness ablation campaign (deferred):** fork instrumentation, task suite,
  verifier design, baseline + one-factor ablations, k=3. Source:
  `harness/tasks/`, `harness/PILOT-STATUS.md`.

## 7. Results
- **Available now:** Monte Carlo / completion-guard simulation structure checks;
  console Automations before/after (#34→#42) with placeholder directional V\*.
- **Still from campaign (future):** arm contrasts with CIs; decay-form AIC/BIC →
  formula v2; hypothesis tests (opacity→failure, blast-radius→iterations).
- Source when fitted: `analysis/fit.py` → `data/fit_results.json` (currently
  SYNTHETIC until live harness metrics).

## 8. The deliverable: dashboard and trust gate
- Live V(t), decay-term breakdown, fleet pass^k, PR verdict.
- Source: `dashboard/`; screenshot `data/figures/dashboard-preview.png`.

## 9. Limitations and future work
- Constants are repo/model-specific (genericity protocol + pass criteria:
  `analysis/GENERICITY-PROTOCOL.md`).
- M(t) human-alignment and review-time ground truth: iPad phase.
- k=3 pass^k CIs; single fixed model (Composer 2.5).

## 10. Conclusion
- Trust is a property of the setup, measured, not assumed; strictness must scale
  with task pressure (V* = R/(R+D) as the one-line summary).
