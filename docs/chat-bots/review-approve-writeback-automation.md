# Review and Approve write-back (Drive relay)

Cursor cloud cannot reliably HTTP POST to Apps Script `/exec` (302 → 405).
Review and Approve automations must **not** POST to `reviewProxyUrl`. Write a
JSON file to Drive; the **sheet orchestrator** applies it on the next poll via
`scanWritebackPendingRelay()`.

Use the **same Drive folder** as intake (`INTAKE_PENDING_FOLDER_ID` on
coordinator). On the **orchestrator**, set either:

- `WRITEBACK_PENDING_FOLDER_ID`, or
- `INTAKE_PENDING_FOLDER_ID` (fallback)

---

## Review automation prompt block

Replace the HTTP POST write-back section with:

```text
Do NOT HTTP POST to reviewProxyUrl from this automation (Apps Script 302/405).

After processing all webhook items, write one ledger write-back file to Google
Drive via Drive MCP:

- Folder ID: writebackPendingFolderId from webhook body
- File name: writeback-review-<reviewId>-r<round>.json
  where reviewId has ":" replaced by "-" (e.g. meeting-1AMbbKr...-r2.json)
- Content (JSON only — no ingressToken):

{
  "mode": "review_writeback",
  "reviewId": "<from webhook>",
  "sheetId": "<from webhook>",
  "round": <from webhook>,
  "itemUpdates": [
    {
      "itemId": "...",
      "command": "",
      "status": "needs-review|clarification|...",
      "iterationCount": <new count>,
      "cursorComment": "<max 320 chars>"
    }
  ]
}

Also print the same JSON in a fenced block labeled REVIEW_WRITEBACK_PAYLOAD.

The sheet orchestrator polls the folder and applies updates in-process.
Do not call Issue Service. Do not create GitHub issues.
```

**Exact filename helper:** for `reviewId` `meeting:DOCID` and `round` 2:

```text
writeback-review-meeting-DOCID-r2.json
```

---

## Approve automation prompt block

Replace the HTTP POST write-back section with:

```text
Do NOT HTTP POST to reviewProxyUrl for sheet write-back (Apps Script 302/405).

After Scaffolding POST, poll Google Drive for the scaffolding result file (primary
signal). GitHub poll is optional backup only when verdict is issue_created.

After reading scaffolding-result (or timeout), write one ledger write-back file to
Google Drive via Drive MCP:

- Folder ID: writebackPendingFolderId from webhook body
- File name: writeback-approve-<reviewId>-r<round>.json
  (reviewId with ":" → "-", e.g. writeback-approve-meeting-DOCID-r2.json)
- Content (JSON only — no ingressToken):

{
  "mode": "review_writeback",
  "reviewId": "<from webhook>",
  "sheetId": "<from webhook>",
  "round": <from webhook>,
  "itemUpdates": [
    {
      "itemId": "...",
      "command": "",
      "status": "approved|clarification|failed",
      "iterationCount": <new count>,
      "issueNumber": "...",
      "issueUrl": "..."
    }
  ],
  "issueResults": [
    {
      "itemId": "...",
      "idempotencyKey": "gemini:...",
      "status": "created|clarification|failed",
      "issueNumber": "...",
      "issueUrl": "...",
      "createdAt": "<ISO>",
      "lastError": ""
    }
  ]
}

On success do not include cursorComment in itemUpdates.
Also print REVIEW_WRITEBACK_PAYLOAD fenced JSON.

The sheet orchestrator applies this on the next poll. Scaffolding webhook POST
from Cursor is unchanged (api2.cursor.sh — not Apps Script).
```

---

## Scaffolding result relay (Scaffolding → Approve)

Scaffolding runs asynchronously. Approve only receives `bc-*` from the webhook POST;
the verdict lives in the Scaffolding run output. **Scaffolding writes a result file;
Approve reads it before sheet write-back.**

### Scaffolding writes (after every run)

| Field | Value |
|-------|--------|
| **Folder** | `additional_context.resultFolderId` (Approve sets from `writebackPendingFolderId`) |
| **Filename** | `scaffolding-result-<slug>.json` where slug = idempotency key with `:` → `-` |
| **Tool** | Google Drive MCP `create_file` — same pending folder as write-back |

```json
{
  "idempotencyKey": "gemini:DOCID:ReviewItems:0",
  "itemId": "DOCID:ReviewItems:0",
  "verdict": "issue_created|need_clarification|skipped|error",
  "issueUrl": "https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/N",
  "issueNumber": "N",
  "clarificationQuestion": "Exact question from NEED CLARIFICATION block",
  "runId": "bc-…",
  "finishedAt": "2026-09-15T10:00:00.000Z"
}
```

| verdict | When |
|---------|------|
| `issue_created` | GitHub issue created |
| `need_clarification` | GAP CHECK still unresolved; no issue |
| `skipped` | Ineligible / skipIssue |
| `error` | Run failed |

### Approve reads (before writeback-approve file)

1. Forward `writebackPendingFolderId` to Scaffolding as `additional_context.resultFolderId`.
2. After Scaffolding POST, poll Drive for `scaffolding-result-<slug>.json`.
3. Poll every **30s**, max **4 attempts** (~2 min).
4. Map verdict → `itemUpdates` / `issueResults` (see Approve block above).
5. GitHub poll is **optional verify only** when `verdict` is `issue_created`.

**Pass:** Result file appears within ~2 min; Approve write-back reflects clarification
or issue without hanging on GitHub poll.

---

## Manual relay (orchestrator editor)

```javascript
scanWritebackPendingRelay();
```

Or after pasting a file into the folder, wait up to one poll interval (default 5 min)
or run `scanWritebackPendingRelay()` once.

**Pass:** Controls diagnostic `writeback_relayed`; file renamed to
`writeback-relayed-review-...`; `dispatchInFlight: false`.
