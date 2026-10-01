# Formula Application Report — All Phases

**Scope:** Formula development, simulation, and Modus pilot work completed through
2026-08-30.

**Current formula:** v1.1  
**Live-score provenance:** `weight_source=placeholder`,
`record_kind=intake_pseudo`  
**Live runs used for calibration:** 0

> The numerical Modus scores in this report are directional pilot scores. They are
> not repository-fitted weights, live trajectory measurements, or a production
> trust threshold.

## Executive result

The formula was numerically applied to two medium-complexity PRs in the Modus
experiment fork:

| Measure | PR #34 baseline | PR #42 retest | Change |
| --- | ---: | ---: | ---: |
| Recovery rate, R | 0.2000 | 0.3000 | +0.1000 |
| Decay rate, D | 0.1562 | 0.1066 | −0.0496 |
| Equilibrium validity, V* | 0.5615 | 0.7377 | +0.1762 |

The aggregate mean V* was **0.6496**. PR #34 exposed a broken Dev–QA–Fix loop.
After loop controls were introduced, PR #42 reached QA PASS after one repair.
That is evidence of a successful directional intervention on one retest, not
evidence of calibrated or sustained performance.

## 1. Shared formula

Observed validity is the fraction of hand-written verifier checks passing at the
latest checkpoint:

```text
V_obs(t) = checks passing at checkpoint(t) / total checks
```

The model balances recovery of invalid work against decay of valid work:

```text
dV/dt = (1 − V(t))·R(t) − V(t)·D(t)
```

When R and D are approximately steady, the equilibrium is:

```text
V* = R / (R + D)
```

The recovery rate is a registry sum:

```text
R(t) = Σ w_f·f_f(t)
```

Here, `f_f(t)` is a factor's normalized activity in `[0,1]` and `w_f` is its
weight. This registry replaced a fixed three-term recovery expression so that
setup controls such as QA, CI, repair, rules, and review can be switched off in
ablation arms and valued independently.

Formula v1.1 uses the hybrid decay form by default:

```text
D = 0.01
  + 0.05·Hc
  + 0.05·O
  + 0.05·Cb
  + 0.05·σ
  + 0.05·Cb·σ
```

The decay inputs are:

- `Hc`: contextual entropy, including context saturation and failed tool calls.
- `O`: diff opacity, derived from changed lines, complexity, and files touched.
- `Cb`: blast radius, based on dependency reach.
- `σ`: specification ambiguity, based on disagreement among independent plans.
- `Cb·σ`: the hybrid interaction for a broad change under an ambiguous spec.

The live intake scorer did not have full telemetry for these constructs. It used
the documented PR-level approximations described in Section 4.

## 2. How factors and weights were chosen

### Recovery factors

Factors were selected because they are observable, toggleable parts of an
AI-native delivery setup rather than attributes of a particular model:

| Lifecycle stage | Factors | Reason for inclusion |
| --- | --- | --- |
| Ticket | `spec_refinement` | Tests whether clearer acceptance criteria improve recovery. |
| Development | `mcp_context`, `rules_context`, `checkpointing` | Tests context quality and damage containment. |
| QA | `agentic_qa`, `ci_gate` | Represents independent machine verification. |
| Repair | `fix_loop` | Represents detected failures being corrected and returned to QA. |
| Review | `review_bot`, `human_alignment` | Represents review recovery; human alignment remains unused pending human-effort data. |
| Completion boundary | `completion_guard_hook` | Tests whether challenging unsupported completion claims triggers bounded repair. |

Core recovery factors received deliberately near-equal placeholder weights of
**0.10**. More granular optional factors use similarly provisional values:
`qa_visual`, `qa_a11y`, `github_mcp`, `figma_mcp`, `qa_token_drift`, and
`qa_design_fidelity` use 0.08; `qa_size_budget` uses 0.06; and changeset/security
gates use 0.05.

These values were not inferred from Modus. Near-equal placeholders prevent the
initial model from pretending that one control is more valuable before ablation
data exists. Repository-specific weights remain a Phase D objective.

### Decay factors

The decay factors came from mechanisms expected to increase failure or review
burden:

- Long, failure-heavy context raises `Hc`.
- Large, complex, multi-file diffs raise `O`.
- Changes with many dependents raise `Cb`.
- Vague or internally inconsistent requirements raise `σ`.
- Broad changes combined with vague requirements add the `Cb·σ` interaction.

Every proxy is normalized to `[0,1]` so its scale cannot arbitrarily dominate the
formula. Phase B sensitivity analysis found no inert parameter, so none was
removed. The hybrid structure was retained because it captures both individual
stressors and the specific broad-change/ambiguous-spec interaction.

## 3. Phase A — initial structure (v0)

**Date:** 2026-07-19  
**Evidence type:** derivation, not a feature run

The starting observation was compounding error. If each autonomous step succeeds
with probability `1−ε`, validity after `n` steps is approximately
`e^(−εn)`. Taking a continuous-time limit yields a decay hazard:

```text
dV/dt = −D(t)·V(t)
```

Recovery was then added because CI, QA, repair, and review act on invalid work:

```text
dV/dt = (1−V)·R − V·D
```

No live values were generated in this phase. Its output was the measurable
definition of `V_obs`, normalized decay proxies, the factor registry, and three
candidate decay forms: multiplicative, additive, and hybrid.

**How it was applied:** the structure was made executable in
`theory/formula.py`. All weights were explicitly marked as placeholders, with
functional-form selection and factor valuation deferred to data.

## 4. Phase B — simulation and formula v1/v1.1

**Dates:** 2026-07-19 and 2026-07-27  
**Evidence type:** synthetic simulation

### Main simulation

The piecewise-constant ODE was compared with **540 synthetic trajectories** and
achieved approximately **0.054 RMSE** on `V_obs`. Simulated full-pipeline versus
bare-agent pass@1 was:

| Task stratum | Full pipeline | Bare agent |
| --- | ---: | ---: |
| Low | ≈1.00 | ≈0.93 |
| Medium | ≈1.00 | ≈0.83 |
| High | ≈0.93 | ≈0.23 |

Sobol analysis retained all factors. On high-complexity tasks, commit cadence was
most influential, followed by repair success, spec refinement, CI catch
probability, context multipliers, and QA catch probability. On medium tasks, QA
catch probability and commit cadence led.

The simulation also exposed an identifiability problem: factors that remain
constant or toggle together can exchange fitted weight without materially
changing the fit. Therefore:

1. ON/OFF arm contrasts became the primary estimand.
2. `bare` and single-factor-off arms were required to avoid ceiling effects.
3. QA and Fix must be reported together unless an arm separates them.
4. Joint factor weights became secondary rather than headline results.

### Completion-guard feature

The `completion_guard_hook` was added as a recovery factor with placeholder
weight **0.10**. Its activity is 1 only at the completion-validation boundary.
The simulated mechanism checks for missing acceptance-criteria, test, or QA
evidence and permits one bounded repair attempt.

Across a detection-probability sweep, its largest mean pass@1 gain was about
**+0.092** for the `no_agentic_qa` high-complexity arm. Its effect was near zero
for the full-pipeline medium arm, where outcomes were already saturated.

**How it was applied:** the hook was registered in formula v1.1 and used to
generate campaign hypotheses. It remains simulation-only because there is no
live hook telemetry.

### Synthetic fitting dry run

`data/fit_results.json` contains an 18-record synthetic pipeline validation.
Additive and hybrid fits reached bounds for many factor weights (`10.0`), showing
that these values are not stable empirical constants. They must not be described
as Modus-fitted or factory weights.

## 5. Level 0 application — Modus PR #34 baseline

**Feature:** menu-item end-icon slot support  
**Issue/PR:** issue #30, PR
[#34](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34)  
**Task stratum:** medium  
**Evidence type:** intake pseudo-record

### Factors entered

The scorer mapped `recovery_seen` to registry activities of 1.0:

| Recovery factor | Activity | Placeholder weight | Contribution to R |
| --- | ---: | ---: | ---: |
| `ci_gate` | 1.0 | 0.10 | 0.10 |
| `agentic_qa` | 1.0 | 0.10 | 0.10 |
| `fix_loop` | 0.0 | 0.10 | 0.00 |
| **Total R** | | | **0.20** |

These factors came from observed workflow events: CI and QA ran, but QA failed
and no Fix iteration occurred.

The intake scorer derived or defaulted the decay inputs:

| Decay factor | Value | How selected |
| --- | ---: | --- |
| `Hc` | 0.8 | Entropy notes contained failure/debug evidence. |
| `O` | ≈0.91 | Soft-saturated opacity from 594 changed lines and 16 files. |
| `Cb` | 0.7 | Intake notes described a shared component. |
| `σ` | 0.3 | Acceptance criteria existed and were not marked vague; default used. |

Substitution into the hybrid decay formula gives approximately:

```text
D = 0.01 + 0.05(0.8) + 0.05(0.91) + 0.05(0.7)
  + 0.05(0.3) + 0.05(0.7)(0.3)
  ≈ 0.1562

V* = 0.20 / (0.20 + 0.1562) ≈ 0.5615
```

### How the result was applied

PR #34 opened without a Dev preflight or stop-boundary. QA failed and
`fix_iterations=0`, so diagnosis identified the **loop** as the weakest layer.
The PR was retained as the pre-intervention baseline rather than repaired,
preserving the before/after contrast.

At **0.5615**, its directional V* was below the provisional simulation threshold
of 0.65. The threshold was used to retain deep human review, not to automate a
merge decision.

## 6. Intervention phase between PRs

The following controls were introduced:

1. A Dev PRE-OPEN PR GATE with required commands and an explicit stop-boundary.
2. Fix parsing for both `## QA FAILED` and `## QA REPORT`.
3. QA GitHub connectivity and `qa-full`/`qa-rerun` triggers.
4. A Fix handoff that removes and re-adds `qa-rerun` because Cursor wakes on a
   new label-added event.
5. A completion-guard hook template, still classified as simulation-only.

Not every installed control was counted directly in R. The score used only
recovery factors actually recorded in `recovery_seen`. In particular,
`completion_guard_hook` was not counted in PR #42.

## 7. Level 0 application — Modus PR #42 retest

**Feature:** update checkbox and switch internal value on input change  
**Issue/PR:** issue #28, PR
[#42](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42)  
**Task stratum:** medium  
**Evidence type:** intake pseudo-record

### Factors entered

| Recovery factor | Activity | Placeholder weight | Contribution to R |
| --- | ---: | ---: | ---: |
| `ci_gate` | 1.0 | 0.10 | 0.10 |
| `agentic_qa` | 1.0 | 0.10 | 0.10 |
| `fix_loop` | 1.0 | 0.10 | 0.10 |
| **Total R** | | | **0.30** |

The additional 0.10 came from observed Fix-loop activity: QA failed once, Fix
made one repair, and QA subsequently passed.

| Decay factor | Value | How selected |
| --- | ---: | --- |
| `Hc` | 0.5 | Entropy notes existed but did not match the debug/fail keywords. |
| `O` | ≈0.87 | Soft-saturated opacity from 212 changed lines and 16 files. |
| `Cb` | 0.2 | No “shared” blast-radius marker; default used. |
| `σ` | 0.3 | Acceptance criteria existed and were not marked vague; default used. |

Substitution gives:

```text
D = 0.01 + 0.05(0.5) + 0.05(0.87) + 0.05(0.2)
  + 0.05(0.3) + 0.05(0.2)(0.3)
  ≈ 0.1066

V* = 0.30 / (0.30 + 0.1066) ≈ 0.7377
```

The lower D was primarily associated with lower opacity and blast-radius inputs.
The Fix loop affected R, not D.

### How the result was applied

PR #42 showed the intended sequence:

```text
Dev stop-boundary → QA FAILED → Fix ×1 → QA PASSED
```

The directional V* moved above 0.65. This supported the conclusion that the loop
intervention worked for this retest. It did not justify reduced review globally:
the policy remained high-level review for low-risk work and deep review for
medium/high work until another successful medium run or a fully automatic repair
handoff was observed.

One operational weakness remained: QA round two required a manual
remove-and-re-add of `qa-rerun`, because the label was already present and GitHub
did not emit another label-added event.

## 8. Delta analysis was not formula output

The separate delta pack reported intake heuristics such as `Hc: 0.0→0.4` and
`Cb: 0.0→0.35`. Those values reflected a different before/after intake heuristic,
including the Fix expansion of PR #42 from 5 to 16 files.

They were diagnostic hints, not the R, D, or V* calculation and must not be mixed
with the score-pack values above.

## 9. Later official-repository automation phases

Later work on `trimble-oss/modus-wc-2.0` included PR #1407, the Dev+QA split,
`/refine` routing, label-added handoffs, and remove/re-add label pulsing.

These changes improved the same delivery loop, but no new score pack in this
research repository records them. Therefore, this report does not invent R, D,
or V* values for those phases. They become another formula application only
after their PR evidence is added to intake or live collectors and the CLI scorer
is run.

## 10. Phases not yet applied with real fitted values

| Phase or level | Current status | Formula values available |
| --- | --- | --- |
| Level 1 Instrument | Automations and collectors exist, but `metrics.jsonl` has 0 live runs. | No live `V_obs(t)` trajectories. |
| Phase C campaign | Exit criterion of at least 6 terminal non-synthetic runs not met. | None. |
| Level 2 / Phase D calibration | Blocked on real campaign data and outcome variation. | No repository-fitted weights. |
| Phase E second-repository validation | Protocol/checklist exists but has not run. | No transfer result or re-fitted constants. |
| Human review economics | Deferred pending human `O_A` and Likert evidence. | No human-alignment weight or throughput claim. |

## 11. What can and cannot be concluded

### Supported

- The recovery-versus-decay ODE reproduced the synthetic micro-process with
  approximately 0.054 RMSE.
- Simulation showed recovery controls matter more as task pressure rises.
- The Modus intake scorer directionally moved R from 0.20 to 0.30, D from
  0.1562 to 0.1066, and V* from 0.5615 to 0.7377.
- The observed pilot workflow changed from QA failure with no repair to one
  repair followed by QA PASS.
- The loop diagnosis yielded concrete controls that were exercised on the
  retest.

### Not supported

- The placeholder weights are not Modus-fitted factory weights.
- Two intake pseudo-records do not establish sustained recovery.
- The completion-guard effect is not live evidence.
- The synthetic fitted coefficients cannot be transferred to Modus.
- No merge-throughput gain or safe autonomous merge policy has been measured.
- Human review is never removed by this framework.

## 12. Source artifacts

- `theory/derivation.md` — derivation and assumptions.
- `theory/formula.py` — executable formula, proxies, registry, and placeholders.
- `theory/formula-changelog.md` — phase-by-phase formula revisions.
- `sim/FINDINGS.md` — simulation, Sobol, identifiability, and hook results.
- `framework/score.py` — intake-to-factor mapping and score computation.
- `data/validity-report.json` — machine-readable Modus pilot results.
- `paper/modus-pilot-abstract-summary.md` — PR timelines and score-pack values.
- `data/fit_results.json` — synthetic fitting validation only.

