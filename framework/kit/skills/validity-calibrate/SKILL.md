---
name: validity-calibrate
description: >-
  Select representative tasks and ablation arms, prepare Level 2 calibration
  for the AI-Native PDLC Validity Framework, and run fitting only when real
  non-synthetic metrics meet pilot exit criteria.
---

# Validity Calibrate (Level 2)

## Goal

Turn instrumented run records into a repository-specific setup-validity profile
by task class (low/medium/high), with arm contrasts as the primary estimand.

## Steps

1. Read `validity.layout.json` (run `python -m framework init --repo .` if missing).
   Use `tasks_dir`, `metrics_path`, `harness_dir`, and `analysis_dir` from that file.
2. Confirm pilot exit criteria (see layout `harness_dir`/PILOT-STATUS when present):
   - ≥6 terminal non-synthetic runs
   - `V_obs` not saturated at 1.0 for all runs
   - stage transitions present
3. Select 5–10 tasks across strata using the task schema under `tasks_dir`.
4. Prefer variance-first arms: `bare`, `no_recovery_loop`, then context ablations.
5. Keep QA + repair combined unless a separating arm is explicitly run.
6. Collect metrics into layout `metrics_path` (delete synthetic first).
7. Run (paths resolved from layout):
   ```bash
   python -m framework calibrate --repo .
   python -m framework report --repo .
   ```
   Do **not** use `--include-synthetic` for claimable reports.
8. Interpret arm contrasts and AIC/BIC decay-form selection; quote fitted weights from fit output only.

## Hard rules

- Refuse calibration claims on synthetic-only `data/fit_results.json`.
- Never recommend `--include-synthetic` for claimable reports.
- Report null/negative effects with confidence intervals.
- Structure transfers; constants do not — see `analysis/GENERICITY-PROTOCOL.md`.
