---
name: design-to-issue
description: Turn a researched design decision into a dual-audience Modus issue.
---

# Design-to-issue

Use after `design-capability-check` and before asking Issue Scaffolding to
create or enrich an issue.

## Inputs

- capability-check result with citations;
- user outcome and affected component(s);
- Figma or staged Drive source, if it exists;
- state coverage and token decisions;
- linked design/development issue or duplicate candidates;
- unanswered product/design questions.

## Procedure

1. Search existing issues and PRs before drafting.
2. Preserve the capability check exactly; do not convert “not listed” into
   “impossible.”
3. Separate design work from implementation work. Link paired issues when
   they share one feature.
4. Specify relevant happy, loading, empty, error, disabled, focus/keyboard,
   responsive, and accessibility states.
5. Use only tokens and Modus primitives documented in the repository/MCP.
6. State whether the design reuses an existing API or proposes a new one.
7. If a cloud QA agent will consume the design, provide a staged Drive folder
   with `manifest.json`, the matching variant, `variable-defs.json`,
   `design-context.md`, and required screenshots.
8. If a necessary decision is missing, ask one numbered question at a time and
   do not call the issue service.

## Draft format

```markdown
## Context
[user outcome and capability evidence]

## Proposed change
[design decision and API reuse/new API statement]

## Acceptance Criteria
- [ ] [happy path]
- [ ] [relevant loading/empty/error/disabled path]
- [ ] [keyboard and accessibility behavior]
- [ ] [responsive/theme behavior]

## Design notes
- States:
- Tokens:
- Components:
- Figma / staged Drive source:
- Open decisions:

## Technical notes
- Existing implementation / sibling precedent:
- Direct reverse impact:
- Compatibility and migration:

## Test plan
- Storybook:
- Unit:
- Accessibility:
- QA-source / QA-verify:

## Sources
- Capability manifest:
- MCP:
- Component docs:
- Related issues/PRs:
```

The resulting issue is still a draft. The shared issue service owns duplicate
search and the Issue Scaffolding automation owns final research and
clarification. This skill never auto-approves implementation.
