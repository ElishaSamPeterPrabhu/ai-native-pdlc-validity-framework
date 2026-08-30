---
name: validity-diagnose
description: >-
  AI diagnosis layer for the Validity Framework. Reads a CLI evidence pack,
  reasons about harness/loop/graph weaknesses, and proposes review policy and
  interventions. Use when diagnosing setup trust, after inspect/evidence, or
  before validity-improve applies fixes.
---

# Validity Diagnose (AI reasoning layer)

## Role split

| Actor | Owns |
| --- | --- |
| **You (AI)** | Metric judgments, layer diagnosis, intervention choice, review-policy judgment |
| **CLI** | `init` / `inspect` / `evidence` / `score` / `collect` / `calibrate` / `report` — facts and formula R/D/V* |
| **Automations** | Dev / QA / Fix execution on the delivery path |
| **Human** | Approves **apply** (rules, hooks, workflows, collectors); optional on metric judgment |

Do **not** treat `python -m framework diagnose --heuristic` or
`layer_diagnosis.optional_heuristic` as the answer. Those are smoke-test hints.

## Steps

1. Ensure layout exists:
   ```bash
   python -m framework init --repo .
   ```
2. Refresh facts (pick one):
   - Offline git only:
     ```bash
     python -m framework inspect --repo .
     python -m framework evidence --repo . --out data/evidence-pack.json
     ```
   - Online automations / remote team (console not API-readable):
     use **validity-intake** or
     ```bash
     python -m framework intake --repo . --intake data/user-intake.json
     ```
   Add `--include-synthetic` only for demos.
3. Read `data/evidence-pack.json` (or layout data dir). Follow
   `diagnosis_instructions` inside the pack.
   Before judging any factor weak or strong, check the score pack's per-field
   provenance (`decay_proxies.*.source`, `defaulted_inputs`,
   `activities_assumed`/`recovery_assumed`) and the registry's
   `missing_behavior` for that factor. A defaulted input is a **measurement
   gap**, not evidence of weakness; list it under `open_questions` instead of
   citing it as a finding.
4. Write a diagnosis artifact (propose path `data/diagnosis.json` or under
   layout `data_dir`) with:
   ```json
   {
     "weakest_layer": "harness|loop|graph|unknown",
     "confidence": "high|medium|low",
     "rationale": ["cite pack fields…"],
     "recommended_controls": ["…"],
     "review_policy_suggestion": {
       "low": "deep|high-level|minimal",
       "medium": "…",
       "high": "…"
     },
     "next_cli_or_automation_actions": ["…"],
     "open_questions": ["…"]
   }
   ```
5. Present the diagnosis to the human in plain language.
6. Hand off to **validity-improve** only after the human accepts the diagnosis.
   Improve applies approved fixes via layout paths / CLI / automations — it does
   not re-diagnose from scratch unless new evidence arrives.

## Reasoning checklist

- Which measurement gaps block a confident call?
- Does validity collapse on medium/high strata while low stays fine? → loop pressure
- Are rules/MCP/hooks missing per layout paths? → harness
- Are handoffs / spec readiness / review routing weak? → graph
- Is the right next step instrumentation (Level 1) rather than a new control?

## Hard rules

- Never invent telemetry absent from the evidence pack.
- Never invent factor activity or decay proxy values; if required inputs are
  missing, say the framework does not have the necessary data and name the gap.
- Disclose per-field provenance (observed / heuristic / imputed / missing)
  before presenting any score-derived finding.
- **Quote** R, D, V* from `python -m framework score` when citing formula numbers; never invent equilibria or fitted weights.
- **You own** metric assessments (evidence → metric, dominant metric, direction) in diagnosis.json.
- Human review is never removed.
- `completion_guard_hook` stays simulation-only until live telemetry exists.
- Prefer one intervention per retest cycle after approval.
