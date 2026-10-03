---
name: workflow-measure-handoff
description: >-
  Wire a newly built (or existing) AI delivery workflow into measurement: register
  it with the Timeline Monitor, run validity-setup / intake / score, and route to
  validity-diagnose and validity-improve. Use right after automations are set up
  or when a team wants to know whether their workflow deserves trust.
---

# Workflow measure handoff

## Steps

1. **Register for monitoring.** Add the repo and its signal map to
   `dashboard/monitor/monitor.config.json` (ask first). Use the stage names from
   `workflow-design.json`. If the monitor is not installed, record this as a gap.
2. **Observe (Level 0).** Follow `validity-setup`:
   `python -m framework init --repo .` then `python -m framework inspect --repo .`.
3. **Collect evidence.** After the first real runs (aim for 3+ issue→PR loops):
   - Offline: `python -m framework evidence --repo .`
   - Console automations not readable by API: follow `validity-intake` and run
     `python -m framework intake --repo . --intake <path>`.
4. **Score.** Follow `validity-score`: `python -m framework score --repo . --input <path>`.
   Present the pack exactly as `factor-provenance.mdc` requires (provenance first,
   `weight_source`, `record_kind`, gaps). Never estimate a missing number.
5. **Diagnose and improve.** Hand the evidence pack to `validity-diagnose`, then
   apply accepted fixes with `validity-improve`. When a good round is followed by a
   failed one, use `validity-improve-from-delta` with `python -m framework delta`.
6. **Close the loop.** Interventions that change stages or signals go back through
   `workflow-design` so the monitor config stays in sync.
