# Issue Scaffolding v2 — sheet-pilot test execution

Run after pasting **Issue Scaffolding v2 + pilot append** into `[PILOT] Modus Issue Scaffolding` (`288c955b`).

## Preflight (automated + manual)

```bash
./scripts/scaffolding_sheet_pilot_test.sh
```

| Check | Pass criteria |
|-------|----------------|
| Orchestrator | `configured: true`, `dispatchInFlight: false` |
| Scaffolding creds | `issueScaffoldingUrlSet` + `issueScaffoldingTokenSet` **or** Approve Cloud Agent env `ISSUE_SCAFFOLDING_WEBHOOK_*` |
| Automations saved | v2 + pilot append on `288c955b`; approve block on Approve automation |

If orchestrator shows `issueScaffoldingUrlSet: false`:

1. Run `configureScaffoldingWebhookUrl()` in Apps Script editor
2. Add `ISSUE_SCAFFOLDING_WEBHOOK_TOKEN` in Script Properties (Bearer from webhook `288c955b`)

## Execute (Apps Script editor)

Deploy latest [`cursor-sheet-review-orchestrator.gs`](../chat-bots/apps-script/cursor-sheet-review-orchestrator.gs) first.

**Recommended (blocking poll, ~2 min each):**

```javascript
runScaffoldingSheetTestPhaseAWithPoll();  // PASS or throws
runScaffoldingSheetTestPhaseBWithPoll();  // PASS or throws
runScaffoldingSheetTestPhaseC_T4aIdempotency();
runScaffoldingSheetTestCleanup();
```

### Phase A — clarification (T3b)

```javascript
runScaffoldingSheetTestPhaseA_T3bClarify();
pollScaffoldingResultAndRelayWriteback('gemini:1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:3');
```

**Pass:** `result.verdict === 'need_clarification'`, `clarificationQuestion` set, no `issueUrl`. Sheet row `status: clarification`.

### Phase B — happy path (T3a)

```javascript
runScaffoldingSheetTestPhaseB_T3aHappy();
pollScaffoldingResultAndRelayWriteback('gemini:1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:2');
```

**Pass:** `verdict === 'issue_created'`, new GitHub issue with 8 sections + **Sources** (manifest/MCP cites). Sheet shows `issueUrl`.

### Phase C — idempotency (T4a, optional)

```javascript
runScaffoldingSheetTestPhaseC_T4aIdempotency();
```

**Pass:** Approve run skips second Scaffolding POST; no duplicate issue.

### Cleanup

```javascript
runScaffoldingSheetTestCleanup();
```

## Write-back folder

Pending JSON folder ID (from prior pilot): `1UT7-aIiKT3bSrelmyUM4mI_e3imNGpqr`

Expected files per phase:

| Phase | scaffolding-result file |
|-------|-------------------------|
| A | `scaffolding-result-gemini-1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4-ReviewItems-3.json` |
| B | `scaffolding-result-gemini-1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4-ReviewItems-2.json` |

## v2 re-test log

| Phase | Date | bc-* run | verdict | issue | Notes |
|-------|------|----------|---------|-------|-------|
| A T3b | | | | | |
| B T3a | | | | | |
| C T4a | | | | | |

Prior baseline (pre-v2 paste): see [`pilot-test-runbook.md`](../chat-bots/pilot-test-runbook.md) §Pass/fail ledger (2026-09-15).

## Exit — move to next work

All of: Phase A pass, Phase B pass, write-back relay, cleanup done.

Then: Design-Research automation (PR3) → upstream PR `upstream/pr1-pr2-capabilities`.
