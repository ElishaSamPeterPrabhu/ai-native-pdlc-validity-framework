# Modus designer copilot

Two surfaces, one shared context pack:

| Surface | Role |
| --- | --- |
| **Figma plugin** | Autocomplete while typing; capture query + selection; hand off to Cursor |
| **Cursor skill** (`design-capability-check`) | Interactive agent research, standards, impact, design decisions, issue draft |

Figma does **not** run the agent. Static text on the canvas is not interactive.
The pilot demo should show **Cursor chat with the skill**, not a text node in Figma.

## Figma plugin (capture + handoff)

```bash
npm install
npm run build
```

Import `manifest.json` in Figma Development.

1. Tab into **Modus Designer Copilot** in quick actions.
2. Autocomplete helps pick `modus-wc-select / readonly`.
3. Run → **Continue in Cursor** panel opens with a copyable prompt.
4. Paste in Cursor chat → agent runs `design-capability-check` interactively.

## Cursor skill (interactive copilot)

In Cursor chat:

> Run design-capability-check for `modus-wc-select / readonly`. What should I design? Does Modus support this? What are the HTML constraints?

The agent reads the shared pack, MCP, component source, and returns grounded suggestions you can discuss and act on. Use `design-to-issue` when ready to draft a GitHub issue.

## Shared pack

Same files for both surfaces:

- `custom-elements.json`
- `designer-context.json`
- `standards-rules.json`
- `capability-engine.js`
- `capability-result.schema.json`

## Pilot demo recommendation

1. **Figma** (30 sec): show autocomplete + handoff copy.
2. **Cursor** (main demo): paste prompt → live agent conversation with citations, alternatives, and next steps.
