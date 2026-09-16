---
name: review-ledger-round
description: Process a sheet review round from orchestrator webhook items. Update cursorComment only. Never create issues.
---

# Review ledger round

Process only the rows in the webhook body. The orchestrator already excluded
`skipIssue=TRUE` rows. Trigger is Controls B1 `review`, not the command column.

- Search `ElishaSamPeterPrabhu/modus-wc-2.0` for evidence and duplicates.
- Write short `cursorComment` (max 320 characters).
- Do **not** HTTP POST to `reviewProxyUrl` from Cursor cloud (Apps Script 302/405).
- Write `writeback-review-<reviewId-slug>-r<round>.json` to Drive folder
  `writebackPendingFolderId` from the webhook body. Slug = `reviewId` with `:`
  replaced by `-`.
- Payload: `{ mode:"review_writeback", reviewId, sheetId, round, itemUpdates }`
  without `ingressToken`. Also output `REVIEW_WRITEBACK_PAYLOAD` fenced JSON.
- Orchestrator `scanWritebackPendingRelay()` applies the file on the next poll.
- Do not call Issue Service. Do not create GitHub issues.
- Do not reclassify the meeting Doc from scratch.
