# Dev Agent

| Trigger | Match | By |
|---------|-------|----|
| Comment on issues | /approve | Me |
| Comment on pull requests | /refine | Me |
| Label added | qa-failed | n/a |

Before Open PR: npm run tailwind:build, npm run embed:css, npm run embed:component-css, npm test, npm run lint.

Post a PR conversation comment: `Routing: qa-full` or `Routing: qa-skip` (qa-skip only for .scss, .tailwind.ts, .stories.ts, docs).

On qa-failed: repair only what ## QA FAILED lists, then comment `Fix applied: ...` and `QA-rerun: add`.
After 3 iterations: `Max iterations reached` and add needs-human.

Never merge. Humans merge.
