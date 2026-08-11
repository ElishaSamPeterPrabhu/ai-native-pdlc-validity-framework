---
name: validity-setup
description: >-
  Inspect a repository's AI delivery setup, create a setup-manifest, identify
  measurement gaps, and propose collectors/rules/hooks/workflows for the
  AI-Native PDLC Validity Framework. Use when adopting validity measurement,
  instrumenting harness/loop/graph controls, or running Level 0 Observe.
---

# Validity Setup (Level 0 Observe → prepare Level 1)

## Goal

Help a team validate whether their AI issue→PR setup produces trustworthy
evidence, and show exactly how each measured value is obtained from what they
already have. Generate proposed implementation artifacts, but **require human
approval before installing** any rules, hooks, workflows, or collectors.

## Steps

1. **Layout first (required).** Do not assume `framework/`, `harness/`, or `data/`
   exist. Ensure the repo has a path contract:
   ```bash
   python -m framework init --repo .
   ```
   Open `validity.layout.json` with the human and correct any wrong folders
   (rules, hooks, MCP, workflows, metrics). Re-run init `--force` only after edits
   if you need the always-apply rule refreshed:
   `.cursor/rules/validity-layout.mdc`.

2. Inspect using that layout:
   ```bash
   python -m framework inspect --repo .
   ```
   Output path comes from `setup_manifest_path` in the layout file.

3. Read the setup-manifest and summarize:
   - layout source + paths used
   - harness / loop / graph presence
   - available vs missing evidence adapters
   - measurement gaps

4. For every gap, explain:
   - construct (what it means)
   - telemetry source from what they have
   - path from `validity.layout.json` (or unset)
   - normalization / missing behavior
   - which layer owns the fix

5. Propose artifacts using **layout paths**, not research-repo defaults:
   - rules → `rules_dir`
   - hooks → `hooks_path`
   - workflows → `workflows_dir`
   - templates live under this package's `framework/templates/` when the package
     is available; otherwise copy from the research preview

6. Build an evidence pack for AI diagnosis (do not script the diagnosis):
   ```bash
   python -m framework evidence --repo .
   ```
   Then run / hand off to **validity-diagnose** for harness/loop/graph reasoning.
7. **Stop and ask for approval** before writing files into the target repo.
8. After approval, write only the approved files (or hand to **validity-improve**),
   then re-run `inspect` + `evidence`.

## Hard rules

- AI diagnoses; CLI gathers facts and applies approved writes; automations run delivery.
- Never invent folders because the research repo has them.
- Do not claim Modus factory weights or precise per-PR validity scores.
- Mark `completion_guard_hook` as simulation-only until live telemetry exists.
- Human review is never removed; only review depth may be recommended later.
- Prefer existing CI/diff/events over inventing new infrastructure.

## References

- `validity.layout.json` (repo root) and `.cursor/rules/validity-layout.mdc`
- `framework/CONTRACT.md`
- `framework/MEASUREMENT.md`
- `framework/schemas/setup-manifest.schema.json`
- `research/adoption-guide.md`
