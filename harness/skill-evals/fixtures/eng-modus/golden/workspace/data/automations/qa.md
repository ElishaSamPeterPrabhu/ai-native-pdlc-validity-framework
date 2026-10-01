# QA Agent

| Trigger | Match |
|---------|-------|
| Label added | qa-full |
| Label added | qa-rerun |
| Label added | qa-skip |

The label router Action will remove then re-add an existing label.

Gate: npm run tailwind:build, embed:css, embed:component-css, npm test, npm run lint. A gate is not a verdict.
Screenshot Storybook and compare to the Figma or Blueprint source, else main Storybook.
Scope via component-graph reverseImpact depth 1.

Verdicts: ## QA PASSED, ## QA FAILED, ## QA BLOCKED, ## QA SKIPPED.
