# Figma capability-check plugin specification

## Problem

Designers need to know whether a Modus component/state already exists before
they commit to a Figma direction. The plugin makes the repository capability
matrix searchable in the design surface and flags a likely mismatch. It does
not replace the Design-Research agent, product approval, or design review.

## User flows

### Search

1. Open the plugin in a Figma file.
2. Enter a component, property, state, event, or phrase such as `readonly`.
3. The plugin searches the current `custom-elements.json` first and enriches
   the result from the generated `designer-context.json` bundle.
4. Results show supported/not-listed, state matrix, token hints, precedent,
   direct impact, source commit, manifest pointer, and links to repository
   docs/Storybook.
5. Curated HTML/ARIA rules are applied after the Modus lookup. A standards
   warning is separate from a Modus capability claim.

### Inspect selection

1. Select a frame or layer whose name contains a Modus tag/state hint.
2. The plugin sends only the selected node ID/name to the UI.
3. The UI compares the hint to the capability matrix.
4. It reports:
   - `existing`: exact capability found;
   - `new-api-candidate`: no matching property/state listed;
   - `ambiguous`: the name cannot be mapped to one component;
   - `source-stale`: matrix or shared context could not be refreshed.

The plugin never says “not possible.” `new-api-candidate` means the request
needs a Design-Research check and possibly product sign-off.

### Handoff

The designer copies a capability-check result into the sheet's design-needed
row or a GitHub issue. The handoff contains the Modus result, standards result,
conditional alternatives, and all source links. The plugin does not contain a
GitHub token and does not create an issue directly.

## Data and security

- For local designer testing, load the pinned bundled snapshots. For release,
  fetch only an allowlisted raw GitHub origin configured at build time.
- Prefer `custom-elements.json` plus `designer-context.json`; use
  `custom-elements.md` for human-readable details.
- Show source commit and generated time.
- Cache for at most 15 minutes in the plugin UI; allow manual refresh.
- Treat parse failure, 404, CORS failure, and stale metadata as visible gaps.
- Send selected node ID/name to the UI only. Do not upload Figma document
  content or private design data.
- No GitHub, Chat, n8n, or MCP credentials in the plugin.

## Capability result shape

```json
{
  "query": "readonly",
  "modusCapability": {
    "status": "existing|new-api-candidate|ambiguous|source-stale",
    "matches": [
      {
        "tag": "modus-wc-text-input",
        "property": "readOnly",
        "source": "src/custom-elements.json#/modules/..."
      }
    ]
  },
  "standards": {
    "status": "compatible|warning|unsupported|unknown",
    "rules": [],
    "alternatives": []
  },
  "selectedNode": {
    "id": "123:456",
    "name": "modus-wc-select / readonly"
  },
  "sourceCommit": "abc123"
}
```

## UI contract

The scaffold uses Modus Web Components for standard controls:

- `modus-wc-text-input` for the search field;
- `modus-wc-button` for Search and Refresh;
- `modus-wc-alert` for source, match, and gap states;
- `modus-wc-card` / `modus-wc-typography` for grouping and labels.

The package version must be pinned in the eventual plugin build. The scaffold
does not claim a package version because the official plugin owner must choose
the supported Modus release.

## Acceptance criteria

- Search returns exact property matches from a current manifest.
- `readonly` distinguishes `readOnly`, `readonly`, and no listed property
  without sibling inference.
- A selected layer produces a visible mismatch result when its state is not
  listed.
- A selected layer such as `modus-wc-select / readonly` produces a separate
  standards warning with conditional options and MDN/WHATWG links.
- Repository context shows state matrix, token hints, precedent, and impact
  only when those facts are present in the generated bundle.
- The UI shows stale/source errors and never treats them as support.
- The UI distinguishes `new-api-candidate` from HTML/ARIA `unsupported`.
- The designer can copy Markdown and JSON handoffs without mutating the file.
- Source links open the target repository/Storybook.
- No credential or private document content is sent to an external endpoint.
- Refreshing the matrix does not require restarting Figma.

## Publishing checklist

- [ ] Replace placeholder raw GitHub URLs.
- [ ] Pin `@trimble-oss/moduswebcomponents` and commit the lockfile.
- [ ] Bundle/register the Modus custom elements and import Modus styles once.
- [ ] Set `data-theme="modus-modern-light"` or the team's approved theme.
- [ ] Configure Figma plugin permissions and review the network allowlist.
- [ ] Test against an existing property, a missing property, and a stale
      manifest.
- [ ] Publish only after the target repository's generated artifact is live.
