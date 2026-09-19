---
name: design-capability-check
description: Research Modus component capabilities from manifest, MCP, code, and graph before drafting an issue.
---

# Design capability check

Use before proposing new component work or drafting an issue in Cursor. Replaces
the Chat ticket-bot research step for IDE users. Uses the same shared pack and
result vocabulary as the Figma-native Modus designer copilot.

## Shared pack (same contract as Figma plugin)

Read from the target repository or the research snapshot under
`docs/design-enablement/figma-plugin/`:

| Artifact | Purpose |
| --- | --- |
| `custom-elements.json` | Manifest facts |
| `designer-context.json` | State matrix, tokens, precedent, impact |
| `standards-rules.json` | HTML/ARIA constraints |
| `capability-result.schema.json` | Result + `suggestions[]` vocabulary |

Deterministic facts come from `capability-engine.js` (`existing`,
`new-api-candidate`, `ambiguous`, `source-stale`, standards status). Structured
`suggestions[]` items must use schema kinds (`existing`, `new-api-candidate`,
`standards-warning`, `token-hint`, `state-matrix`, `precedent`, `impact`,
`gap`) with `text`, `rationale`, `citations[]`, and `grounding`. Never invent
APIs when the pack has no fact — emit a `gap` suggestion instead.

## Procedure

1. Read the target repository's `AGENTS.md` and applicable `.cursor/rules/*`.
2. Identify the exact component tag and requested state/property/event.
3. Query `src/custom-elements.json`, `custom-elements.md`, and the shared
   `designer-context.json` bundle when present.
4. Call MCP **`component-capabilities`** (or `get_modus_component_data`) with
   exact `component_name`, `property`, `state`, or `query`; use
   `include_siblings: true` only when comparing sibling precedent.
5. Read component **source** before claiming behavior:
   - `src/components/<tag>/<tag>.tsx`
   - matching `.scss`, `.spec.ts`, `.stories.ts`, and `readme.md`
6. Read checked-in styles/tokens and one relevant **sibling** component when a
   reusable precedent may exist.
7. Read direct `reverseImpact[tag]` from
   `docs/component-graph/component-graph.json`. If it is absent, use the
   component README `Used by` / `Depends on` section and label that source.
   Do not infer dependents from names.
8. Apply the curated HTML/ARIA standards rule registry when the request maps
   to a native control or semantic state. Cite the authoritative standard and
   explain alternatives with submission, focus, and accessibility tradeoffs.
9. Search GitHub issues and PRs for duplicates and prior decisions.
10. Record the result as `existing`, `new-api-candidate`, or
   `not-found-in-inspected-source`.
11. Emit grounded `suggestions[]` in the shared schema — design next steps, not
   canned chat replies. Each suggestion cites manifest paths, context bundle
   keys, or standards rule ids.

## Required output

```markdown
## DESIGN RESEARCH

### Request
- Component/state:
- User outcome:

### Capability check
| Requested capability | Result | Source |
| --- | --- | --- |

### Grounded suggestions
| Kind | Suggestion | Rationale | Citations |
| --- | --- | --- | --- |

### Standards and design guardrail
- Compatibility:
- Constraint:
- Alternatives and tradeoffs:
- Standards source:

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
- State matrix:
- Token hints:
- Precedent:

### Impact and handoff
- Direct reverse impact:
- Impact source:
- API compatibility:
- QA-source / QA-verify:
```

Every “supports” or “does not support” statement must cite a manifest path,
MCP response, component source file, spec, Storybook source, or
context-bundle entry. Every standards constraint must cite its registry entry
and authoritative documentation. Every suggestion row must cite pack fields.
If sources cannot answer a required question, stop with:

```markdown
## NEED CLARIFICATION
- [one concrete question]
```

Do not invent tokens, states, browser behavior, or a replacement interaction.
Do not create GitHub issues, labels, or PRs in this skill. Hand off to
`design-to-issue` when the human wants a draft issue body.
