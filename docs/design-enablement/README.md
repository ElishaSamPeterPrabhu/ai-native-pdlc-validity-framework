# Designer enablement kit

Modus designers get interactive help from **Figma Agents + custom skills** (primary) and **Cursor skills** (deep research + issues). The custom Figma plugin is optional for autocomplete/handoff only.

| Artifact | Use |
| --- | --- |
| [`figma-agent/`](figma-agent/) | **Upload-ready Figma agent skills** — `/modus-design-assist`, `/modus-capability-check`, `/modus-generate-states`, `/modus-accessibility-check` |
| [`figma-plugin/`](figma-plugin/) | Optional parameter plugin (autocomplete + Cursor handoff) |
| [`figma-plugin-spec.md`](figma-plugin-spec.md) | Plugin contract (secondary surface) |
| [`.cursor/skills/design-capability-check/SKILL.md`](../../.cursor/skills/design-capability-check/SKILL.md) | Cursor agent — manifest, MCP, source, issue handoff |
| [`.cursor/skills/design-to-issue/SKILL.md`](../../.cursor/skills/design-to-issue/SKILL.md) | GitHub issue draft from research |

## Recommended pilot demo

Operator script: [`../pilot/interactive-demo-runbook.md`](../pilot/interactive-demo-runbook.md). Hub: [`../../dashboard/sheet-pilot-map.html`](../../dashboard/sheet-pilot-map.html).

1. **Figma Agents** (parallel track, not sheet-triggered) — select component → `/modus-design-assist` or `/modus-accessibility-check`.
2. **Sheet ledger** — walk a completed row, or type `review` / `approve` in `Controls!B1` on a **new** row. Do not re-approve a row that already has `issueUrl`.
3. **Cursor** (optional) — `design-capability-check` when they need repo citations or an issue draft. No Design-Research cloud automation.
