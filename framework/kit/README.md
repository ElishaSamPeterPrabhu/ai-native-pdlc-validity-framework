# Starter kit

Copy into your repo to build an AI delivery workflow that can be monitored and
measured.

```bash
cp -r starter-kit/cursor/rules/*  <your-repo>/.cursor/rules/
cp -r starter-kit/cursor/skills/* <your-repo>/.cursor/skills/
```

Then ask Cursor: "use workflow-builder". It reads your repo, interviews you, designs
the workflow, fills `automations/` templates, and hands off to measurement.

| Path | What |
| --- | --- |
| `cursor/rules/` | `workflow-generic.mdc`, `workflow-frontend.mdc` |
| `cursor/skills/` | `workflow-*` builder skills |
| `automations/` | Dev, QA, Fix, `/ask`+`/refine`, product intake templates |
| `workflows/label-router.yml` | GitHub Action that turns exact comment lines into labels |
| `signal-contract.md` | Labels, headers, commands, stages |
| `profiles/` | `generic.json`, `frontend.json` (Modus as worked example) |

## Placeholders

`workflow-setup-cursor` / `workflow-setup-other` fill these from `repo-profile.json`,
`process-map.json`, and `workflow-design.json`. An unfilled `{{…}}` is a setup bug.

| Placeholder | Filled with | Used in |
| --- | --- | --- |
| `{{REPO}}` | `owner/name` | automations, label router |
| `{{DEFAULT_BRANCH}}` | base branch for PRs | dev |
| `{{GATE_COMMANDS}}` | build/test/lint commands, in order | dev, qa, fix |
| `{{TEST_COMMAND}}`, `{{LINT_COMMAND}}`, `{{BUILD_COMMAND}}` | single commands | profiles |
| `{{QA_SKIP_PATTERNS}}` | file patterns that may route `qa-skip` | dev, qa |
| `{{RISK_PATHS}}` | paths that force a draft PR + human review | dev |
| `{{DESIGN_SOURCE_HINT}}` | where design sources live (Figma, Blueprint, none) | dev |
| `{{FRONTEND_RULE}}` | ` and workflow-frontend.mdc` for frontend, empty for generic | dev, qa, fix |
| `{{VISUAL_STEP}}` | visual QA step (frontend) or empty | qa |
| `{{VISUAL_DIM}}` | the `visual` dimension plus separator (frontend) or empty | qa |
| `{{COMPONENT_GRAPH_PATH}}` | component impact graph path | frontend profile |
| `{{INTAKE_SOURCE}}` | meeting-notes source or ledger | product intake |
| `{{ISSUE_TEMPLATE}}` | issue template path | product intake |
| `{{INTAKE_LABEL}}` | label for intake-created issues | product intake |
| `{{BOT_LOGIN}}`, `{{HUMAN_LOGIN}}` | allowlisted commenters | label router |

Measurement (`validity-*` skills, `pdlc-validity` CLI): `pip install pdlc-validity`.
