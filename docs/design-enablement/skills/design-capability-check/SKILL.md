---
name: design-capability-check
description: Check Modus component capabilities and states before design work.
---

# Design capability check

Use this skill before proposing a new Modus component, prop, state, token
variant, or Figma interaction.

## Procedure

1. Read the target repository's `AGENTS.md` and applicable `.cursor/rules/*`.
2. Identify the exact component tag and requested state/property/event.
3. Query `src/custom-elements.json` and the Modus component-docs MCP.
4. Read the component readme, Storybook story, and one relevant sibling
   component when a reusable precedent may exist.
5. Read the direct `reverseImpact[tag]` entry from
   `docs/component-graph/component-graph.json`. Do not infer dependents.
6. Search GitHub issues and PRs for an existing request or decision.
7. Record the result as `existing`, `new-api-candidate`, or
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
- Manifest/MCP:

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
MCP response, component source, or Storybook source. If the sources cannot
answer a required question, stop with:

```markdown
## NEED CLARIFICATION
- [one concrete question]
```

Do not invent tokens, states, or browser behavior. Do not create labels, open a
PR, or create a Figma file. The human decides whether a new API is desirable.
