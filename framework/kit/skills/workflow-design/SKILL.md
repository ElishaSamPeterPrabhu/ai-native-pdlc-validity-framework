---
name: workflow-design
description: >-
  Turn repo-profile.json and process-map.json into a target AI delivery workflow:
  stages, triggers, agents, gates, human checkpoints, and a signal contract, each
  control mapped to harness, loop, or graph. Produces workflow-design.json. Use
  before generating Cursor Automations or other automation configs.
---

# Workflow design

## Inputs

`repo-profile.json`, `process-map.json`, `starter-kit/profiles/<generic|frontend>.json`,
`starter-kit/signal-contract.md`.

## Steps

1. **Pick the profile.** `frontend` if the repo ships UI (components, stories,
   styles); else `generic`. Load the profile JSON as the baseline.
2. **Lay out stages.** Start from the baseline flow and remove or add stages to
   match the process map:
   - Product→Issue: intake → review → approve → issue created.
   - Issue→PR: `/approve` → Dev → PR opened → routing → QA → Fix (cap 3) → re-QA →
     human review → merge.
3. **For each stage define:** trigger (event + who may fire it), agent or job,
   gate commands (from `repo-profile.commands`), exit signal (exact header or
   label from the signal contract), human checkpoint.
4. **Map controls to layers** so measurement can see them:
   - **Harness** — what constrains a single run (rules, sandbox, gate commands,
     design-source resolution, risk-area denylist).
   - **Loop** — how failure becomes repair (QA verdict → Fix → re-QA, iteration cap,
     clarification).
   - **Graph** — how impact is scoped (component/module graph, reverse dependencies,
     coverage targets).
5. **Scale review to risk.** Low-risk (docs/styles) may use `qa-skip` with
   verification; risk areas from the process map always get `needs-human`.
6. **Write `workflow-design.json`** under `data_dir` after approval:

```json
{
  "profile": "frontend",
  "stages": [
    {"id": "dev", "flow": "issue_to_pr", "trigger": "issue_comment /approve by Me",
     "agent": "Dev", "gate": ["npm test", "npm run lint"],
     "exit_signals": ["Routing: qa-full", "Routing: qa-skip"],
     "human_checkpoint": "", "layer": "harness"},
    {"id": "intake", "flow": "product_to_issue", "trigger": "schedule: new meeting notes",
     "agent": "meeting-review-intake", "gate": [], "exit_signals": ["needs-review"],
     "human_checkpoint": "row review in the ledger", "layer": "harness"}
  ],
  "signals": "starter-kit/signal-contract.md",
  "risk_policy": {"needs_human_paths": []},
  "measurement": {"monitor_repo": "owner/name"}
}
```

   Shape rules (validated by `framework/schemas/workflow-design.schema.json`):
   - Every stage has `id`, `flow` (`product_to_issue` or `issue_to_pr`), and
     `exit_signals` (array of exact contract strings).
   - `trigger`, `human_checkpoint` are plain strings; `agent` is a string or null.
   - `signals` is the **path** to the signal contract, not an inline copy. Put
     per-stage signals in `exit_signals`.

7. Show the design as a short mermaid flowchart plus a stage table, get approval,
   then hand off to `workflow-setup-cursor` or `workflow-setup-other`.
