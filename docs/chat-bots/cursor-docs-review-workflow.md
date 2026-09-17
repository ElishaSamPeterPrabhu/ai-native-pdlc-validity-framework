# Cursor review ledger workflow

This is the sheet-led replacement path for the pilot meeting-intake flow.
Meeting notes stay a Google Doc. The **review ledger** lives in a Google Sheet
(`ReviewItems`, `ReviewItemsDetail`, `Issues`, `Controls`). Apps Script:
[`apps-script/cursor-sheet-review-orchestrator.gs`](apps-script/cursor-sheet-review-orchestrator.gs).

Gemini coordinator:
[`apps-script/cursor-gemini-meeting-intake-coordinator.gs`](apps-script/cursor-gemini-meeting-intake-coordinator.gs).

## End-to-end path (Gemini to GitHub)

The initial Gemini trigger does **not** create issues. Review does **not**
create issues. Approve does **not** write GitHub itself.

```text
Gemini notes
  → Gemini coordinator Apps Script
  → Cursor Meeting Intake automation
  → intake-pending-<docId>.json on Drive
  → coordinator UrlFetchApp relay → orchestrator /exec
  → ReviewItems sheet (needs-review)

Controls!B1 = review
  → sheet orchestrator
  → Cursor Review automation
  → write-back cursorComment only

Controls!B1 = approve
  → sheet orchestrator (skipIssue rows excluded)
  → Cursor Approve automation
  → Cursor Issue Scaffolding (288c955b) webhook
  → GitHub draft issue
  → write-back issueUrl + Issues tab
```

| Piece | Role | Creates GitHub issues? |
| --- | --- | --- |
| Gemini coordinator Apps Script | Gmail/Gemini → Intake webhook; Drive relay → ledger | No |
| Sheet orchestrator Apps Script | `B1=review` or `B1=approve` → matching webhook | No |
| Meeting Intake automation | Classify Doc → Drive JSON; coordinator relays to sheet | No |
| Review automation | Evidence + short `cursorComment` | No |
| Approve automation | POST Issue Scaffolding webhook; write-back URLs | No |
| Issue Scaffolding `288c955b` | Research and draft/enrich the GitHub issue | Yes |

`skipIssue=TRUE` rows never leave the orchestrator on review or approve.

## Trigger

The only human trigger is **Controls!B1**:

- `review` — send non-skip rows to `CURSOR_REVIEW_CALLBACK_URL`
- `approve` — send non-skip rows to `CURSOR_APPROVE_CALLBACK_URL`

`reviewerComment` never triggers. The per-row `command` column is leftover
storage; it is not the trigger.

`skipIssue` is the skip control for both commands.

## State model

`ReviewItems` is the reviewer-facing surface:

```text
itemId | round | title | classification | status | skipIssue |
reviewerComment | cursorComment | command | iterationCount |
issueNumber | issueUrl | updatedAt
```

`ReviewItemsDetail` stores remaining intake fields as JSON keyed by `itemId`.

`Issues` has one row per issue attempt:

```text
itemId | idempotencyKey | status | issueNumber | issueUrl |
createdAt | lastError | reviewComment
```

Allowed classifications:

```text
repo-work | design-work | process/meta | decision-record | already-tracked
```

Allowed item statuses:

```text
needs-review | changes-requested | approved | rejected | duplicate |
clarification | creating | created | failed
```

Only `repo-work` and `design-work` rows that a human approved and did not skip
reach Issue Scaffolding. `process/meta`, `decision-record`, `already-tracked`,
`rejected`, and `clarification` never create issues.

The stable issue key is:

```text
gemini:<meetingDocId>:<itemSuffix>
```

where `itemSuffix` is the row `itemId` with a leading `<meetingDocId>:` removed
when present. The orchestrator computes this via `buildIdempotencyKey` and may
attach it on approve webhook items.

## Orchestrator properties

Required:

- `REVIEW_SHEET_ID`
- `CURSOR_REVIEW_CALLBACK_URL`
- `CURSOR_APPROVE_CALLBACK_URL`
- `CURSOR_REVIEW_INGRESS_TOKEN` — Review webhook Bearer + write-back secret
- `CURSOR_APPROVE_INGRESS_TOKEN` — Approve webhook Bearer + write-back secret

Legacy: `CURSOR_INGRESS_TOKEN` is still accepted as the Review token if
`CURSOR_REVIEW_INGRESS_TOKEN` is unset.

Optional:

- `REVIEW_LEDGER_POST_URL` — public `/macros/s/.../exec` write-back URL
- `DRY_RUN_REVIEW`

Issue Scaffolding credentials for Approve (either source):

- Cloud Agent env secrets `ISSUE_SCAFFOLDING_WEBHOOK_URL` +
  `ISSUE_SCAFFOLDING_WEBHOOK_TOKEN`, or
- Orchestrator Script Properties with the same names — approve payloads include
  `issueScaffoldingWebhookUrl` and `issueScaffoldingWebhookToken` when set
  (workaround when Cloud Agents → Environments table will not load)

URL: `https://api2.cursor.sh/automations/webhook/288c955b-aaad-11f1-b532-320a589b8025`
Token: Generate auth header on `[PILOT] Modus Issue Scaffolding`

The sheet approve path does **not** use n8n Issue Service. Chat/ticket/QA bots
may still use the shared n8n adapter documented in [`issue-service.md`](issue-service.md).
Do not call Scaffolding from Intake, Review, or Apps Script.

## Gemini coordinator properties

Required (standalone coordinator project):

- `CURSOR_MEETING_INTAKE_WEBHOOK_URL`
- `CURSOR_INGRESS_TOKEN` — Bearer to call Meeting Intake webhook
- `CURSOR_REVIEW_INGRESS_TOKEN` — must match orchestrator review token (ledger relay)
- `REVIEW_SHEET_ID`
- `REVIEW_LEDGER_POST_URL` — same public `/exec` as orchestrator write-back
- `INTAKE_PENDING_FOLDER_ID` — Drive folder for `intake-pending-<docId>.json`

Relay helpers: `postItemsToLedger`, `relayIntakePendingForDoc(docId)`,
`scanIntakePendingRelay()` (runs after each Gmail poll). Prompt:
[`meeting-intake-automation-prompt.md`](meeting-intake-automation-prompt.md).

## Write-back

Cursor POSTs JSON to the orchestrator `/exec` URL with `ingressToken` from the
webhook body:

```json
{
  "ingressToken": "...",
  "mode": "review_writeback",
  "reviewId": "meeting:<docId>",
  "sheetId": "<sheetId>",
  "round": 1,
  "itemUpdates": [],
  "issueResults": []
}
```

Review write-back may include `cursorComment` (orchestrator truncates to 320
chars). Approve write-back on success must omit `cursorComment` and include
`issueNumber`, `issueUrl`, and `issueResults`.

### Approve → Scaffolding POST (sheet path)

Approve POSTs one Scaffolding webhook request per eligible row:

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
      "type": "feature",
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

The orchestrator may attach `idempotencyKey` and `meetingDocUrl` on each webhook
item. Approve must map full row fields (including `ReviewItemsDetail` merge)
into `additional_context`. Idempotency suffix strips a leading `<docId>:` from
`itemId` so keys are not doubled.

Approve outcome rules:

- `issueUrl` non-empty → `itemUpdates.status: approved`, `issueResults.status: created`
- Scaffolding `NEED CLARIFICATION` or empty URL after ~2 min poll →
  `status: clarification`, `lastError` = first question; never `accepted` with
  empty `issueUrl`

Idempotency: skip POST when the row or **Issues** tab already has the same
`idempotencyKey` with status `created` or a non-empty `issueUrl`.

### Write-back POST (avoid 405)

Apps Script Web Apps redirect POST with 302; **external** clients (Cursor cloud,
curl) that follow as GET return 405 or spurious `Invalid ingress token`.

**Meeting Intake:** do **not** POST from the Cursor automation. Intake writes
`intake-pending-<docId>.json` to Drive; the Gemini coordinator relays with
`UrlFetchApp`. See [`meeting-intake-automation-prompt.md`](meeting-intake-automation-prompt.md).

**Review and Approve write-back:** do **not** POST from Cursor. Write
`writeback-review-...-r<N>.json` or `writeback-approve-...-r<N>.json` to the
pending Drive folder; orchestrator `scanWritebackPendingRelay()` applies updates
in-process on each poll. See
[`review-approve-writeback-automation.md`](review-approve-writeback-automation.md).

Set on the **orchestrator** (same folder as intake is fine):

- `WRITEBACK_PENDING_FOLDER_ID`, or
- `INTAKE_PENDING_FOLDER_ID` (fallback)

Webhook bodies include `writebackPendingFolderId` when configured.

Legacy **Review and Approve** agents that still POST to `reviewProxyUrl` may
intermittently succeed; treat Drive relay as the supported path.

If migrating legacy prompts, agents must:

1. Use the public `https://script.google.com/macros/s/.../exec` URL from
   `body.reviewProxyUrl` (orchestrator `getReviewProxyUrl()` — never
   `/a/macros/trimble.com/...`).
2. POST JSON with `Content-Type: application/json` and
   `Authorization: Bearer <ingressToken>` in the body field `ingressToken` as
   documented above.
3. Do **not** follow redirects as GET. If the first response is 301/302, read
   `Location` and POST the **same JSON body** once to that URL.
4. Treat 2xx on the final POST as success; do not append duplicate
   `issueResults` on retry.

Preferred: use Drive write-back files instead of the steps above.

The orchestrator upserts **Issues** tab rows by `idempotencyKey` (update in
place; append only when the key is new).

### Apps Script deploy checklist

When [`cursor-sheet-review-orchestrator.gs`](apps-script/cursor-sheet-review-orchestrator.gs)
changes in the repo:

1. Open the bound orchestrator project in the Apps Script editor.
2. Replace `Code.gs` with the repo file (full paste).
3. **Deploy → Manage deployments → Edit → New version** (keep the same Web App
   URL; access **Anyone**).
4. Confirm `REVIEW_LEDGER_POST_URL` (if set) uses the public `/macros/s/.../exec`
   form, not the Trimble `/a/macros/...` URL.
5. Run `repairPilotLoadingSurfaceKeepIssue()` once if the pilot loading row
   surface is mangled but already has `issueUrl` (do **not** run
   `pilotPrepareLoadingRow()` on rows with a created issue).
6. Verify `doGet` on the `/exec` URL returns `"configured": true`.

## Security

1. `LockService` while claiming a round.
2. Validate ingress token on inbound POST.
3. Allowlisted spreadsheet ID.
4. Redact tokens from error messages.
5. One Cursor POST per typed B1 command; poll with empty B1 does nothing.
