---
name: design-capability-check
description: Research Modus component capabilities from manifest, MCP, code, and graph before drafting an issue.
---

# Design capability check

Use before proposing new component work or drafting an issue in Cursor. Replaces
the Chat ticket-bot research step for IDE users.

## Procedure

1. Read the target repository's `AGENTS.md` and applicable `.cursor/rules/*`.
2. Identify the exact component tag and requested state/property/event.
3. Query `src/custom-elements.json` and `custom-elements.md` when present.
4. Call MCP **`component-capabilities`** (or `get_modus_component_data`) with
   exact `component_name`, `property`, `state`, or `query`; use
   `include_siblings: true` only when comparing sibling precedent.
5. Read component **source** before claiming behavior:
   - `src/components/<tag>/<tag>.tsx`
   - matching `.scss`, `.spec.ts`, `.stories.ts`, and `readme.md`
6. Read one relevant **sibling** component when a reusable precedent may exist.
7. Read direct `reverseImpact[tag]` from
   `docs/component-graph/component-graph.json`. Do not infer dependents.
8. Search GitHub issues and PRs for duplicates and prior decisions.
9. Record the result as `existing`, `new-api-candidate`, or
   `not-found-in-inspected-source`.

## Required output

```markdown
## DESIGN RESEARCH

### Request
- Component/state:
- User outcome:

### Capability check
| Requested capability | Result | Source |
| --- | --- | --- |

### Existing precedent
- Sibling/component:
- Manifest/MCP/code:

### State and design contract
- Happy:
- Loading:
- Empty:
- Error:
- Disabled:
- Focus/keyboard:
- Responsive:
- Tokens:
- Design source:

### Impact and handoff
- Direct reverse impact:
- API compatibility:
- QA-source / QA-verify:
```

Every “supports” or “does not support” statement must cite a manifest path,
MCP response, component source file, spec, or Storybook source. If sources
cannot answer a required question, stop with:

```markdown
## NEED CLARIFICATION
- [one concrete question]
```

Do not invent tokens, states, or browser behavior. Do not create GitHub issues,
labels, or PRs in this skill. Hand off to `design-to-issue` when the human wants
a draft issue body.
