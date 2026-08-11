# Derivation: From Per-Step Success to the Validity ODE

This document derives the validity model from first principles, states every assumption
explicitly, and defines the normalized, dimensionless proxies used for fitting. The
executable form lives in `formula.py`; revisions are recorded in `formula-changelog.md`.

---

## 0. What V(t) is, observably

**Definition.** For a run of a task with a hand-written verifier composed of m checks,
the observed validity at time t is the verifier pass-fraction at the latest commit
checkpoint at or before t:

    V_obs(t) = (number of verifier checks passing at checkpoint(t)) / m  ∈ [0, 1]

This makes V(t) a measurable time series (dense grading, one point per agent commit),
not a philosophical quantity. Everything below is a model of how V_obs evolves.

---

## 1. The base: compounding per-step error (discrete)

Model an agent run as a sequence of steps (tool calls / edits) i = 1..n, each succeeding
independently with probability p_i.

**Assumption A1 (Markov steps):** the outcome of step i depends only on the current
workspace state, not the full history.
**Assumption A2 (independence):** step failures are independent given the state.
(Both are wrong in detail — error loops correlate failures — which is exactly what the
contextual-entropy term will re-introduce.)

Probability the trajectory is still valid after n steps:

    P_valid(n) = ∏_{i=1}^{n} p_i

With a constant per-step error rate ε (p_i = 1 − ε):

    P_valid(n) = (1 − ε)^n ≈ e^{−εn}        (for small ε)

This is the compounding-error problem: validity decays *exponentially* in the number of
steps. A 1% per-step error rate gives P_valid(100) ≈ 37%, P_valid(300) ≈ 5%. This single
line is why long-horizon autonomy fails without recovery mechanisms, and it is
empirically visible in METR's 50%-vs-80%-reliability horizons (the 80% horizon is ~5×
shorter) and SWE-Marathon's <30% pass@1 on multi-hour tasks.

---

## 2. The continuous limit: decay as a hazard rate

Let steps occur at rate λ steps per unit time. Over an interval dt the agent takes λ·dt
steps, each destroying validity with probability ε(t). Then

    V(t + dt) = V(t) · (1 − ε(t))^{λ dt}  ≈  V(t) · (1 − ε(t) λ dt)

    ⇒  dV/dt = − D(t) · V(t),        D(t) ≡ λ ε(t)  ≥ 0

D(t) is a **hazard rate**: the instantaneous rate at which correct work becomes
incorrect (wrong edits, regressions, hallucinated interfaces). Pure decay — this is the
model of an agent with no tests, no QA, no repair loop.

---

## 3. Adding recovery: the logistic-form ODE

The setup pushes back: tests catch regressions, the QA agent rejects broken PRs, the fix
agent repairs them, checkpoints bound the damage. Model recovery as a rate R(t) ≥ 0 at
which *invalid* work is detected and repaired. Only invalid work can be repaired
(capacity 1 − V), and only valid work can decay (mass V):

    dV/dt = (1 − V(t)) · R(t)  −  V(t) · D(t)          … (ODE v0 structure)

**Assumption A3 (well-mixed):** any invalid fraction is equally likely to be caught by
recovery; any valid fraction equally likely to decay. (Verifier granularity per
component makes this reasonable at commit resolution.)

Properties worth stating because they become testable predictions:

- **Equilibrium.** For roughly constant R, D, V(t) relaxes toward

      V* = R / (R + D)

  with time constant τ = 1/(R + D). High-decay tasks (large blast radius, vague spec)
  need proportionally large recovery to hold the same V*. This is the mathematical form
  of "the strictness of the setup must scale with task complexity".

- **The static formula is the equilibrium special case.** The original static validity
  V = (∏ p_i) · C · max(0, 1 − O_A/O_M) is recovered as: ∏ p_i ≈ e^{−∫D dt} is the
  no-recovery trajectory factor, C = pass^k the cross-run consistency measurement, and
  the review-economics factor is the gate applied to the *delivered* artifact (Section 6).

---

## 4. Decomposing D(t): the decay proxies, normalized

All proxies are mapped to dimensionless [0, 1] via saturating transforms so no term
dominates by unit choice alone. Raw telemetry → normalized form:

| Symbol | Meaning | Raw telemetry | Normalized proxy (∈ [0,1]) |
| --- | --- | --- | --- |
| H_c(t) | Contextual entropy | current tokens T_cur, cap T_max; failed tool calls A_fail, total A_total | `h = (T_cur/T_max) · (A_fail/A_total dampened)`; ĥ = min(1, h) — see formula.py `entropy_proxy` |
| O(t) | Diff opacity | ΔLOC, Δ cyclomatic complexity, files touched N_f | `ô = 1 − exp(−(log2(1+ΔLOC) · (1+ΔCC_norm) · N_f) / s_O)` with saturation scale s_O |
| C_b | Blast radius / coupling | dependency-graph reach D(F_changed), total D_tot | `ĉ = D(F_changed) / D_tot` (already in [0,1]) |
| σ_spec | Spec ambiguity | 3 independently generated plans, pairwise embedding cosine sim | `σ̂ = 1 − mean pairwise cosine similarity` (clipped to [0,1]) |

**Candidate functional forms for D(t)** (Phase D discriminates by AIC/BIC on real data):

- **D-mult (v0 assumption):** D = d₀ · ĉ · σ̂ · ĥ · ô
  — any factor ≈ 0 switches decay off entirely. Fragile: a task with zero ambiguity but
  huge blast radius would be predicted safe, which is implausible.
- **D-add (weighted linear):** D = d₀ + d_c·ĉ + d_σ·σ̂ + d_h·ĥ + d_o·ô
  — each stressor contributes independently; d₀ is baseline slip rate.
- **D-hybrid (main effects + one interaction):** D-add + d_{cσ}·(ĉ·σ̂)
  — encodes the hypothesis that blast radius is most dangerous *when the spec is vague*
  (the C × σ_spec interaction from the outline's hypothesis table).

v0 ships D-mult (fidelity to the original outline); v1 default is D-hybrid pending
simulation; v2 is whatever the data selects.

---

## 5. Decomposing R(t): the factor registry

Recovery is a **sum over enabled setup factors** rather than a hardcoded α, β, γ triple:

    R(t) = Σ_{f ∈ registry, enabled} w_f · f(t),      f(t) ∈ [0, 1]

where f(t) is the factor's normalized activity signal and w_f its fitted weight
(units: validity per unit time). The original αT + βM + γρι is the special case with a
three-entry registry. Initial registry (each toggleable per experiment arm):

| Factor | Stage | Activity signal f(t) | Toggle |
| --- | --- | --- | --- |
| `spec_refinement` | ticket | 1 if issue was scaffolded into acceptance criteria | Issue Scaffolding automation on/off |
| `agentic_qa` | QA | 1 while QA agent reviews PRs on this run | QA Agent automation on/off |
| `fix_loop` | repair | fraction of iteration budget remaining | Fix Agent automation on/off; cap 1 vs 3 |
| `ci_gate` | QA | 1 if deterministic CI tests gate the PR | CI workflow on/off |
| `mcp_context` | dev | 1 if the Modus MCP server is available to the agent | MCP config present/absent |
| `rules_context` | dev | 1 if .cursor/rules present | rules files present/removed |
| `checkpointing` | dev | commit cadence: commits per unit time, saturated | prompt instruction on/off |
| `review_bot` | review | 1 if an external AI review bot is installed | bot installed/uninstalled |
| `human_alignment` | any | rate of needs-human / clarification events | deferred to iPad phase (M(t) = 0 for now) |

A factor's measured value is Δw_f from ON/OFF ablation arms; secondary readouts are
ΔV* (equilibrium shift) and Δpass^k.

---

## 6. The review-economics gate (delivered validity)

Trajectory validity is necessary but not sufficient: if reviewing the agent's PR costs
more than doing the work manually, the automation has negative value regardless of
correctness. Delivered validity applies the economic gate to the trajectory's end state:

    V_delivered = V(t_end) · pass^k · max(0, 1 − O_A / O_M)

- O_A: review overhead of the agent PR. Until human data exists, anchored to structural
  proxies (O(t_end)) calibrated against published effect sizes (AI PRs ≈ +20% review
  time; structural footprint predicts effort, AUC 0.96 — see research/related-work.md).
- O_M: estimated manual cost (the human-time estimate that also calibrates the task's
  complexity stratum, METR-style).
- pass^k: consistency across k i.i.d. repeats of the same task (τ-bench).

The trust gate verdict (dashboard / PR check) is a thresholding of V_delivered:
merge-worthy ≥ θ_hi > review-carefully ≥ θ_lo > abandon. Thresholds are chosen after the
campaign from the observed V_delivered distribution (e.g. tertiles), not assumed.

---

## 7. Assumptions ledger (for the paper's threats-to-validity section)

| # | Assumption | Where it bites | Mitigation |
| --- | --- | --- | --- |
| A1 | Markov steps | Error loops violate it | H_c term re-introduces history via failure-rate feedback |
| A2 | Independent failures | Correlated cascade failures | Fix-loop iteration telemetry captures cascades explicitly |
| A3 | Well-mixed recovery/decay | Recovery targets what QA can see | Verifier granularity per component; report per-check trajectories |
| A4 | Proxies are linearly related to their constructs | Saturating transforms are guesses | Sensitivity analysis on transform scales (s_O etc.) in Phase B |
| A5 | R, D piecewise-constant within a pipeline stage | Both vary within stages | Fit uses stage-segmented piecewise-constant R(t), D(t) |
| A6 | Fixed model (Composer 2.5) | Constants are model-specific | Model recorded in run metadata; model-as-factor deferred to v3 |

## 8. What Phase B must answer before real money is spent

1. Which parameters actually move V(t)? (Sobol indices — anything inert gets dropped in v1.)
2. Are the weights identifiable from ~30 trajectories per arm with ~5–15 commit
   checkpoints each? (Fit on synthetic data with realistic noise; check recovery of
   ground-truth w_f.)
3. Which D-form candidates are distinguishable at that sample size? (If D-add vs
   D-hybrid can't be separated, don't claim the interaction in the paper.)
