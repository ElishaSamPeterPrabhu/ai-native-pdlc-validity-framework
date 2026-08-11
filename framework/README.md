# AI-Native PDLC Validity Framework

**Research preview `0.1.0`** — formula `v1.1`, evidence status `simulation-calibrated`.

Measure whether an AI delivery setup (issue → implement → QA → repair → human PR
review) is trustworthy by task difficulty, diagnose weak **harness / loop / graph**
controls, and scale human review depth without removing human review.

Install:

```bash
pip install pdlc-validity
```

Repository: https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework

## Quick start

```bash
# 0) Path contract for THIS repo (required before inspect on foreign trees)
pdlc-validity init --repo .
# or: python -m framework init --repo .
# edit validity.layout.json if folders differ, keep .cursor/rules/validity-layout.mdc in sync

# Level 0 Observe (paths come from validity.layout.json)
python -m framework inspect --repo .

# Evidence pack for AI diagnosis (facts only — no scripted layer verdict)
python -m framework evidence --repo . --include-synthetic

# Online automations (console not API-listable): user intake + PR evidence
# cp framework/templates/intake/user-intake.example.json data/user-intake.json
python -m framework intake --repo . --intake data/user-intake.json

# Then: Cursor skill validity-diagnose → human approval → validity-improve
# Teach PR template: framework/templates/intake/pr-body-formula.md
# Guide: framework/ONLINE-REVIEW.md

# Score dropped vs a prior good round? (facts → AI explains metrics → one fix)
python -m framework delta \
  --before framework/templates/intake/round-good.example.json \
  --after framework/templates/intake/round-failed.example.json
# CLI-owned R/D/V* (placeholder weights; not repo-fitted)
python -m framework score --input data/user-intake.json
# then Cursor skill: validity-improve-from-delta
# Playbooks: framework/catalog/metric-playbooks.json | Guide: framework/IMPROVE-LOOP.md

# Setup-validity profile aggregates (use --include-synthetic only for demos)
python -m framework report --repo . --include-synthetic

# Local validation vs simpler baselines
python -m framework validate --repo . --out data/validation
```

**AI diagnoses metric calls; CLI owns formula numbers.** Do not treat
`diagnose --heuristic` or `intake_heuristic_scores` as formula R/D/V*.
Quote `python -m framework score` for equilibria.

Adopter repos rarely match this research tree. The always-apply rule
`.cursor/rules/validity-layout.mdc` tells agents to read `validity.layout.json`
instead of inventing `harness/` / `data/` / `framework/` paths.

## What you get

| Artifact | Purpose |
| --- | --- |
| `CONTRACT.md` | Units of analysis, adoption levels, claim boundaries |
| `schemas/` | setup-manifest, run-record, factor-registry, validity-report, delta-pack, evidence-pack, score-pack |
| `adapters/` | repo inspect + diff/opacity helpers |
| `catalog/interventions.json` | how to implement and retest each control |
| `templates/` | rules, hooks, CI workflow starters |
| CLI (`python -m framework …`) | init, inspect, evidence, intake, delta, score, collect, calibrate, diagnose, report, validate |

## Cursor skills

Project skills under `.cursor/skills/`:

- `validity-setup` — layout + inspect + evidence (approval required for writes)
- `validity-intake` — online automations + PR paste when console is not API-readable
- `validity-diagnose` — **AI reasoning**: harness/loop/graph + review policy
- `validity-improve` — apply human-approved fixes via CLI/paths/automations
- `validity-improve-from-delta` — score dropped: explain metrics + one playbook fix
- `validity-calibrate` — Level 2 task/arm selection and fitting gates

## Evidence discipline

- `data/fit_results.json` is **SYNTHETIC** until the live campaign lands.
- `completion_guard_hook` is **simulation-only** until live hook telemetry exists.
- Do not publish precise every-PR scores from placeholder weights.
- Primary scientific estimand after the campaign: **arm contrasts**, then ODE fits.

## Reference implementation

Modus Web Components automations + harness in this repo:

- `harness/AUTOMATION-PROMPTS.md`
- `harness/RETARGET-RUNBOOK.md`
- `harness/PILOT-STATUS.md`
