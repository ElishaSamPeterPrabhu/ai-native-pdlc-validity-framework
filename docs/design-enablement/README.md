# Designer enablement kit

This kit makes the same Modus repository context available before a designer
commits to a new component state or API. It is a portable source package for
the official `modus-wc-2.0` repository, the Figma plugin owner, and designers
using Cursor.

| Artifact | Use |
| --- | --- |
| [`custom-elements.md`](custom-elements.md) | Derived distribution contract for the capability matrix |
| `designer-context.json` | Shared component, state, token, precedent, impact, and source-link context bundle |
| [`render_custom_elements.py`](render_custom_elements.py) | Deterministic manifest-to-Markdown renderer |
| [`figma-plugin-spec.md`](figma-plugin-spec.md) | Plugin behavior, security, and publishing contract |
| [`figma-plugin/`](figma-plugin/) | Vanilla Figma plugin scaffold using Modus elements in its UI |
| [`skills/design-capability-check/SKILL.md`](skills/design-capability-check/SKILL.md) | Pre-design repository capability check |
| [`skills/design-to-issue/SKILL.md`](skills/design-to-issue/SKILL.md) | Convert a researched design decision into a shared issue draft |

## Distribution path

1. The official Modus repository generates `custom-elements.md` from
   `src/custom-elements.json` in CI.
2. The official Modus repository generates and checks `designer-context.json`
   from the manifest, checked-in component sources, styles, stories, and graph
   or README impact fallback.
3. The generated files are committed and available at raw GitHub URLs.
4. The Figma plugin fetches the raw JSON/context from an allowlisted host.
5. Chat bots and Cursor agents use the manifest/MCP as authority and the
   Markdown as a readable index.
6. A stale, missing, or malformed artifact is shown as a gap; it is never
   treated as evidence that a capability exists.

The renderer in this kit is a portable starting point. The target repository
should own its build integration and package/version policy.

## Before publishing

- Set the raw GitHub URL to the official repository and default branch.
- Pin the Modus package used by the plugin UI; do not use a floating version.
- Add the plugin's allowed-host policy and cache expiry.
- Verify the generated file against a current target manifest.
- Test a known existing property, a missing property, and a malformed manifest.
