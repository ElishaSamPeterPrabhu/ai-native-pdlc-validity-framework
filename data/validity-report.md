# Modus Validity Pilot Report

**Repo:** [ElishaSamPeterPrabhu/modus-wc-2.0](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0)  
**Pilot branch:** `framework-test`  
**Generated:** 2026-08-10  
**Evidence:** intake pseudo-scores (`weight_source=placeholder`) — not live harness telemetry

## Decision

| Question | Answer |
|----------|--------|
| Repair PR #34? | **No** — keep as pre-intervention baseline |
| Enough for a pilot report? | **Yes** — baseline + closed retest |
| Ready to calibrate? | **No** — need ≥6 real `metrics.jsonl` runs |

## Verdict

Interventions on the Dev/QA/Fix loop **worked** for one medium retest.

- **Before (PR [#34](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34)):** Dev opened without pre-flight → QA FAILED (missing npm scripts) → no Fix → loop broken  
- **After (PR [#42](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42)):** Dev stop-boundary yes → QA FAILED (lint) → Fix ×1 → QA PASSED → **loop closed**

## Scores (`python -m framework score`)

| Round | R | D | V* |
|-------|---|---|-----|
| PR #34 baseline | 0.20 | 0.1562 | 0.5615 |
| PR #42 retest | **0.30** | **0.1066** | **0.7377** |
| Aggregate | — | — | **0.6496** |

ΔR = +0.10 · ΔD = −0.05 · ΔV* = +0.18 (placeholder weights)

## What was applied

1. Dev Agent PRE-OPEN PR GATE (stop-boundary + STEP 1 checks in PR body)
2. Fix Agent accepts `## QA FAILED` / `## QA REPORT`
3. Fix Agent: remove-then-add `qa-rerun` (label-added trigger)
4. QA Agent GitHub connected; `qa-full` + `qa-rerun` triggers; PR opened by Anyone
5. `completion_guard_hook` installed (simulation-only)

## Proven vs not proven

**Proven**

- Dev stop-boundary observable on PR open  
- QA can fail and later pass  
- Fix Agent repairs and re-enters QA (1 iteration on #42)  
- Placeholder R/V* move in the expected direction  

**Not proven (do not claim)**

- Automatic Fix→QA handoff without manual `qa-rerun` toggle  
- Sustained recovery (second consecutive medium pass)  
- Fitted weights / Level 2 calibrate  
- Live hook telemetry  

## Review policy (until recovered)

| Stratum | Lane |
|---------|------|
| low | high-level |
| medium | deep |
| high | deep |

Human review is never removed.

## Continue with

1. Optional: second medium `qa-full` issue to prove automatic `qa-rerun` handoff  
2. Leave PR #34 open/unmerged as baseline (or close as abandoned baseline — do not Fix-repair it for the pilot)  
3. Skip `calibrate` until real metrics exist  

Machine-readable twin: `data/validity-report.json`
