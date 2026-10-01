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

Measurement (`validity-*` skills, `pdlc-validity` CLI): `pip install pdlc-validity`.
