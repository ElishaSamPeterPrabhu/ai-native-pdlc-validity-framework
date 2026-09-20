# Demo workflow links (open in order)

**Deep links for the room.** Operator script: [`interactive-demo-runbook.md`](interactive-demo-runbook.md) · Hub: [`dashboard/sheet-pilot-map.html`](../../dashboard/sheet-pilot-map.html)

**Do not use in this demo:** official Issue Scaffolding `80b1f7a5`, Design-Research automation, legacy Chat intake `a970221a-8c0a-11f1-bf4b-42ffb4d10ea7`.

Agent run URL pattern: `https://cursor.com/t/trimble/agents/{bc-uuid}` (same as `https://cursor.com/agents/{bc-uuid}`).

---

## Act 1 — Sheet pilot (showcase: issue [#49](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49))

Walk a **completed** row; do not re-`approve` the same idempotency key.

| Step | What to say | Open this | Evidence on screen |
| --- | --- | --- | --- |
| 0 | “This map is the private pilot hub—sheet gate, pilot scaffolding only, Figma in parallel.” | Local: `python dashboard/server.py --port 8600` → [sheet-pilot-map.html](http://localhost:8600/sheet-pilot-map.html) · GitHub: [sheet-pilot-map.html](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/cursor/cloud-agent-1787121861002-xrufz/dashboard/sheet-pilot-map.html) | Wired Review / Approve / Orchestrator; Figma node |
| 1 | “Designers use Figma Agent skills—not sheet-triggered.” | [`docs/design-enablement/figma-agent/README.md`](../design-enablement/figma-agent/README.md) | Skills in Cursor Agents panel |
| 2 | “Human ledger: one row already has `issueUrl`.” | [Review ledger](https://docs.google.com/spreadsheets/d/1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4/edit) — **ReviewItems**, **Issues**, **Controls!B1** | Presenter columns: title, classification, status, reviewerComment, cursorComment, issueUrl |
| 3 | “Orchestrator is configured before we enter the room.” | `curl -sL` → [orchestrator `/exec`](https://script.google.com/macros/s/AKfycbx2ytZQabxL0UVVCt56zjbiklM6xvlSFvI8NTQXwmqzqHPw6q9x8-FPcsTR-QSXeFOawg/exec) | `configured: true`, `dispatchInFlight: false` |
| 4 | *(Optional)* “Meeting notes can feed intake via Gemini coordinator.” | Coordinator: [Apps Script project](https://script.google.com/home/projects/1zn-2eits9Ld5chLZKMykFAc7o4xKtUPXuaoUS9TyQcdngT1RGGaxMirN/edit) · source [`cursor-gemini-meeting-intake-coordinator.gs`](../chat-bots/apps-script/cursor-gemini-meeting-intake-coordinator.gs) · test doc `1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4` ([`pilot-test-runbook.md`](../chat-bots/pilot-test-runbook.md)) | Classified items → sheet rows (no GitHub) |
| 5 | “Meeting Intake classifies; it does not open issues.” | Automation: [Pilot Meeting Intake](https://cursor.com/t/trimble/automations/b1b60664-b000-11f1-bf4b-42ffb4d10ea7) · **Run (T1 E2E):** [bc-8f4b8e56](https://cursor.com/t/trimble/agents/bc-8f4b8e56-6df7-46bf-9338-56dbb1fea141) · *(partial ingress relay)* [bc-dc82bb95](https://cursor.com/t/trimble/agents/bc-dc82bb95-58d1-4296-80f1-381c86f06c29) | 4 items classified; sheet upsert path documented in runbook |
| 6 | “Review round writes `cursorComment` only—human still approves on B1.” | Automation: [Pilot Review](https://cursor.com/t/trimble/automations/e3195783-b00b-11f1-bf4b-42ffb4d10ea7) · **Run (T2):** [bc-ecd79503](https://cursor.com/t/trimble/agents/bc-ecd79503-1bf0-4a23-ac82-b9ab6e5b8bdc) · **Run (r3 relay, disabled row):** [bc-b9524d5c](https://cursor.com/t/trimble/agents/bc-b9524d5c-744b-4c71-962e-47f23a2881a2) | Controls: `writeback_relayed review r3`; row `:ReviewItems:2` has cursorComment |
| 7 | “Approve POSTs pilot scaffolding—no n8n Issue Service.” | Automation: [Pilot Approve](https://cursor.com/t/trimble/automations/8a65434d-b03e-11f1-bf4b-42ffb4d10ea7) · **Run (T3a → #49):** [bc-52ce005e](https://cursor.com/t/trimble/agents/bc-52ce005e-b1de-49ea-a1b6-be6b0b11e5ad) | Scaffolding webhook + Drive write-back; idempotent batch |
| 8 | “Only `288c955b` creates GitHub issues from the sheet path.” | Automation: [PILOT Issue Scaffolding](https://cursor.com/t/trimble/automations/288c955b-aaad-11f1-b532-320a589b8025) · **Run (T3a scaffold):** [bc-a842b909](https://cursor.com/t/trimble/agents/bc-a842b909-b018-4238-b308-85b876d568fe) | Issue body scaffold sections; dedupe/update to #49 |
| 9 | “Write-back lands in Drive; orchestrator relays to the sheet.” | [Write-back folder](https://drive.google.com/drive/folders/1UT7-aIiKT3bSrelmyUM4mI_e3imNGpqr) · pattern `scaffolding-result-*.json`, `writeback-approve-*.json` ([`scaffolding-sheet-test-execution.md`](scaffolding-sheet-test-execution.md)) | Issues tab + ReviewItems `approved` + `issueUrl` |
| 10 | “This is the sheet-approved disabled-button scaffold.” | [#49 — Add disabled prop to button](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49) | Matches ledger row; T3a happy path in [`pilot-test-runbook.md`](../chat-bots/pilot-test-runbook.md) |

**Idempotency demo (same approve batch, no second issue):** [bc-54231524](https://cursor.com/t/trimble/agents/bc-54231524-8ead-4deb-8bc7-992962aa9ed8) (T4a).

---

## Act 2 — Dev → QA loop (`trimble-oss/modus-wc-2.0`)

Narrative from [`data/validity-report.md`](../../data/validity-report.md): PR [#34](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34) loop broken (QA FAILED, no repair); PR [#42](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42) QA FAILED (lint) → Dev repair → **loop closed** (Fix Agent not required for pilot story—Dev repairs on `qa-failed` per [`harness/CONSOLE-TRIGGERS.md`](../../harness/CONSOLE-TRIGGERS.md)).

| Step | What to say | Open this | Evidence on screen |
| --- | --- | --- | --- |
| 11 | “Dev opens with stop-boundary in the PR body.” | [Dev Agent](https://cursor.com/t/trimble/automations/69f213ff-4748-4bed-a065-9ba8b97d6bfe) · **Run (PR #42):** [bc-65dc91fc](https://cursor.com/t/trimble/agents/bc-65dc91fc-b4a6-4657-b25d-e559ac558358) | PR #42 footer + command table |
| 12 | “Baseline: QA failed; nobody closed the loop.” | [PR #34](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34) | `## QA FAILED` (2026-07-20); missing npm scripts; `fix_iterations=0` |
| 13 | “QA Agent posts FAILED; no Fix in this baseline.” | [QA Agent](https://cursor.com/t/trimble/automations/aac94e20-8523-48e4-a239-26daa40f1675) · **Run (PR #34 QA):** [bc-fdcb9904](https://cursor.com/t/trimble/agents/bc-fdcb9904-68dc-4abe-9671-2e94197ff1de) | Failed checks in QA comment; label `qa-failed` |
| 14 | “After intervention: fail → repair → pass.” | [PR #42](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42) | First QA FAILED (lint); human/Dev fix comment; second QA PASSED |
| 15 | “Second QA round—the loop closes.” | Same QA automation · **Run (QA pass):** [bc-8cd16c11](https://cursor.com/t/trimble/agents/bc-8cd16c11-18cb-4d99-9148-30f45b2a124a) | `## QA PASSED` on PR #42 ([`paper/modus-pilot-abstract-summary.md`](../../paper/modus-pilot-abstract-summary.md) timeline) |

---

## Sanity — do not re-approve the showcase row

| Sheet row | idempotencyKey | GitHub | Pilot test |
| --- | --- | --- | --- |
| `1Mb2yw…:ReviewItems:2` (disabled button) | `gemini:1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:2` | [#49](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49) | T3a — approve [bc-52ce005e](https://cursor.com/t/trimble/agents/bc-52ce005e-b1de-49ea-a1b6-be6b0b11e5ad) |
| `1Mb2yw…:ReviewItems:0` (loading state) | `gemini:…:ReviewItems:0` | [#48](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/48) | **Frozen** — never re-approve |

Canonical ledger spreadsheet id: `1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4` (meeting doc ids in rows may still reference `1Mb2yw…` test doc).
