---
name: validity-improve
description: >-
  Apply human-approved Validity Framework interventions using layout paths,
  CLI, rules, hooks, and automations. Use after validity-diagnose has produced
  an accepted diagnosis — this skill executes fixes, it does not re-reason the
  layer diagnosis from scratch.
---

# Validity Improve (apply approved fixes)

## Role

You **execute** an accepted diagnosis. You do not replace `validity-diagnose`.

1. Read `data/diagnosis.json` (or the diagnosis the human just accepted).
2. If missing, run **validity-diagnose** first — do not invent a weakest layer
   from `diagnose --heuristic`.

## Steps

1. Confirm `validity.layout.json` paths for writes (`rules_dir`, `hooks_path`,
   `workflows_dir`).
2. Map `recommended_controls` to `framework/catalog/interventions.json` (or
   layout `framework_dir`/catalog).
3. For each approved control, show the recipe targeting **layout paths**, then
   **stop for human approval** before writing.
4. After approval, apply via:
   - file writes (rules/hooks/workflows at layout paths)
   - CLI helpers (`inspect`, `collect`, `calibrate`, `report`, `evidence`)
   - automations (Dev/QA/Fix) when the control is an automation toggle
5. Remeasure:
   ```bash
   python -m framework inspect --repo .
   python -m framework evidence --repo .
   ```
   Then ask **validity-diagnose** to update the diagnosis from new evidence.

## Hard rules

- No silent diagnosis from scripts.
- One control change per retest cycle when possible.
- Simulation-only controls stay labeled as such.
- Human review is never removed.
