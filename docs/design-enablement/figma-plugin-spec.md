# Figma-native Modus designer copilot

## Problem

Modus library designers need grounded help while naming component frames,
choosing properties/states, and avoiding HTML/ARIA traps — without leaving
Figma or opening a chat panel. The copilot surfaces facts and suggestions in
Figma's native command bar and as on-canvas annotations.

It does not replace product approval, design review, or the Cursor
`design-capability-check` skill for issue drafting.

## User flows

### Command-bar autocomplete

1. Run the plugin from Figma quick actions (`Tab` into plugin name).
2. Type a Modus tag, property, or state in the `query` parameter.
3. On every keystroke the plugin calls `figma.parameters.on('input')` and
   `result.setSuggestions(...)`.
4. Suggestions are labeled with grounded status:
   - `existing` — listed in manifest/context;
   - `new-api-candidate` — not listed for that component;
   - `standards-warning` — HTML/ARIA constraint from the standards registry;
   - `source-stale` — pack unavailable; no capability claim is made.

This is retrieval from the shared pack, not a chat transcript.

### Run with selection

1. Select a component frame whose name hints at a Modus tag/state.
2. Complete the `query` parameter and run the plugin.
3. The plugin POSTs `{ query, selection, contextSlice, facts }` to the
   allowlisted local copilot (`http://localhost:3777/suggest` during research).
4. The copilot returns structured `suggestions[]` (see schema). Every item must
   cite pack fields; gaps are reported, not invented.
5. The plugin writes a short annotation on a dedicated **Modus copilot** frame
   beside the selection (sticky note / text). No HTML panel, no chat UI.

### What this is not

- Not a Modus-WC search form in an iframe.
- Not preset FAQ replies keyed on keywords.
- Not a merge-blocking artifact in `trimble-oss/modus-wc-2.0` until the pack
  and suggestion quality are accepted.

## Shared source contract

| Artifact | Role | Consumers |
| --- | --- | --- |
| `custom-elements.json` | Manifest facts | Engine, copilot, Cursor skill |
| `designer-context.json` | State matrix, tokens, precedent, impact | Engine, copilot, Cursor skill |
| `standards-rules.json` | HTML/ARIA constraints | Engine, copilot, Cursor skill |
| `capability-engine.js` | Deterministic facts only | Plugin autocomplete, copilot, tests |
| `capability-result.schema.json` | Result + `suggestions[]` contract | Plugin, copilot, Cursor skill |
| `component-index.json` | Lightweight tag/property index for fast autocomplete | Plugin only |

The engine answers **what is true**. The copilot answers **what to try next**,
using those facts.

## Capability result shape

```json
{
  "query": "modus-wc-select / readonly",
  "modusCapability": {
    "status": "new-api-candidate",
    "tag": "modus-wc-select",
    "property": null,
    "matches": []
  },
  "standards": {
    "status": "unsupported",
    "rules": [],
    "alternatives": []
  },
  "suggestions": [
    {
      "kind": "standards-warning",
      "text": "Do not model native readonly on select",
      "rationale": "HTML select has no readonly semantics",
      "citations": ["standards-rules.json#html.select.readonly"],
      "grounding": "unsupported"
    }
  ],
  "selectedNode": { "id": "123:456", "name": "modus-wc-select / readonly" },
  "sourceCommit": "abc123"
}
```

## Data and security

- Plugin sandbox sends only selection `id`, `name`, `type`, plus the query and
  a context slice. It never uploads the Figma document.
- No API keys in the plugin. The copilot runs locally during research; production
  would use a Trimble-hosted allowlisted URL.
- `networkAccess.allowedDomains` lists only the copilot origin.
- Bundled snapshots are for offline autocomplete; stale pack → `source-stale`.

## Acceptance criteria

- Autocomplete returns tag/property suggestions without opening a plugin panel.
- `modus-wc-select / readonly` shows a standards warning separate from Modus status.
- Run creates a visible on-canvas annotation with cited suggestions.
- Copilot refuses to invent APIs when the pack has no fact (returns gap suggestion).
- Cursor `design-capability-check` skill uses the same schema vocabulary.
- No credential or private document content leaves the designer machine except
  the allowlisted copilot POST payload.

## Local development

```bash
cd docs/design-enablement/figma-plugin
npm install
npm run build
npm run copilot   # terminal 1 — http://localhost:3777
# Import manifest.json in Figma → Development → run from quick actions
```

## Publishing checklist (future)

- [ ] Host copilot on Trimble allowlisted HTTPS origin.
- [ ] Replace localhost in `manifest.json` network allowlist.
- [ ] Pin context pack revision and document refresh policy.
- [ ] Do not add `designer-context-check.yml` to Modus repo until accepted.
