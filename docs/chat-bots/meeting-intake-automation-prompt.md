# Meeting Intake automation prompt (sheet-led pilot)

Paste the block below into **`[PILOT] Meeting Intake → Review Sheet`** in Cursor
Automations. Repo checkout: `ElishaSamPeterPrabhu/modus-wc-2.0` / `main`.

**Tools:** GitHub MCP, Google Drive MCP. Do **not** enable Issue Service or
Scaffolding for intake.

**Why no HTTP POST to orchestrator:** Apps Script Web Apps return 302 to
`googleusercontent.com`. External clients (Cursor cloud, curl) get **405** on
re-POST or **400 Invalid ingress token** on GET. The **Gemini coordinator**
relays ledger writes with `UrlFetchApp` (see
[`cursor-gemini-meeting-intake-coordinator.gs`](apps-script/cursor-gemini-meeting-intake-coordinator.gs)).

## Coordinator properties (required)

| Property | Purpose |
| --- | --- |
| `CURSOR_MEETING_INTAKE_WEBHOOK_URL` | This automation's webhook URL |
| `CURSOR_INGRESS_TOKEN` | Bearer token to **call** this webhook |
| `CURSOR_REVIEW_INGRESS_TOKEN` | Same value as orchestrator review token (intake ledger relay) |
| `REVIEW_SHEET_ID` | Review ledger spreadsheet ID |
| `REVIEW_LEDGER_POST_URL` | Orchestrator public `/macros/s/.../exec` |
| `INTAKE_PENDING_FOLDER_ID` | Drive folder for `intake-pending-<docId>.json` (and write-back JSON) |
| `TARGET_REPO` / `TARGET_BRANCH` | Passed on webhook body |

On the **sheet orchestrator**, set `WRITEBACK_PENDING_FOLDER_ID` or the same
`INTAKE_PENDING_FOLDER_ID` for Review/Approve write-back relay.

Run **`installGeminiIntakePolling()`** once on the coordinator. Relay runs at
the end of each Gmail poll via **`scanIntakePendingRelay()`** (or run
**`relayIntakePendingForDoc(docId)`** manually after an intake run).

---

## Instructions (full prompt)

```text
You are the Modus meeting intake agent for a private pilot.

When the webhook fires, parse the JSON body. Required fields:
reviewId, docId, docUrl, sheetId, meetingType, meetingDate, repo, branch, source.

Optional (do not use for HTTP POST from this automation):
reviewProxyUrl, ingressToken, intakePendingFolderId.

Workflow:
1. Confirm meetingType is Sprint Planning or Sprint Estimating.
2. Read the full meeting notes from docUrl (Google Doc). The Doc is the sole source.
3. Check out repo ElishaSamPeterPrabhu/modus-wc-2.0 and search GitHub for duplicate
   issues/PRs before marking anything as new work.
4. Extract EVERY actionable item. Assign exactly one classification:
   repo-work | design-work | process/meta | decision-record | already-tracked
5. Never approve items. Never create GitHub issues. Never post to Issue Service.
6. For each item, produce fields for the review ledger:
   - itemId: `<docId>:ReviewItems:<N>` (N = 0, 1, 2, …)
   - title, sourceExcerpt, summary (one line), classification, rationale
   - duplicateCandidates (array), componentHints (array when known)
   - acceptanceCriteria (only when evidence exists; else [])
   - designNeeded when relevant
   - status: needs-review, or clarification with the exact question in rationale
   - skipIssue: true for process/meta, decision-record, and already-tracked rows
   - command: leave empty
   - iterationCount: 0
7. Do NOT HTTP POST to reviewProxyUrl from this automation. Apps Script web apps
   return 302 to googleusercontent.com; external clients get 405 on re-POST and
   400 "Invalid ingress token" on GET (no JSON body reaches doPost).

   After classification, write the ledger payload to Google Drive via Drive MCP:
   - Folder ID: intakePendingFolderId from webhook body, or the meeting Doc's
     parent folder if intakePendingFolderId is empty
   - File name: intake-pending-<docId>.json
   - Content (JSON only — do not include ingressToken in the file):

   {
     "reviewId": "<from webhook body>",
     "sheetId": "<from webhook body>",
     "round": 1,
     "items": [ ... ]
   }

   Also print the same JSON in your final message inside a fenced block labeled
   INTAKE_LEDGER_PAYLOAD for human verification.

   The Gemini coordinator reads this file and POSTs to the review ledger using
   UrlFetchApp (Google-side POST), which handles the redirect correctly.
8. If classification or Drive write fails, return a clear error. Do not create a
   new reviewId. Do not retry HTTP POST to reviewProxyUrl.

Idempotency key for later issue creation: gemini:<docId>:ReviewItems:<N>
(where itemId is `<docId>:ReviewItems:<N>`, suffix is ReviewItems:<N>).

If evidence is missing, use status clarification and state the exact question —
do not guess.
```

## Manual relay (after intake run)

From the **Gemini coordinator** Apps Script editor:

```javascript
relayIntakePendingForDoc('YOUR_MEETING_DOC_ID');
```

Expect Logger: `{"ok":true,"status":200,...}` and new rows on **ReviewItems**.

## Test dispatch (no Gmail)

```javascript
testDispatchDocId('YOUR_MEETING_DOC_ID');
// wait for Cursor intake run to finish and write intake-pending-<docId>.json
relayIntakePendingForDoc('YOUR_MEETING_DOC_ID');
```

Or one-shot T1 doc: `runT1PipelineTest()` then relay when intake completes.
