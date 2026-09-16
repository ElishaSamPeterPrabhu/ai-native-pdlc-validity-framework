---
name: meeting-review-intake
description: Classify Gmail/Calendar meeting notes into a Google Docs review ledger without creating issues automatically.
---

# Meeting review intake

Use this skill for approved Modus Sprint Planning or Sprint Estimating intake.

1. Validate the Gmail subject and Calendar occurrence against the configured
   Modus series allowlist.
2. Fetch the linked meeting Doc when the email is incomplete.
3. Preserve every actionable-looking item and assign exactly one rubric bucket:
   `repo-work`, `design-work`, `process/meta`, `decision-record`, or
   `already-tracked`.
4. Search repository context and existing issues before calling an item new.
5. Write classified items to Drive as `intake-pending-<docId>.json` (or return
   `INTAKE_LEDGER_PAYLOAD` JSON). The Gemini coordinator relays to the Google
   Sheet review ledger via `UrlFetchApp`; do not HTTP POST to Apps Script from
   Cursor cloud.
6. Never mark an item approved and never create an issue during intake.
   Issues are created only after Controls B1 `approve` → Approve automation →
   Issue Service → Issue Scaffolding.

Use `gemini:<meetingDocId>:ReviewItems:<N>` as the stable idempotency key when
`itemId` is `<meetingDocId>:ReviewItems:<N>`. If required evidence is missing,
write `clarification` and the exact question instead of guessing.

The sheet orchestrator owns ledger rows after coordinator relay. This skill
returns a structured payload; it does not invent a second storage format or
bypass the shared Issue Service.

