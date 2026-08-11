# Phase E checklist (second repository)

Protocol: `analysis/GENERICITY-PROTOCOL.md`

## Pre-run

- [ ] Choose non-frontend repo with a test suite
- [ ] Map core factors to local toggles (mark N/A explicitly)
- [ ] Port 4–6 tasks (2 per stratum) with hand-written verifiers
- [ ] Freeze success criteria from `framework/VALIDATION.md` / `SUCCESS_CRITERIA.json`

## Arms (k=3)

- [ ] `baseline`
- [ ] `bare`
- [ ] `no_recovery_loop`

## Analysis

- [ ] Fit with `analysis/fit.py` on second-repo data alone
- [ ] Compare AIC/BIC decay form to Modus campaign selection
- [ ] Compare arm-contrast sign/order (not magnitudes)
- [ ] Run baselines: CI-only, static-risk, transferred Modus placeholders

## Claims allowed only if pass criteria met

- Structure transfer (ODE + registry + proxy normalization)
- Re-fitted constants side-by-side

## Claims forbidden

- Constant transfer from Modus
- Review-economics calibration without human O_A data
