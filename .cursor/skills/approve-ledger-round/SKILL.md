---
name: approve-ledger-round
description: Process a sheet approve round. Call Issue Scaffolding for eligible rows. Do not rewrite cursorComment on success.
---

# Approve ledger round

Process only the rows in the webhook body. The orchestrator already excluded
`skipIssue=TRUE` rows. Trigger is Controls B1 `approve`.

- Process only `repo-work` and `design-work` rows. Ignore all other
  classifications.
- Idempotency key: use `item.idempotencyKey` from the webhook when present;
  else `gemini:<docId>:<suffix>` where `docId` is from `reviewId`
  (`meeting:<docId>`) and `suffix` is `itemId` with a leading `<docId>:`
  stripped — never double-prefix the docId.
- Repo: `ElishaSamPeterPrabhu/modus-wc-2.0`. `autoApprove` is always false.
- Do **not** call n8n Issue Service on the sheet path. POST **Issue Scaffolding**
  directly. Credentials: `body.issueScaffoldingWebhookUrl` /
  `body.issueScaffoldingWebhookToken` from the webhook (Apps Script passthrough),
  else env `ISSUE_SCAFFOLDING_WEBHOOK_URL` + `ISSUE_SCAFFOLDING_WEBHOOK_TOKEN`.
- Before POST, skip rows that already have `issueUrl` or a matching row on the
  sheet **Issues** tab for the same idempotency key with status `created`.
- Scaffolding POST body (one row at a time):

```json
{
  "prompt": "Research and scaffold this approved sheet row using pilot Issue Scaffolding instructions.",
  "issue_url": null,
  "repo": "ElishaSamPeterPrabhu/modus-wc-2.0",
  "labels": ["needs-scaffolding"],
  "additional_context": {
    "sheetApproved": true,
    "normalized_request": {
      "repo": "ElishaSamPeterPrabhu/modus-wc-2.0",
      "title": "...",
      "summary": "...",
      "type": "feature|design|bug|docs",
      "components": [],
      "labels": ["needs-scaffolding"],
      "source": {
        "kind": "gemini-notes",
        "meetingDocId": "...",
        "url": "https://docs.google.com/document/d/.../edit"
      },
      "contextEvidence": [],
      "acceptanceCriteria": [],
      "designNeeded": false,
      "idempotencyKey": "gemini:<docId>:<suffix>",
      "autoApprove": false
    },
    "review": {
      "reviewerComment": "...",
      "cursorComment": "...",
      "acceptanceCriteria": [],
      "designNeeded": false,
      "classification": "repo-work"
    },
    "source": {
      "kind": "gemini-notes",
      "meetingDocId": "...",
      "url": "https://docs.google.com/document/d/.../edit"
    },
    "context_evidence": [],
    "raw_conversation": []
  },
  "auto_approve": false,
  "idempotency_key": "gemini:<docId>:<suffix>"
}
```

Add to `additional_context`: `"resultFolderId": "<writebackPendingFolderId>"`.

- Populate `context_evidence`, `raw_conversation`, and `review` from merged row
  fields (`sourceExcerpt`, `rationale`, `reviewerComment`, `cursorComment`,
  `acceptanceCriteria`, `componentHints`). Use `row.meetingDocUrl` when present.
- Use `type: design` for `design-work`; add `design-research` label when
  design work needs research. Do not invent scope the row does not support.
- Do not create GitHub issues yourself. Scaffolding creates issues; Approve reads
  the Drive result file Scaffolding writes.
- Forward `writebackPendingFolderId` to Scaffolding as
  `additional_context.resultFolderId`.
- After Scaffolding POST, poll Drive for
  `scaffolding-result-<idempotencyKey with ":" → "-">.json` in
  `writebackPendingFolderId` (every 30s, max 4 attempts). Parse `verdict`:
  - `need_clarification` → write-back `status: clarification`,
    `lastError` = `clarificationQuestion` from file.
  - `issue_created` → write-back `status: approved`, `issueUrl` from file.
  - `error` / timeout → write-back `status: failed`.
- GitHub poll is optional verify only when verdict is `issue_created`; do not use
  GitHub poll as primary clarification signal.
- If Scaffolding returns `NEED CLARIFICATION` in run output but Approve must not
  parse webhook body — only the Drive result file counts.
- On success (`issueUrl` non-empty from result file), write-back `status: approved`,
  `issueResults.status: created`, `issueNumber`, `issueUrl`. Do not include
  `cursorComment`.
- Do **not** HTTP POST sheet write-back to `reviewProxyUrl` (Apps Script 302/405).
- Write `writeback-approve-<reviewId-slug>-r<round>.json` to Drive folder
  `writebackPendingFolderId`. Payload includes `itemUpdates` and `issueResults`
  without `ingressToken`. Output `REVIEW_WRITEBACK_PAYLOAD` fenced JSON.
- Orchestrator `scanWritebackPendingRelay()` applies the file on the next poll.
