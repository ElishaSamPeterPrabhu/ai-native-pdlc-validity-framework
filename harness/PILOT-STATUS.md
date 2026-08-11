# Pilot status (2026-08-11)

**Console Automations pilot:** documented in
`paper/modus-pilot-abstract-summary.md` (#34 → interventions → #42 closed QA
pass; placeholder V\*). Submission abstracts synced to that report.
**Harness 6-run calibrate** (below) remains deferred for this submission pass.

## Validated end-to-end locally (no agent spend)

- Driver mechanics against the live fork: issue creation with labels, timeline
  snapshot (with lag-retry fix), state polling, cleanup — exercised on issue #24.
- Per-commit verifier grading on real commits: `low-alert-blend` verifier scores
  **1.0 on experiment-base** (fix present) and **0.0 on `87b26a41b~1`** (pre-fix)
  — the discrimination V_obs(t) requires.
- Verifier suite grades cleanly inside the repo's Stencil/Jest setup after the
  CSS-codegen steps (`tailwind:build`, `embed:css`, `embed:component-css`), which
  the collector runs automatically.
- Dashboard renders live from `data/metrics.jsonl` (currently synthetic records,
  each marked `"synthetic": true`).

## Blocked on console steps (requires your Cursor login; see RETARGET-RUNBOOK.md)

1. Point the five automations' triggers at `ElishaSamPeterPrabhu/modus-wc-2.0`
   (base branch `experiment-base`) and fix the failing `github` MCP tool.
2. Grant the Cursor GitHub app access to the fork.
3. Set the cloud-agent spend limit.

## Then: the actual pilot (3 tasks x baseline arm x k=2 ≈ 6 runs)

```bash
python harness/driver.py --arm baseline --task low-card-hover --repeats 2
python harness/driver.py --arm baseline --task low-alert-blend --repeats 2
python harness/driver.py --arm baseline --task med-badge-align --repeats 2
python harness/collectors.py data/runs/baseline__*      # grade + telemetry
rm data/metrics.jsonl.synthetic 2>/dev/null; # synthetic records: delete data/metrics.jsonl first
python analysis/fit.py                                   # fitting pipeline
python -m framework calibrate --metrics data/metrics.jsonl
python -m framework report --metrics data/metrics.jsonl --out data/validity-report.json
```

Local research-preview validation (no agent spend):

```bash
python -m framework validate --out data/validation
```

Pilot exit criteria (before the ~90–150-run campaign):
- All 6 runs reach a terminal state without manual repair.
- Collected checkpoints show V_obs variation (not all 1.0 — else re-check task
  difficulty or verifier strictness).
- Stage transitions present in every record (approved -> dev -> PR -> QA verdict).
- Non-synthetic metrics only; `data/fit_results.json` remains SYNTHETIC until then.

## Campaign plan (after pilot)

Arms x tasks x k (order: variance first, per Phase-B ceiling-effect finding):
1. `bare`, `no_recovery_loop` — where outcome variance lives
2. `no_mcp`, `no_rules` — the context-value experiments
3. `no_spec_refinement`, `no_ci_gate`, `no_checkpointing`, `fix_cap_1`
4. `with_review_bot` (after Bugbot is enabled on the fork)

9 tasks x k=3 x (1 baseline + 8 ablations) = 243 max; prune to ~120 by running
ablations on the medium+high strata only (6 tasks) after baseline covers all 9.
