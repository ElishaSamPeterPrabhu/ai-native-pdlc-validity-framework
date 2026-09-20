# Interactive pilot demo (operator script)

**Deep links:** [`demo-workflow-links.md`](demo-workflow-links.md)

**Branch:** `cursor/cloud-agent-1787121861002-xrufz`  
**Repo:** https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework  
**Hub:** [`dashboard/sheet-pilot-map.html`](../../dashboard/sheet-pilot-map.html)

Out of scope: official Issue Scaffolding `80b1f7a5`, Design-Research automation, n8n, Apps Script editor during the show.

## Live links

| Asset | URL |
| --- | --- |
| Review ledger | https://docs.google.com/spreadsheets/d/1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4/edit |
| Map (local) | `python dashboard/server.py --port 8600` then http://localhost:8600/sheet-pilot-map.html |
| Map (GitHub) | https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/cursor/cloud-agent-1787121861002-xrufz/dashboard/sheet-pilot-map.html |
| [Pilot] Meeting Intake | https://cursor.com/t/trimble/automations/b1b60664-b000-11f1-bf4b-42ffb4d10ea7 |
| [Pilot] Review | https://cursor.com/t/trimble/automations/e3195783-b00b-11f1-bf4b-42ffb4d10ea7 |
| [Pilot] Approve | https://cursor.com/t/trimble/automations/8a65434d-b03e-11f1-bf4b-42ffb4d10ea7 |
| [PILOT] Issue Scaffolding | https://cursor.com/t/trimble/automations/288c955b-aaad-11f1-b532-320a589b8025 |
| Figma skills | [`docs/design-enablement/figma-agent/README.md`](../design-enablement/figma-agent/README.md) |

## Sheet — presenter columns

Show on **ReviewItems:** `title`, `classification`, `status`, `reviewerComment`, `cursorComment`, `issueUrl`.

Hide for the room: `itemId`, `round`, `command`, `iterationCount`, `skipIssue`, `issueNumber`, `updatedAt`. Hide tab **ReviewItemsDetail**. Keep **Controls** and **Issues**.

To apply polish after pasting the latest orchestrator: run **`applyDemoPresentationFormatting()`** once in Apps Script (not during the demo). Issue URLs become clickable links; ops columns stay hidden.

Optional backup (if you do not paste the script): **Data → Filter views → Create new filter view**, name it `Demo`, hide the same ops columns. Do not delete test rows; freeze header and leave `ReviewItems:0` as do-not-touch.

**Presenter data:** one completed row with `issueUrl` (walk this), plus one **fresh** row with empty `issueUrl` only if you need a live B1. Hide T3 clutter (`1Mb2yw…:ReviewItems:2/3/4`) via filter view rather than deleting.

Live trigger stays **Controls!B1** only (`review` / `approve`). Do not re-deploy the Web App during the show.

## Apps Script (preflight only)

You do **not** run the Script editor in the room. Confirm beforehand:

```bash
curl -sL "https://script.google.com/macros/s/AKfycbx2ytZQabxL0UVVCt56zjbiklM6xvlSFvI8NTQXwmqzqHPw6q9x8-FPcsTR-QSXeFOawg/exec" | python3 -m json.tool
```

Pass: `configured: true`, `dispatchInFlight: false`.

Also confirm:

1. Latest orchestrator is the bound script (paste + **new Web App version** only in prep, not in the room).
2. `onEdit` on B1 and/or `installReviewTrigger()` poll is armed.
3. `Controls!B1` is empty.

If B1 sits idle, recover with `installReviewTrigger()` — that is a fix, not the show. Poll-only can take ~1 minute.

## Show a completed run vs run again

If review → approve → scaffolding already wrote `cursorComment` + `issueUrl`:

- **Show that.** Walk the row, Issues tab, GitHub issue, Cursor run.
- **Do not** type `approve` on the same row. Idempotency skips a second issue.

Live B1 only on a **new** row with empty `issueUrl`. Figma skills should be run live (chat does not persist like the sheet).

## 15–25 minutes

| Minutes | Beat |
| --- | --- |
| 0–3 | Open the map. Private pilot, no n8n, human gate is B1, only `288c955b` creates issues. |
| 3–8 | **Figma (parallel, not sheet-triggered):** select → `/modus-accessibility-check` or `/modus-design-assist`. |
| 8–18 | **Sheet:** walk a completed row, **or** `review` then `approve` on a fresh row. |
| 18–22 | Optional: Dev → QA exists on the product repo — do not open official `80b1f7a5`. |
| 22–25 | Close: designers in Figma Agents; engineering on sheet + pilot scaffolding. |

## Gemini grounding

Attach the repo on branch `cursor/cloud-agent-1787121861002-xrufz`. Use this runbook, the map `links` object, and [`cursor-docs-review-workflow.md`](../chat-bots/cursor-docs-review-workflow.md). Do not invent official automation IDs.
