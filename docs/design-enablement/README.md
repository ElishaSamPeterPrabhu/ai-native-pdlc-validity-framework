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

1. **Figma Agents** — select component → `/modus-design-assist` (intake) or `/modus-accessibility-check` (readonly demo) → conversational clarifiers → actionable answer.
2. **Cursor** — same question with full pack citations when they need repo proof or an issue draft.
