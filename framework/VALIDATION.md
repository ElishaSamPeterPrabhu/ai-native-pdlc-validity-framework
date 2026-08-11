# Validation plan (live Modus + second repository)

## Status gate

| Gate | Requirement | Current |
| --- | --- | --- |
| Local structure | formula v1.1, schemas, CLI, contract checks | runnable via `python -m framework validate` |
| Pilot | 6 terminal non-synthetic runs, V_obs variation, stages | see `harness/PILOT-STATUS.md` (console unblock) |
| Campaign | arm contrasts primary; CI; null effects reported | pending pilot |
| Phase E | `analysis/GENERICITY-PROTOCOL.md` | not run |
| Review economics | human O_A / Likert | deferred (iPad phase) |

## Success criteria (pre-registered)

Copied to `data/validation/SUCCESS_CRITERIA.json` by the local validator.

1. **Calibration error:** hybrid (or AIC-selected) form RMSE on held-out trajectories beats constant-mean baseline when outcome variance is material.
2. **Repeatability:** pass^k reported with binomial/bootstrap CIs; k≥3 on differing arms.
3. **Factor-effect recovery:** ON/OFF arm signs match mechanism hypotheses; QA+fix combined unless separated.
4. **Diagnosis usefulness:** recommended layer matches injected ablation in at least the high-variance arms.
5. **Review effort / false-safe:** deep lane catches high-risk failures; minimal lane never skips human review.
6. **Merge throughput:** measured only after review-depth policy is live; do not claim from simulation.

## Local command

```bash
python -m framework validate --out data/validation
```

This compares equilibrium / CI-only / static-risk / constant-mean predictors on
available metrics and records claim warnings. Synthetic metrics validate the
pipeline only.

## Unblock Modus pilot

1. Retarget Cursor automations to the experiment fork (`harness/RETARGET-RUNBOOK.md`).
2. Grant GitHub app access; set spend limit.
3. Run the 3×2 baseline pilot commands in `harness/PILOT-STATUS.md`.
4. Delete synthetic `data/metrics.jsonl` before collecting real records.
5. Only then run `python -m framework calibrate`.

## Second repository

Follow `analysis/GENERICITY-PROTOCOL.md`. Compare:

- transferred Modus calibration (directional only)
- local Level-2 fit
- CI-only and static-risk baselines

Pass = structure transfer (decay form + arm contrast order), not constant transfer.
