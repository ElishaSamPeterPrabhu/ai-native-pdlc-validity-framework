# Sheet-led pipeline test runbook

Repeatable matrix for validating intake → review → approve → scaffolding → write-back
without product implementation. See also
[`cursor-docs-review-workflow.md`](cursor-docs-review-workflow.md) deploy checklist.

**Frozen row (never re-approve):** `1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:0`

## Preconditions

| Check | How | Pass |
|-------|-----|------|
| Orchestrator deployed | Paste [`cursor-sheet-review-orchestrator.gs`](apps-script/cursor-sheet-review-orchestrator.gs) + new Web App version | `doGet` → `configured: true` |
| Write-back Drive folder | On orchestrator: `WRITEBACK_PENDING_FOLDER_ID` or `INTAKE_PENDING_FOLDER_ID` (same folder as intake) | `scanWritebackPendingRelay()` finds files |
| Coordinator relay | Paste [`cursor-gemini-meeting-intake-coordinator.gs`](apps-script/cursor-gemini-meeting-intake-coordinator.gs); set `INTAKE_PENDING_FOLDER_ID` | `doGet` → `configured: true` |
| Write-back URL | `REVIEW_LEDGER_POST_URL` = public `/macros/s/.../exec` | Not `/a/macros/trimble.com/` |
| Automations saved | Glass | Approve enriched POST + 405 rules; Scaffolding multi-source + Drive MCP |
| Scaffolding creds | Approve env **or** Script Properties `ISSUE_SCAFFOLDING_WEBHOOK_*` | Approve run reaches Scaffolding (T0 proved env path) |
| Dispatch idle | `doGet` or Controls diagnostic | `dispatchInFlight: false` |
| Sheet baseline | Issues tab | One row for #48; loading row `approved` |

```bash
curl -sL "https://script.google.com/macros/s/AKfycbx2ytZQabxL0UVVCt56zjbiklM6xvlSFvI8NTQXwmqzqHPw6q9x8-FPcsTR-QSXeFOawg/exec" | python3 -m json.tool
```

## Seed synthetic rows (T3a/T3b/T3d)

From **Cursor Sheet Review Orchestrator** Apps Script editor:

1. Deploy latest [`cursor-sheet-review-orchestrator.gs`](apps-script/cursor-sheet-review-orchestrator.gs).
2. Run **`seedPilotTestRows()`** once.
3. Confirm log lists three itemIds and expected `gemini:<docId>:ReviewItems:N` keys.

| ID | itemId suffix | classification | skipIssue | Expected after approve |
|----|---------------|----------------|-----------|------------------------|
| T3a | `ReviewItems:2` | repo-work | FALSE | New GitHub issue; Issues tab one row |
| T3b | `ReviewItems:3` | repo-work | FALSE | `status: clarification`; no empty issueUrl |
| T3d | `ReviewItems:4` | process/meta | TRUE | Excluded from Approve payload |

### T3a detail JSON (ReferenceItemsDetail)

```json
{
  "sourceExcerpt": "Sprint Planning | Add disabled prop to button | modus-wc-button",
  "summary": "Expose a boolean disabled prop on modus-wc-button with accessible disabled state.",
  "designNeeded": false,
  "componentHints": ["modus-wc-button"],
  "acceptanceCriteria": [
    "disabled prop defaults to false",
    "When disabled, click handlers do not fire",
    "Host sets aria-disabled=true when disabled",
    "Visual style matches Modus disabled token (opacity/cursor)"
  ],
  "rationale": "Common control gap; aligns with Modus button patterns."
}
```

### T3b detail JSON

```json
{
  "sourceExcerpt": "Sprint Planning | Maybe fix spinner sizes",
  "summary": "Unclear spinner sizing request without acceptance criteria.",
  "designNeeded": false,
  "componentHints": ["modus-wc-loader"],
  "acceptanceCriteria": [],
  "rationale": "Thin intake item for clarification-path test."
}
```

## Execute order

1. Preconditions
2. `seedPilotTestRows()` (or manual rows above)
3. **T3a:** optional `Controls!B1=review` → human AC → `approve`
4. **T4a:** re-type `approve` on T3a after issue exists → skip POST
5. **T3b:** `approve` → Scaffolding `NEED CLARIFICATION`
6. **T3d:** `approve` → row excluded (no Scaffolding POST for skipIssue)
7. **T1:** new meeting Doc → coordinator `testDispatchDocId('<docId>')`
8. **T2:** `Controls!B1=review` on intake rows
9. **T3c** (optional): design-work row with staged Figma Drive folder
10. **T5:** audit Scaffolding Sources on T3a issue body
11. **T6 (Drive scaffolding result):** after approve, confirm
    `scaffolding-result-<slug>.json` in pending folder before expecting sheet
    write-back; Approve must not hang on GitHub-only poll

### T6 — Scaffolding result + approve write-back

After `Controls!B1=approve` on an isolated row:

1. Scaffolding run completes → **`scaffolding-result-<idempotencyKey-slug>.json`**
   in `WRITEBACK_PENDING_FOLDER_ID` / `INTAKE_PENDING_FOLDER_ID`.
2. Approve reads result (`verdict`, `issueUrl`, `clarificationQuestion`).
3. Approve writes **`writeback-approve-meeting-<docId>-r<round>.json`**.
4. Orchestrator `scanWritebackPendingRelay()` (or next poll) → Controls
   `writeback_relayed approve …`.

**Phase A (tooltip):** `1AMbbKr…:ReviewItems:0` with reviewerComment → clarification
or issue via Drive.

**Phase B (clean AC):** run `seedT1HappyPathRow()` → `ReviewItems:3` with T3a-style
disabled-button AC → expect `verdict: issue_created` with no clarification.

```javascript
isolateT1TooltipForApprove();  // Phase A
seedT1HappyPathRow();
isolateSingleRowForApprove('1AMbbKrWc8fmS2CI_jzwoC7KvdygL4Wz9kY3Y861gjYg:ReviewItems:3');  // Phase B
restoreIsolatedApproveSkips();  // after tests
```

## T1 intake (new Doc required)

Coordinator dedupes by `docId`. Copy meeting notes to a **new Google Doc** with bullets:

- One `repo-work` item with component hint
- One `design-work` or `process/meta` item
- One thin `repo-work` for later clarification

Run from **Gemini coordinator** project: `testDispatchDocId('<newDocId>')` or `runT1PipelineTest()`.

**Coordinator properties:** `CURSOR_REVIEW_INGRESS_TOKEN` must match orchestrator;
`INTAKE_PENDING_FOLDER_ID` must point at a Drive folder the intake agent can write.

**Flow:** Intake classifies → writes `intake-pending-<docId>.json` → coordinator
`relayIntakePendingForDoc(docId)` or automatic `scanIntakePendingRelay()` after
Gmail poll. Do **not** expect Cursor to POST directly to `/exec`.

**Pass:** ≥2 new ReviewItems rows; `reviewId: meeting:<docId>`; no GitHub issues.

## Pass/fail ledger

| ID  | Date | Agent run (bc-*) | GitHub issue | idempotencyKey correct | Issues rows | Notes |
| T0  | 2026-09-14 | bc-868574f8 | #48 | old doubled (OK) | 1 | baseline |
| T3a | 2026-09-15 | bc-52ce005e (approve) | [#49](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49) | scaffold body doubled; sheet upsert OK | 2 (#48+#49) | happy path |
| T4a | 2026-09-15 | bc-54231524 | none new | n/a | 2 | skip second POST |
| T3b | 2026-09-15 | bc-52ce005e | none | n/a | clarification row | NEED CLARIFICATION |
| T3d | 2026-09-15 | bc-52ce005e | n/a | n/a | n/a | skipIssue excluded |
| T1  | 2026-09-15 | bc-dc82bb95 | n/a | n/a | n/a | external POST 302/405; use Drive relay + `relayIntakePendingForDoc` |
| T2  | 2026-09-15 | bc-ecd79503 | n/a | n/a | n/a | review on T1 rows |
| T5  | 2026-09-15 | (scaffold on T3a) | #49 Sources | see #49 body | n/a | Drive+code+blueprint cited |

## Non-goals

- Do **not** implement or close GitHub #48
- Do **not** re-approve `ReviewItems:0`
- Do **not** run `pilotPrepareLoadingRow()` on rows with existing issues
