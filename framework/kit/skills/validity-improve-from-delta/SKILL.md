---
name: validity-improve-from-delta
description: >-
  When setup validity falls between rounds, map evidence to generic top-level
  formula metrics (not stack-specific), explain them, and propose one
  playbook-backed intervention. Use after a good rating followed by a failed
  run, or with framework delta output.
---

# Validity Improve-from-Delta

## User question

> We rated the setup; it looked good. Another round failed and the value
> dropped. What should we change?

## Metric rule (critical)

Use **only** top-level metrics from `framework/catalog/metric-playbooks.json`:
`V_obs`, `V_star`, `Hc`, `O`, `Cb`, `sigma_spec`, `R_recovery`, `pass_at_1`.

- Frontend / backend / data / infra details are **evidence**, not new metrics.
- Your job is to **map** “what happened” → nearest metric and cite the snippet.
- Follow `ai_mapping_rule` in the playbooks file.

## Steps

1. Build delta facts:
   ```bash
   python -m framework delta --before <prior.json> --after <failed.json> --out data/delta-pack.json
   ```
2. Read the delta pack + `metric-playbooks.json`. Follow `improve_instructions`.
3. Tell the human:
   - Evidence → metric mappings
   - Which metrics worsened
   - Plain-language meaning for this workflow
   - **One** control_class / intervention (raise R or lower D) + retest
   - Review depth until recovered
4. Write `data/improvement-plan.json` with `dominant_metric`, `evidence_snippet`,
   `control_class`, `intervention_id` (if any), `retest`.
5. Human approval → **validity-improve** applies one change → delta again.

## Hard rules

- No stack-specific metric invention.
- One change per round.
- Human review never removed.
- `intake_heuristic_scores` in delta packs are **hints only** — you own the authoritative metric call; cite evidence.
- When citing R, D, or V*, quote `python -m framework score` output; never invent formula equilibria.
- Human gate is on **apply**, not on every metric judgment.
