---
name: repo-context-resolver
description: Answer Modus repository questions from cited capability and impact evidence, or return clarification when evidence is insufficient.
---

# Repository context resolver

Search in this order and cite each material claim:

1. `custom-elements.json` and generated `custom-elements.md`;
2. applicable `.cursor/rules` and repository instructions;
3. the direct `reverseImpact` entry in
   `docs/component-graph/component-graph.json`;
4. component source, stories, readmes, and sibling precedent;
5. staged design source or an explicit design-needed result;
6. existing GitHub issues and PRs.

For each answer, separate observed repository facts from recommendations and
open questions. Do not invent props, tokens, states, consumers, or affected
products. If the evidence does not support an answer, return a focused
clarification request rather than creating an issue.

When a confirmed work item remains, hand it to `review-ledger-round` and the
shared Issue Service. This skill does not create GitHub issues directly.

