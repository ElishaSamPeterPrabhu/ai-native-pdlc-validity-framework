# Related Work: Positioning the Validity Formula (as of July 2026)

Purpose: record what the state of the art measures, what we adopt from each line of work,
and what remains genuinely ours. This is the source material for the paper's related-work
section and for reviewer defense ("how is this different from X?").

## 1. Summary matrix

| Work | What it measures | Grading method | What we adopt | What it does NOT do (our gap) |
| --- | --- | --- | --- | --- |
| **τ-bench** (Sierra, arXiv 2406.12045) | Tool-agent-user interaction reliability in customer-service domains | Final DB state vs annotated goal; **pass^k** = all k i.i.d. trials succeed | pass^k as our consistency metric C; end-state (not transcript) verification | No software engineering, no time dynamics, no review economics |
| **METR time horizons** (arXiv 2503.14499; metr.org/time-horizons) | Task duration (human-expert time) at which an agent succeeds with 50% / 80% reliability; doubling ~7 months | Logistic fit of success probability vs human task duration | Complexity stratification method (calibrate Low/Med/High by human-time); the compounding-error empirical grounding | Measures capability trend, not a per-run trust model; no system/guardrail factors; no telemetry proxies |
| **DeepSWE** (Datacurve, arXiv 2607.07946) | 113 original long-horizon SWE tasks, 5 languages, contamination-free | Hand-written implementation-agnostic verifier per task (1.4% judge disagreement vs 32.4% for inherited tests) | Verifier design: hand-written, accepts any correct implementation, never inherited PR tests | Single pass/fail per run; no partial progress, no dynamics, no human-in-loop economics |
| **SWE-Marathon** (arXiv 2606.07682) | 20 ultra-long-horizon tasks (multi-hour, multi-stage); no agent exceeds 30% pass@1 | Multi-component pass distributions; failure-mode taxonomy | Evidence that long-horizon failure is the norm (motivates decay term); failure taxonomy categories as labels for our failed runs | Describes failure, does not model it as a dynamical system; no recovery factors |
| **Long-Horizon-Terminal-Bench** (arXiv 2607.08964) | 46 long terminal tasks with dense subtask grading | Reward-based partial-progress scoring per subtask | Dense grading idea → our V_obs(t): run the verifier at every commit, not just at the end | Terminal tasks, not PR lifecycle; no consistency (pass^k), no review stage |
| **"AI Writes Faster Than Humans Can Review"** (arXiv 2607.01904) | Longitudinal enterprise study of a 2× AI mandate | Observational: review coverage, latency, comment substance | Empirical anchors: AI PRs take ~20–22% longer review-to-merge; human review coverage fell 89%→68%; substantive review 39%→21% | Measures the overhead, doesn't model when a PR deserves trust |
| **"Habituation at the Gate"** (arXiv 2606.22721) | 400 reviewers, 11,429 reviews of agent PRs | Within-reviewer longitudinal stats | Evidence that reviewer trust drifts irrationally (+14.5pp approval, −22% comment effort, +3.5× latency) → motivates an objective V(t) instead of subjective trust | No objective validity signal proposed |
| **Early-Stage Prediction of Review Effort** (arXiv 2601.00753) | 33,707 agent PRs; predicts high-maintenance PRs at creation (AUC 0.96) | Static complexity cues (files, patch size, entropy) | Confirms our O(t) proxy family (structural footprint) predicts review cost better than intent text | Point prediction at creation time; no dynamics, no guardrail valuation |
| **Review-bot benchmarks** (Greptile/Augment/DeepSource/Martian, 2026) | Bug catch rates of AI review bots | Seeded-bug PRs | Candidate review-stage factors (Bugbot, CodeRabbit, Greptile) | Vendor-run results conflict wildly (44–82% catch, F1 30–60%); no neutral, formula-grounded valuation — our ablation provides one |

## 2. What we adopt (explicit)

1. **pass^k** (τ-bench): our consistency factor. For per-trial success p, pass^k ≈ p^k; reported as the fraction of tasks where all k repeats pass.
2. **Human-time complexity strata** (METR): Low/Med/High task strata are calibrated by estimated human completion time, and analysis includes a logistic success-vs-complexity fit as a sanity baseline.
3. **Hand-written implementation-agnostic verifiers** (DeepSWE): one verifier per task, checks requested functionality, accepts any correct implementation. Never graded by inherited repo tests alone.
4. **Dense partial-progress grading** (LH-Terminal-Bench): verifier executed at every agent commit → V_obs(t) time series, the observable the ODE is fitted against.
5. **Review-economics anchors** (2607.01904, 2606.22721, 2601.00753): until we collect human review data, the O_A/O_M term is anchored to published effect sizes (≈20% longer review-to-merge for AI PRs; structural footprint predicts effort at AUC ≈ 0.96).

## 3. What is novel (the paper's claim)

To our knowledge, no existing work does all of the following together:

1. **Trust as a fitted dynamical system.** Benchmarks output static scores; we model per-run validity V(t) as an ODE (recovery vs decay) and fit its constants from telemetry.
2. **Factor valuation by ablation.** The recovery term is a registry sum R(t) = Σ w_f·f(t); any setup addition (an MCP server, rules files, a QA gate, a review bot) receives a measured weight from ON/OFF arms — "this MCP is worth +X equilibrium validity" is a number, not an opinion.
3. **The serverless label-handoff pipeline as the instrument.** Stages (scaffold → dev → QA → fix) hand off via GitHub labels/comments only; every transition is a timestamped event, so the experiment infrastructure doubles as the telemetry source. ~2,750 runs/7d at 91.8% success in production use.
4. **Review economics inside the validity score.** Validity is zero if reviewing costs more than writing; existing benchmarks ignore the reviewer entirely.

## 4. Threats reviewers will raise (and our answers)

- *"Your V(t) is just test pass rate."* — V_obs is the observable; the contribution is the fitted dynamics (which factors move it, how fast, and the equilibrium prediction per task class), plus the review-economics gate.
- *"Constants won't generalize beyond Modus."* — Agreed; constants are repo-specific by design. The claim is the structure and method generalize (Phase E genericity check re-fits constants on a non-frontend repo).
- *"Vendor benchmarks already rank review bots."* — They disagree with each other by up to 37 points on the same tool; our ablation is neutral and expressed in validity units rather than catch-rate units.
- *"k=3 is small for pass^k."* — Correct; we report pass^k with exact binomial CIs and treat it as a screening signal, with k increased on the tasks where arms differ.
