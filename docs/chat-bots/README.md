# Modus conversational delivery bots

These documents and sanitized n8n exports define the human-applied Google Chat
layer around `trimble-oss/modus-wc-2.0`.

The pilot replacement path is documented in
[`cursor-docs-review-workflow.md`](cursor-docs-review-workflow.md) and visualized in
[`../dashboard/sheet-pilot-map.html`](../dashboard/sheet-pilot-map.html) (Apps Script +
Cursor only — no n8n on sheet approve). Gemini coordinator Apps Script feeds Meeting
Intake (Drive JSON + UrlFetchApp relay). The sheet orchestrator routes `Controls!B1=review` and `B1=approve` to two
Cursor webhooks. Approve calls Issue Scaffolding directly (no n8n). The n8n/Chat exports
remain available for migration parity and fallback.

| Artifact | Purpose |
| --- | --- |
| [`ticket-bot.md`](ticket-bot.md) | Clarify-first ticket formation and confirmation |
| [`qa-bot.md`](qa-bot.md) | Answer-first shared-context Q&A with optional escalation |
| [`issue-service.md`](issue-service.md) | One validated issue-creation contract |
| [`context-resolver.md`](context-resolver.md) | Explicit private-repository evidence boundary for bot answers |
| [`meeting-intake-rubric.md`](meeting-intake-rubric.md) | Gemini notes classification and completeness rules |
| [`meeting-intake-automation-prompt.md`](meeting-intake-automation-prompt.md) | Full Cursor Meeting Intake automation prompt (sheet pilot) |
| [`review-approve-writeback-automation.md`](review-approve-writeback-automation.md) | Review/Approve Drive write-back (no Apps Script POST from Cursor) |
| [`apps-script/cursor-gemini-meeting-intake-coordinator.gs`](apps-script/cursor-gemini-meeting-intake-coordinator.gs) | Gmail → Intake webhook; Drive relay → review ledger |
| [`apps-script/cursor-sheet-review-orchestrator.gs`](apps-script/cursor-sheet-review-orchestrator.gs) | Sheet ledger: `B1=review` or `B1=approve` to two Cursor webhooks |
| [`backlog-enrichment.md`](backlog-enrichment.md) | PO sheet to GitHub issue quality and readiness contract |
| [`workflows/ticket-bot.template.json`](workflows/ticket-bot.template.json) | Sanitized ticket bot import |
| [`workflows/qa-bot.template.json`](workflows/qa-bot.template.json) | Sanitized Q&A bot import |
| [`workflows/context-resolver.template.json`](workflows/context-resolver.template.json) | Sanitized private manifest evidence resolver |
| [`workflows/meeting-intake.template.json`](workflows/meeting-intake.template.json) | Sanitized Gmail/Calendar/Docs intake import |
| [`workflows/backlog-enrichment.template.json`](workflows/backlog-enrichment.template.json) | Sanitized sheet review/enrichment import |

The JSON files intentionally contain no credential IDs, Chat webhook keys,
GitHub tokens, approval URLs, or team calendar IDs. Import and bind credentials
in n8n manually.
