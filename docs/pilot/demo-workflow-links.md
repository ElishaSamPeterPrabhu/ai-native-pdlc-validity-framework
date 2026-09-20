# Demo presenter narrative (open in order)

Read **top to bottom** in the room. Operator timing and sheet polish: [`interactive-demo-runbook.md`](interactive-demo-runbook.md) · **Branch:** `cursor/cloud-agent-1787121861002-xrufz`

**Do not use in this demo:** official Issue Scaffolding `80b1f7a5`, Design-Research automation, legacy Chat intake `a970221a-8c0a-11f1-bf4b-42ffb4d10ea7`.

**Provenance:** Showcase [#49](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49) is **T3a** on sheet row `ReviewItems:2` with idempotency key `gemini:1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:2`. Rows were seeded via `seedPilotTestRows()` for the test matrix ([`pilot-test-runbook.md`](../chat-bots/pilot-test-runbook.md)); agent runs below are real. In the room: *same architecture, proven runs*—do not re-`approve` that row.

Agent run URL pattern: `https://cursor.com/t/trimble/agents/{bc-uuid}` (alias: `https://cursor.com/agents/{bc-uuid}`).

## Bookmarks (copy into browser folder)

```text
Gemini test doc:  https://docs.google.com/document/d/1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4/edit
Review ledger:    https://docs.google.com/spreadsheets/d/1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4/edit
Intake run:       https://cursor.com/t/trimble/agents/bc-8f4b8e56-6df7-46bf-9338-56dbb1fea141
Review r3 (:2):   https://cursor.com/t/trimble/agents/bc-b9524d5c-744b-4c71-962e-47f23a2881a2
Approve T3a:      https://cursor.com/t/trimble/agents/bc-52ce005e-b1de-49ea-a1b6-be6b0b11e5ad
Scaffold T3a:     https://cursor.com/t/trimble/agents/bc-a842b909-b018-4238-b308-85b876d568fe
Write-back Drive: https://drive.google.com/drive/folders/1UT7-aIiKT3bSrelmyUM4mI_e3imNGpqr
Issue #49:        https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49
PR #42:           https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42
Dev run #42:      https://cursor.com/t/trimble/agents/bc-65dc91fc-b4a6-4657-b25d-e559ac558358
QA pass #42:      https://cursor.com/t/trimble/agents/bc-8cd16c11-18cb-4d99-9148-30f45b2a124a
PR #34:           https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34
QA fail #34:      https://cursor.com/t/trimble/agents/bc-fdcb9904-68dc-4abe-9671-2e94197ff1de
```

---

## Act A — Meeting notes → GitHub issue #49 (pilot sheet path)

| # | Say | Open | Agent run | If link fails |
| --- | --- | --- | --- | --- |
| A1 | “Work starts in meeting notes—not in GitHub.” | [Gemini test doc `1Mb2yw…`](https://docs.google.com/document/d/1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4/edit) | — | — |
| A2 | *(Optional)* “Coordinator forwards notes to Meeting Intake.” | [Coordinator Apps Script](https://script.google.com/home/projects/1zn-2eits9Ld5chLZKMykFAc7o4xKtUPXuaoUS9TyQcdngT1RGGaxMirN/edit) · [`cursor-gemini-meeting-intake-coordinator.gs`](../chat-bots/apps-script/cursor-gemini-meeting-intake-coordinator.gs) | — | — |
| A3 | “Intake **classifies**; it does not create issues.” | [Pilot Meeting Intake](https://cursor.com/t/trimble/automations/b1b60664-b000-11f1-bf4b-42ffb4d10ea7) | Primary: [bc-8f4b8e56](https://cursor.com/t/trimble/agents/bc-8f4b8e56-6df7-46bf-9338-56dbb1fea141) · Alt T1 partial: [bc-dc82bb95](https://cursor.com/t/trimble/agents/bc-dc82bb95-58d1-4296-80f1-381c86f06c29) | [Intake Run History](https://cursor.com/t/trimble/automations/b1b60664-b000-11f1-bf4b-42ffb4d10ea7/runs) → **Sep 15** successful dispatch row → **View details** |
| A4 | “Items land on the **review ledger**—reviewer comment + Cursor comment, no issue yet.” | [Ledger `1et7Nna…`](https://docs.google.com/spreadsheets/d/1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4/edit) tab **ReviewItems** row **`ReviewItems:2`** (disabled button) | — | — |
| A5 | “Review automation writes **`cursorComment`**; I still own approve.” | [Pilot Review](https://cursor.com/t/trimble/automations/e3195783-b00b-11f1-bf4b-42ffb4d10ea7) | **r3 / row :2:** [bc-b9524d5c](https://cursor.com/t/trimble/agents/bc-b9524d5c-744b-4c71-962e-47f23a2881a2) · Optional T2: [bc-ecd79503](https://cursor.com/t/trimble/agents/bc-ecd79503-1bf0-4a23-ac82-b9ab6e5b8bdc) | [Review Run History](https://cursor.com/t/trimble/automations/e3195783-b00b-11f1-bf4b-42ffb4d10ea7/runs) → **Sep 15:** **1st row** 3:14 PM (r3); **2nd row** 2:57 PM (T2) |
| A6 | “Human gate: I typed **`approve`** on **Controls!B1**.” *(Walk completed state; do not fire again on :2.)* | Same sheet → tab **Controls** cell **B1** | — | — |
| A7 | “Approve POSTs **pilot scaffolding** and Drive write-back—not n8n.” | [Pilot Approve](https://cursor.com/t/trimble/automations/8a65434d-b03e-11f1-bf4b-42ffb4d10ea7) | T3a → #49: [bc-52ce005e](https://cursor.com/t/trimble/agents/bc-52ce005e-b1de-49ea-a1b6-be6b0b11e5ad) | [Approve Run History](https://cursor.com/t/trimble/automations/8a65434d-b03e-11f1-bf4b-42ffb4d10ea7/runs) → scroll past Sep 18 rows → **Sep 15, 3:23 PM, ~17m** (T3a batch) |
| A8 | “Only **`288c955b`** creates/updates the GitHub issue from this path.” | [PILOT Issue Scaffolding](https://cursor.com/t/trimble/automations/288c955b-aaad-11f1-b532-320a589b8025) | T3a: [bc-a842b909](https://cursor.com/t/trimble/agents/bc-a842b909-b018-4238-b308-85b876d568fe) · Sibling: [bc-13fe644e](https://cursor.com/t/trimble/agents/bc-13fe644e-79db-4317-ba8e-3d9eec782f01) | [Scaffolding Run History](https://cursor.com/t/trimble/automations/288c955b-aaad-11f1-b532-320a589b8025/runs) → **Sep 15** ~**1m** success just after T3a approve |
| A9 | “Relay: JSON in Drive → orchestrator → **Issues** tab + `issueUrl`.” | [Write-back folder](https://drive.google.com/drive/folders/1UT7-aIiKT3bSrelmyUM4mI_e3imNGpqr) · `scaffolding-result-*.json`, `writeback-approve-*.json` ([`scaffolding-sheet-test-execution.md`](scaffolding-sheet-test-execution.md)) | — | — |
| A10 | “Sheet-approved scaffold on GitHub.” | [#49 — Add disabled prop to button](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49) | — | Sources section (T5 in runbook) |

**T4a idempotency** (re-approve, no second issue): [bc-54231524](https://cursor.com/t/trimble/agents/bc-54231524-8ead-4deb-8bc7-992962aa9ed8).

---

## Act B — Pilot sheet vs engineering loop (PR + agents)

**Say:** “Sheet pilot uses **`288c955b`**. Product engineering already runs **Dev + QA** on the fork—here’s broken vs closed loop.”

| # | Say | Open | Agent run | If link fails |
| --- | --- | --- | --- | --- |
| B1 | “After interventions: Dev stop-boundary → QA fail → repair → **QA pass**.” | [PR #42](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42) | Dev: [bc-65dc91fc](https://cursor.com/t/trimble/agents/bc-65dc91fc-b4a6-4657-b25d-e559ac558358) · QA pass: [bc-8cd16c11](https://cursor.com/t/trimble/agents/bc-8cd16c11-18cb-4d99-9148-30f45b2a124a) | Dev: [Dev Run History](https://cursor.com/t/trimble/automations/69f213ff-4748-4bed-a065-9ba8b97d6bfe/runs) · QA: [QA Run History](https://cursor.com/t/trimble/automations/aac94e20-8523-48e4-a239-26daa40f1675/runs) → match PR #42 / `exp/28-checkbox` in run summary |
| B2 | “Baseline: QA **FAILED**, no repair—intentional before picture.” | [PR #34](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34) | QA fail: [bc-fdcb9904](https://cursor.com/t/trimble/agents/bc-fdcb9904-68dc-4abe-9671-2e94197ff1de) | [QA Run History](https://cursor.com/t/trimble/automations/aac94e20-8523-48e4-a239-26daa40f1675/runs) → **Older** until run mentions PR **#34** or branch `exp/30-menu-item-end-icon` |
| B3 | “Scores and timeline if PR thread is thin.” | [`data/validity-report.md`](../../data/validity-report.md) · [`paper/modus-pilot-abstract-summary.md`](../../paper/modus-pilot-abstract-summary.md) | — | — |

Dev repairs on `qa-failed` for the pilot story (not Fix Agent)—see [`harness/CONSOLE-TRIGGERS.md`](../../harness/CONSOLE-TRIGGERS.md).

---

## Appendix — optional beats

### Map hub

- Local: `python dashboard/server.py --port 8600` → [sheet-pilot-map.html](http://localhost:8600/sheet-pilot-map.html)
- GitHub: [sheet-pilot-map.html](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/cursor/cloud-agent-1787121861002-xrufz/dashboard/sheet-pilot-map.html)

### Figma (parallel, not sheet-triggered)

- [`docs/design-enablement/figma-agent/README.md`](../design-enablement/figma-agent/README.md)

### Orchestrator preflight (not in-room)

```bash
curl -sL "https://script.google.com/macros/s/AKfycbx2ytZQabxL0UVVCt56zjbiklM6xvlSFvI8NTQXwmqzqHPw6q9x8-FPcsTR-QSXeFOawg/exec" | python3 -m json.tool
```

Pass: `configured: true`, `dispatchInFlight: false`.

### Sanity — row ↔ issue (do not re-approve showcase)

| Sheet row | idempotencyKey | GitHub | Pilot test |
| --- | --- | --- | --- |
| `1Mb2yw…:ReviewItems:2` (disabled button) | `gemini:1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:2` | [#49](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/49) | T3a — [bc-52ce005e](https://cursor.com/t/trimble/agents/bc-52ce005e-b1de-49ea-a1b6-be6b0b11e5ad) |
| `1Mb2yw…:ReviewItems:0` (loading state) | `gemini:…:ReviewItems:0` | [#48](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/48) | **Frozen** — never re-approve |

Canonical ledger: `1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4`.

### Automation list URLs (no run)

| Automation | URL |
| --- | --- |
| [Pilot] Meeting Intake | https://cursor.com/t/trimble/automations/b1b60664-b000-11f1-bf4b-42ffb4d10ea7 |
| [Pilot] Review | https://cursor.com/t/trimble/automations/e3195783-b00b-11f1-bf4b-42ffb4d10ea7 |
| [Pilot] Approve | https://cursor.com/t/trimble/automations/8a65434d-b03e-11f1-bf4b-42ffb4d10ea7 |
| [PILOT] Issue Scaffolding | https://cursor.com/t/trimble/automations/288c955b-aaad-11f1-b532-320a589b8025 |
| Dev Agent | https://cursor.com/t/trimble/automations/69f213ff-4748-4bed-a065-9ba8b97d6bfe |
| QA Agent | https://cursor.com/t/trimble/automations/aac94e20-8523-48e4-a239-26daa40f1675 |
