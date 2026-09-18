---
name: design-to-issue
description: Turn researched Modus capability evidence into a cited GitHub issue draft in Cursor chat.
---

# Design-to-issue

Use after `design-capability-check` when the user wants a draft issue in Cursor.
This replaces the Chat ticket-bot draft/confirm step. It does **not** auto-create
GitHub issues; the human confirms and files (or routes through Issue Scaffolding).

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
3. Separate design work from implementation work. Link paired issues when they
   share one feature.
4. Specify relevant happy, loading, empty, error, disabled, focus/keyboard,
   responsive, and accessibility states.
5. Use only tokens and Modus primitives documented in the repository/MCP/code.
6. When a native control or semantic state is involved, include the standards
   constraint, authoritative source link, and conditional alternatives with
   focus, submission, and accessibility tradeoffs.
7. State whether the work reuses an existing API or proposes a new one.
8. In **Technical notes**, cite inspected source files (tsx/scss/spec/stories),
   state matrix/token evidence, and direct graph impact or README impact
   fallback; do not paraphrase without paths.
9. If a cloud QA agent will consume the design, provide a staged Drive folder
   with `manifest.json`, the matching variant, `variable-defs.json`,
   `design-context.md`, and required screenshots.
10. If a necessary decision is missing, ask one numbered question at a time and
   stop without a final draft.

## Draft format

```markdown
## Context
[user outcome and capability evidence]

## Proposed change
[decision and API reuse/new API statement]

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
- Likely files:
- Direct reverse impact:
- State matrix and token evidence:
- Standards constraints and alternatives:
- Compatibility and migration:

## Test plan
- Storybook:
- Unit:
- Accessibility:
- QA-source / QA-verify:

## Sources
- Capability manifest:
- Designer context bundle:
- Standards registry:
- MCP / custom-elements.md:
- Component source:
- Related issues/PRs:
```

After the human confirms, they may `gh issue create`, paste into Issue
Scaffolding, or use the sheet approve path. Never auto-approve implementation.
