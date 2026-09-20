/**
 * Sheet-led Cursor review orchestrator.
 *
 * Review ledger lives in a Google Sheet (ReviewItems / ReviewItemsDetail / Issues).
 * Meeting notes can stay a separate Google Doc; link them in intake metadata.
 *
 * Required Script Properties:
 *   REVIEW_SHEET_ID
 *   CURSOR_REVIEW_CALLBACK_URL   (Controls B1=review)
 *   CURSOR_APPROVE_CALLBACK_URL  (Controls B1=approve)
 *   CURSOR_REVIEW_INGRESS_TOKEN  (Bearer for Review webhook + write-back)
 *   CURSOR_APPROVE_INGRESS_TOKEN (Bearer for Approve webhook + write-back)
 *
 * Legacy: CURSOR_INGRESS_TOKEN is accepted as a fallback for Review only.
 *
 * Optional:
 *   REVIEW_LEDGER_POST_URL (override write-back URL; defaults to this web app's /exec URL)
 *   REVIEW_SOURCE_ALLOWLIST (comma-separated spreadsheet IDs)
 *   REVIEW_POLL_MINUTES (1, 5, 10, 15, 30)
 *   DRY_RUN_REVIEW (true — skip Cursor POST and echo updates into the sheet)
 *   ISSUE_SCAFFOLDING_WEBHOOK_URL — passed on approve payloads when Cloud Agent
 *     env secrets are unavailable (Script Properties workaround)
 *   ISSUE_SCAFFOLDING_WEBHOOK_TOKEN — Bearer token for Scaffolding webhook
 *   WRITEBACK_PENDING_FOLDER_ID — Drive folder for Review/Approve write-back JSON
 *     (falls back to INTAKE_PENDING_FOLDER_ID when unset)
 *
 * Setup (dry-run):
 *   1. Set REVIEW_SHEET_ID (or run createReviewLedgerDemo to create one)
 *   2. Run installDryRunPolling once
 *   3. Type review or approve in Controls!B1 and wait up to ~1 minute
 *
 * Presenter polish (run once, not during a demo): applyDemoPresentationFormatting()
 *
 * Trigger: Controls!B1 only (review | approve | reject). Per-row command column
 * is leftover storage; it does not trigger.
 *
 * Column contract:
 *   reviewerComment — human notes, never triggers
 *   cursorComment   — Cursor write-back only (Review automation; not Approve)
 *   command         — leftover storage; not a trigger
 *   skipIssue       — TRUE excludes row from both review and approve payloads
 *   iterationCount  — increments each time Cursor processes the row
 *   status          — in-progress while a round is running
 *
 * Cursor is called at most once per typed B1 command. Polling with empty B1
 * does nothing.
 */

const TAB_REVIEW_ITEMS = 'ReviewItems';
const TAB_REVIEW_DETAIL = 'ReviewItemsDetail';
const TAB_ISSUES = 'Issues';
const TAB_CONTROLS = 'Controls';

const REVIEW_HEADERS = [
  'itemId', 'round', 'sourceExcerpt', 'classification', 'rationale',
  'duplicateCandidates', 'title', 'summary', 'owner', 'designNeeded',
  'acceptanceCriteria', 'status', 'skipIssue', 'reviewerComment', 'cursorComment',
  'command', 'iterationCount', 'issueStatus', 'issueNumber', 'issueUrl',
  'lastError', 'updatedAt',
];

const REVIEW_SURFACE_HEADERS = [
  'itemId', 'round', 'title', 'classification', 'status', 'skipIssue',
  'reviewerComment', 'cursorComment', 'command', 'iterationCount',
  'issueNumber', 'issueUrl', 'updatedAt',
];

const REVIEW_PAYLOAD_FIELDS = REVIEW_HEADERS.filter(
  (name) => REVIEW_SURFACE_HEADERS.indexOf(name) === -1
);

const TRIGGER_COMMANDS = ['@cursor-review', 'review', 'approve', 'reject'];
const CURSOR_COMMENT_MAX = 320;

const ISSUE_HEADERS = [
  'itemId', 'idempotencyKey', 'status', 'issueNumber', 'issueUrl',
  'createdAt', 'lastError', 'reviewComment',
];

/** meeting:<docId> → docId; otherwise empty string. */
function meetingDocIdFromReviewId(reviewId) {
  const value = String(reviewId || '').trim();
  const match = value.match(/^meeting:([^:]+)$/);
  return match ? match[1] : '';
}

/** Stable issue key: gemini:<docId>:<suffix> without doubling docId in itemId. */
function buildIdempotencyKey(reviewId, itemId) {
  const docId = meetingDocIdFromReviewId(reviewId);
  const rawItemId = String(itemId || '').trim();
  if (!docId || !rawItemId) return '';
  const prefix = `${docId}:`;
  const suffix = rawItemId.indexOf(prefix) === 0
    ? rawItemId.slice(prefix.length)
    : rawItemId;
  return `gemini:${docId}:${suffix}`;
}

function meetingDocUrlFromReviewId(reviewId) {
  const docId = meetingDocIdFromReviewId(reviewId);
  return docId ? `https://docs.google.com/document/d/${docId}/edit` : '';
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    const body = parseJsonBody(e);
    requireToken(body.ingressToken);
    const reviewId = String(body.reviewId || '').trim();
    const sheetId = String(body.sheetId || body.docId || '').trim();
    if (!reviewId || !sheetId) throw new Error('reviewId and sheetId are required');
    assertAllowedSpreadsheet(sheetId);

    const spreadsheet = SpreadsheetApp.openById(sheetId);
    ensureLedgerTabs(spreadsheet);
    if (String(body.mode || '').trim().toLowerCase() === 'review_writeback') {
      const result = applyReviewWritebackPayload(spreadsheet, body);
      return jsonResponse(result);
    }
    const items = Array.isArray(body.items) ? body.items : [];
    upsertItems(spreadsheet, items, Number(body.round || 1));
    writeState(spreadsheet, {
      reviewId,
      round: Number(body.round || 1),
      state: 'idle',
      lastProcessedRevision: String(body.reviewRevision || ''),
      claimedAt: '',
      claimedBy: '',
      lastError: null,
    });
    return jsonResponse({ ok: true, reviewId, itemCount: items.length });
  } catch (error) {
    return jsonResponse({ ok: false, error: safeError(error) }, 400);
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}

function doGet() {
  const config = readConfigStatus();
  let lastScan = { outcome: 'unknown', detail: 'REVIEW_SHEET_ID not configured', at: '' };
  let dispatchInFlight = false;
  if (config.reviewSheetIdSet) {
    try {
      const spreadsheet = openConfiguredSpreadsheet();
      dispatchInFlight = isDispatchInFlight(readDispatch(spreadsheet));
      lastScan = readScanDiagnostic(spreadsheet);
    } catch (error) {
      lastScan = { outcome: 'error', detail: safeError(error), at: new Date().toISOString() };
    }
  }
  return jsonResponse({
    ok: true,
    service: 'cursor-sheet-review-orchestrator',
    configured: config.configured,
    config,
    dryRun: isDryRunEnabled(),
    pollMinutes: normalizePollMinutes(getProperty('REVIEW_POLL_MINUTES') || 5),
    dispatchInFlight,
    lastScan,
  });
}

function readConfigStatus() {
  const reviewSheetIdSet = Boolean(getProperty('REVIEW_SHEET_ID'));
  const reviewCallbackUrlSet = Boolean(getProperty('CURSOR_REVIEW_CALLBACK_URL'));
  const approveCallbackUrlSet = Boolean(getProperty('CURSOR_APPROVE_CALLBACK_URL'));
  const reviewIngressTokenSet = Boolean(getReviewIngressToken());
  const approveIngressTokenSet = Boolean(getProperty('CURSOR_APPROVE_INGRESS_TOKEN'));
  const missing = [];
  if (!reviewSheetIdSet) missing.push('REVIEW_SHEET_ID');
  if (!reviewCallbackUrlSet) missing.push('CURSOR_REVIEW_CALLBACK_URL');
  if (!approveCallbackUrlSet) missing.push('CURSOR_APPROVE_CALLBACK_URL');
  if (!reviewIngressTokenSet) {
    missing.push('CURSOR_REVIEW_INGRESS_TOKEN (or legacy CURSOR_INGRESS_TOKEN)');
  }
  if (!approveIngressTokenSet) missing.push('CURSOR_APPROVE_INGRESS_TOKEN');
  return {
    reviewSheetIdSet,
    reviewCallbackUrlSet,
    approveCallbackUrlSet,
    reviewIngressTokenSet,
    approveIngressTokenSet,
    issueScaffoldingUrlSet: Boolean(getProperty('ISSUE_SCAFFOLDING_WEBHOOK_URL')),
    issueScaffoldingTokenSet: Boolean(getProperty('ISSUE_SCAFFOLDING_WEBHOOK_TOKEN')),
    reviewIngressTokenSource: getProperty('CURSOR_REVIEW_INGRESS_TOKEN')
      ? 'CURSOR_REVIEW_INGRESS_TOKEN'
      : (getProperty('CURSOR_INGRESS_TOKEN') ? 'CURSOR_INGRESS_TOKEN' : ''),
    missing,
    configured: missing.length === 0,
  };
}

function installReviewTrigger() {
  removeTriggersFor('scanReviewSheet');
  const minutes = normalizePollMinutes(getProperty('REVIEW_POLL_MINUTES') || 5);
  ScriptApp.newTrigger('scanReviewSheet')
    .timeBased()
    .everyMinutes(minutes)
    .create();
}

function installDryRunPolling() {
  const props = PropertiesService.getScriptProperties();
  props.setProperty('DRY_RUN_REVIEW', 'true');
  props.setProperty('REVIEW_POLL_MINUTES', '1');
  installReviewTrigger();
}

/**
 * One-click dry-run setup: create demo sheet, install 1-minute polling, log URL.
 * Run once from the Apps Script editor (no Cursor required).
 */
function setupDryRunTest() {
  const url = createReviewLedgerDemo();
  installDryRunPolling();
  Logger.log('Dry-run polling enabled (every 1 minute).');
  Logger.log(`Open sheet: ${url}`);
  Logger.log('Type review in Controls!B1 and wait up to 1 minute.');
  return url;
}

function scanReviewSheet() {
  try {
    runReviewScan(false, false);
  } finally {
    scanWritebackPendingRelay();
  }
}

function testReviewTriggerNow() {
  runReviewScan(true, true);
}

function applyReviewWritebackPayload(spreadsheet, body) {
  const reviewId = String(body.reviewId || '').trim();
  const itemUpdates = Array.isArray(body.itemUpdates) ? body.itemUpdates : [];
  const issueResults = Array.isArray(body.issueResults) ? body.issueResults : [];
  const round = Number(body.round || 1);
  applyItemUpdates(spreadsheet, itemUpdates, round);
  if (issueResults.length) appendIssueResults(spreadsheet, issueResults);
  writeState(spreadsheet, {
    ...readState(spreadsheet),
    reviewId,
    round,
    state: 'completed',
    lastProcessedRevision: String(body.reviewRevision || ''),
    claimedAt: '',
    claimedBy: '',
    lastError: null,
  });
  writeDispatch(spreadsheet, {
    inFlight: false,
    fingerprint: '',
    claimedAt: '',
    backgroundComposerId: '',
  });
  return {
    ok: true,
    mode: 'review_writeback',
    reviewId,
    itemCount: itemUpdates.length,
    issueCount: issueResults.length,
  };
}

function getWritebackPendingFolderId() {
  return getProperty('WRITEBACK_PENDING_FOLDER_ID') || getProperty('INTAKE_PENDING_FOLDER_ID');
}

function writebackPendingFileName(kind, reviewId, round) {
  const slug = String(reviewId || 'unknown')
    .replace(/:/g, '-')
    .replace(/[^\w-]/g, '');
  return `writeback-${kind}-${slug}-r${Number(round || 1)}.json`;
}

function writebackRelayedFileName(kind, reviewId, round) {
  return writebackPendingFileName(kind, reviewId, round).replace(
    /^writeback-/,
    'writeback-relayed-'
  );
}

function getWritebackPendingFolder() {
  const folderId = getWritebackPendingFolderId();
  if (!folderId) throw new Error('WRITEBACK_PENDING_FOLDER_ID (or INTAKE_PENDING_FOLDER_ID) is not configured');
  return DriveApp.getFolderById(folderId);
}

function archiveWritebackPendingFile(kind, reviewId, round) {
  const folder = getWritebackPendingFolder();
  const pendingName = writebackPendingFileName(kind, reviewId, round);
  const files = folder.getFilesByName(pendingName);
  if (!files.hasNext()) return;
  const file = files.next();
  const relayedName = writebackRelayedFileName(kind, reviewId, round);
  const existing = folder.getFilesByName(relayedName);
  while (existing.hasNext()) {
    existing.next().setTrashed(true);
  }
  file.setName(relayedName);
}

/**
 * Apply Review/Approve write-back JSON from Drive (in-process; no external POST).
 */
function relayWritebackFromPayload(payload, kind) {
  const reviewId = String(payload.reviewId || '').trim();
  const sheetId = String(payload.sheetId || '').trim();
  const round = Number(payload.round || 1);
  if (!reviewId || !sheetId) throw new Error('reviewId and sheetId are required in write-back payload');
  assertAllowedSpreadsheet(sheetId);
  const spreadsheet = SpreadsheetApp.openById(sheetId);
  ensureLedgerTabs(spreadsheet);
  const result = applyReviewWritebackPayload(spreadsheet, {
    ...payload,
    mode: 'review_writeback',
    reviewId,
    round,
  });
  archiveWritebackPendingFile(kind, reviewId, round);
  writeScanDiagnostic(
    spreadsheet,
    'writeback_relayed',
    `${kind} r${round}; items=${result.itemCount}; issues=${result.issueCount}`
  );
  Logger.log(JSON.stringify({ kind, reviewId, round, ...result }));
  return result;
}

function relayWritebackPendingFile(file, kind) {
  const payload = JSON.parse(file.getBlob().getDataAsString());
  return relayWritebackFromPayload(payload, kind);
}

/** Scan Drive for writeback-review-* and writeback-approve-* JSON and apply to the sheet. */
function scanWritebackPendingRelay() {
  const folderId = getWritebackPendingFolderId();
  if (!folderId) return { ok: false, skipped: true, reason: 'writeback folder unset' };
  const folder = DriveApp.getFolderById(folderId);
  const processed = [];
  const iterator = folder.getFiles();
  while (iterator.hasNext()) {
    const file = iterator.next();
    const name = String(file.getName() || '');
    const match = name.match(/^writeback-(review|approve)-(.+)-r(\d+)\.json$/);
    if (!match) continue;
    const kind = match[1];
    try {
      const result = relayWritebackPendingFile(file, kind);
      processed.push({ file: name, kind, ok: true, itemCount: result.itemCount });
    } catch (error) {
      processed.push({ file: name, kind, ok: false, error: safeError(error) });
      Logger.log(`Writeback relay failed for ${name}: ${safeError(error)}`);
    }
  }
  if (processed.length) Logger.log(`scanWritebackPendingRelay: ${JSON.stringify(processed)}`);
  return { ok: true, processed };
}

/** Clear a stuck Cursor lock so the next typed command can fire. Run from the editor. */
function resetCursorDispatch() {
  const spreadsheet = openConfiguredSpreadsheet();
  writeDispatch(spreadsheet, {
    inFlight: false,
    fingerprint: '',
    claimedAt: '',
    backgroundComposerId: '',
  });
  writeState(spreadsheet, { ...readState(spreadsheet), state: 'idle', lastError: null });
  writeScanDiagnostic(spreadsheet, 'reset', 'Dispatch lock cleared. Type review in Controls!B1.');
  Logger.log('Cursor dispatch lock cleared. Type review in Controls!B1 to fire once.');
}

/** Log current lock/state to Logger and Controls tab. Run from the editor after a failed trigger. */
function explainLastScan() {
  const spreadsheet = openConfiguredSpreadsheet();
  const diag = readScanDiagnostic(spreadsheet);
  const dispatch = readDispatch(spreadsheet);
  const state = readState(spreadsheet);
  const summary = {
    diagnostic: diag,
    dispatch,
    reviewState: state,
    dryRun: isDryRunEnabled(),
    reviewCallbackUrlSet: Boolean(getProperty('CURSOR_REVIEW_CALLBACK_URL')),
    approveCallbackUrlSet: Boolean(getProperty('CURSOR_APPROVE_CALLBACK_URL')),
    reviewIngressTokenSet: Boolean(getReviewIngressToken()),
    approveIngressTokenSet: Boolean(getProperty('CURSOR_APPROVE_INGRESS_TOKEN')),
    reviewProxyUrl: getReviewProxyUrl(),
  };
  Logger.log(JSON.stringify(summary, null, 2));
  return summary;
}

/** Simple trigger: fires when Controls!B1 is edited on the bound spreadsheet. */
function onEdit(e) {
  if (!e || !e.range) return;
  const sheet = e.range.getSheet();
  if (sheet.getName() !== TAB_CONTROLS || e.range.getA1Notation() !== 'B1') return;
  const value = String(e.range.getValue() || '').trim();
  if (value) {
    try {
      runReviewScan(false, true);
    } finally {
      scanWritebackPendingRelay();
    }
  }
}

function runReviewScan(forceDryRun, forceNewDispatch) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) {
    try {
      writeScanDiagnostic(
        openConfiguredSpreadsheet(),
        'lock_busy',
        'Another scan holds the script lock. Wait a few seconds and type review again.'
      );
    } catch (_) {}
    return;
  }
  try {
    const spreadsheet = openConfiguredSpreadsheet();
    const state = readState(spreadsheet);
    const source = forceNewDispatch ? 'onEdit' : 'poll';

    const triggerCommand = normalizeTriggerCommand(readTriggerCell(spreadsheet));
    const dryRun = forceDryRun || isDryRunForCommand(triggerCommand);
    const rows = readTableRows(spreadsheet, TAB_REVIEW_ITEMS);
    const changedRows = findTriggeredRows(rows, triggerCommand);
    if (!changedRows.length) {
      // Routine poll with nothing armed — stay quiet; do not overwrite a real outcome.
      if (source === 'onEdit') {
        writeScanDiagnostic(spreadsheet, 'no_trigger', `B1="${triggerCommand}"; no armed rows`);
      }
      return;
    }

    const fingerprint = triggerFingerprint(triggerCommand, changedRows);
    const dispatch = readDispatch(spreadsheet);
    if (!forceNewDispatch && isDispatchInFlight(dispatch) && dispatch.fingerprint === fingerprint) {
      clearProcessedCommands(spreadsheet, changedRows);
      clearTriggerCell(spreadsheet);
      writeScanDiagnostic(
        spreadsheet,
        'skipped_duplicate',
        `source=${source}; same command already in-flight (poll dedupe). Run resetCursorDispatch, then type review again.`
      );
      return;
    }

    const nextRound = Number(state.round || 0) + 1;
    const claimedAt = new Date().toISOString();
    markRowsInProgress(spreadsheet, changedRows, nextRound);
    writeState(spreadsheet, {
      ...state,
      round: nextRound,
      state: 'claimed',
      claimedAt,
      claimedBy: dryRun ? 'apps-script-dry-run' : 'apps-script',
      lastError: null,
    });
    writeDispatch(spreadsheet, {
      inFlight: true,
      fingerprint,
      claimedAt,
      backgroundComposerId: '',
    });

    // Consume the typed command before the Cursor POST so the next poll
    // sees an empty trigger and does not fire again.
    clearProcessedCommands(spreadsheet, changedRows);
    clearTriggerCell(spreadsheet);

    const reviewId = state.reviewId || `meeting:${spreadsheet.getId()}`;
    const meetingDocUrl = meetingDocUrlFromReviewId(reviewId);
    const payload = {
      reviewId,
      sheetId: spreadsheet.getId(),
      round: nextRound,
      command: triggerCommand,
      reviewProxyUrl: getReviewProxyUrl(),
      ingressToken: getCursorIngressToken(triggerCommand),
      writebackPendingFolderId: getWritebackPendingFolderId(),
      items: changedRows.map((row) => {
        const item = {
          ...row,
          rowAction: triggerCommand,
          idempotencyKey: buildIdempotencyKey(reviewId, row.itemId || row._itemId),
        };
        if (meetingDocUrl) item.meetingDocUrl = meetingDocUrl;
        return item;
      }),
      reviewRevision: String(spreadsheet.getRevisionId ? spreadsheet.getRevisionId() : nextRound),
    };
    if (triggerCommand === 'approve') {
      const scaffoldingUrl = getProperty('ISSUE_SCAFFOLDING_WEBHOOK_URL');
      const scaffoldingToken = getProperty('ISSUE_SCAFFOLDING_WEBHOOK_TOKEN');
      if (scaffoldingUrl) payload.issueScaffoldingWebhookUrl = scaffoldingUrl;
      if (scaffoldingToken) payload.issueScaffoldingWebhookToken = scaffoldingToken;
    }
    const response = dryRun ? buildDryRunReviewResponse(payload) : callCursor(payload);
    const asyncAccept = !dryRun && response.async === true;
    if (dryRun) {
      writeScanDiagnostic(
        spreadsheet,
        'dry_run_only',
        `source=${source}; DRY_RUN or missing callback for ${triggerCommand} — sheet updated locally, Cursor automation NOT called`
      );
    } else if (!response.ok) {
      writeScanDiagnostic(
        spreadsheet,
        'cursor_post_failed',
        `source=${source}; HTTP/error: ${response.error || 'unknown'}`
      );
    } else if (asyncAccept) {
      writeScanDiagnostic(
        spreadsheet,
        'cursor_post_ok',
        `source=${source}; async accept backgroundComposerId=${response.backgroundComposerId || 'n/a'}`
      );
    } else {
      writeScanDiagnostic(spreadsheet, 'cursor_post_sync', `source=${source}; sync response applied to sheet`);
    }
    writeState(spreadsheet, {
      ...state,
      round: nextRound,
      state: response.ok ? (asyncAccept ? 'running' : 'completed') : 'failed',
      lastProcessedRevision: response.reviewRevision || '',
      claimedAt,
      claimedBy: dryRun ? 'apps-script-dry-run' : 'apps-script',
      lastError: response.ok ? null : response.error,
    });
    writeDispatch(spreadsheet, {
      inFlight: Boolean(response.ok && asyncAccept),
      fingerprint,
      claimedAt,
      backgroundComposerId: response.backgroundComposerId || '',
    });
    if (!asyncAccept && response.itemUpdates) applyItemUpdates(spreadsheet, response.itemUpdates, nextRound);
    if (!asyncAccept && response.issueResults) appendIssueResults(spreadsheet, response.issueResults);
  } catch (error) {
    try {
      const spreadsheet = openConfiguredSpreadsheet();
      const state = readState(spreadsheet);
      writeState(spreadsheet, { ...state, state: 'failed', lastError: safeError(error) });
      writeDispatch(spreadsheet, { ...readDispatch(spreadsheet), inFlight: false });
      writeScanDiagnostic(spreadsheet, 'error', safeError(error));
    } catch (_) {}
    throw error;
  } finally {
    lock.releaseLock();
  }
}

function buildDryRunReviewResponse(payload) {
  const stamp = new Date().toISOString();
  return {
    ok: true,
    reviewRevision: `dry-run:${stamp}`,
    itemUpdates: (payload.items || []).map((item) => {
      const action = String(item.rowAction || item.command || 'review').trim().toLowerCase();
      const approved = action === 'approve';
      const rejected = action === 'reject';
      const iterationCount = Number(item.iterationCount || 0) + 1;
      let status = String(item.status || 'needs-review');
      if (approved) status = 'approved';
      if (rejected) status = 'rejected';
      if (action.indexOf('changes-requested:') === 0) status = 'changes-requested';
      if (action.indexOf('duplicate:') === 0) status = 'duplicate';
      const update = {
        itemId: item.itemId || item._itemId,
        command: '',
        status,
        iterationCount,
      };
      if (action !== 'approve') {
        update.cursorComment = `[dry-run ${action} round ${payload.round} @ ${stamp}]`;
      }
      return update;
    }),
  };
}

function findTriggeredRows(rows, triggerCommand) {
  const globalCmd = normalizeTriggerCommand(triggerCommand);
  if (!globalCmd || TRIGGER_COMMANDS.indexOf(globalCmd) === -1) return [];
  return rows
    .filter((row) => {
      const itemId = String(row.itemId || row._itemId || '').trim();
      if (!itemId) return false;
      if (isSkipIssue(row)) return false;
      return true;
    })
    .map((row) => ({ ...row, command: globalCmd }));
}

function normalizeTriggerCommand(raw) {
  const value = String(raw || '').trim().toLowerCase();
  if (value === 'review-all') return 'review';
  if (value === 'approve-all') return 'approve';
  return value;
}

function getCursorCallbackUrl(triggerCommand) {
  const command = normalizeTriggerCommand(triggerCommand);
  if (command === 'approve') return getProperty('CURSOR_APPROVE_CALLBACK_URL');
  return getProperty('CURSOR_REVIEW_CALLBACK_URL');
}

function getCursorIngressToken(triggerCommand) {
  const command = normalizeTriggerCommand(triggerCommand);
  if (command === 'approve') return getProperty('CURSOR_APPROVE_INGRESS_TOKEN');
  return getReviewIngressToken();
}

function getReviewIngressToken() {
  return getProperty('CURSOR_REVIEW_INGRESS_TOKEN') || getProperty('CURSOR_INGRESS_TOKEN');
}

function normalizeCommand(row) {
  return String(row.command || '').trim().toLowerCase();
}

function isSkipIssue(row) {
  if (row.skipIssue === true) return true;
  const value = String(row.skipIssue || '').trim().toLowerCase();
  return value === 'true' || value === 'yes' || value === '1' || value === 'x';
}

function markRowsInProgress(spreadsheet, rows, round) {
  applyItemUpdates(spreadsheet, rows.map((row) => ({
    itemId: row.itemId || row._itemId,
    status: 'in-progress',
  })), round);
}

function clearProcessedCommands(spreadsheet, rows) {
  const sheet = spreadsheet.getSheetByName(TAB_REVIEW_ITEMS);
  if (!sheet) return;
  const commandIndex = getHeaderIndex(sheet, 'command');
  rows.forEach((row) => {
    const rowNumber = findRowNumber(sheet, row.itemId || row._itemId);
    if (rowNumber > 0 && commandIndex >= 0) {
      sheet.getRange(rowNumber, commandIndex + 1).setValue('');
    }
  });
}

function callCursor(payload) {
  const callbackUrl = getCursorCallbackUrl(payload.command);
  if (!callbackUrl) {
    return { ok: false, error: `Missing callback URL for command ${payload.command}` };
  }
  const response = UrlFetchApp.fetch(callbackUrl, {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: { Authorization: `Bearer ${getCursorIngressToken(payload.command)}` },
    payload: JSON.stringify(payload),
  });
  const code = response.getResponseCode();
  const body = response.getContentText();
  let parsed = {};
  try { parsed = JSON.parse(body); } catch (_) {}
  if (code < 200 || code >= 300) {
    return { ok: false, error: `Cursor callback failed (${code})` };
  }
  // Cursor webhooks return async accept: { success: true, backgroundComposerId: "..." }
  // Treat this as ok=true; itemUpdates arrive later via doPost write-back.
  if (parsed.backgroundComposerId || parsed.success === true) {
    return { ok: true, async: true, backgroundComposerId: parsed.backgroundComposerId || '' };
  }
  if (parsed.ok === false) {
    return { ok: false, error: parsed.error || 'Cursor returned ok=false' };
  }
  return { ok: true, ...parsed };
}

function ensureLedgerTabs(spreadsheet) {
  ensureTab(spreadsheet, TAB_REVIEW_ITEMS, REVIEW_SURFACE_HEADERS);
  ensureTab(spreadsheet, TAB_REVIEW_DETAIL, ['itemId', 'payload']);
  ensureTab(spreadsheet, TAB_ISSUES, ISSUE_HEADERS);
  ensureControlsTab(spreadsheet);
  applySheetFormatting(spreadsheet);
}

function ensureControlsTab(spreadsheet) {
  let sheet = spreadsheet.getSheetByName(TAB_CONTROLS);
  if (!sheet) sheet = spreadsheet.insertSheet(TAB_CONTROLS);
  sheet.getRange('A1').setValue('Cursor Trigger');
  sheet.getRange('B1').setNote('Type review or approve, then press Enter. Do not run Apps Script during a demo.');
  sheet.getRange('A2').setValue('Commands: review · approve · reject');
  sheet.getRange('B2').setValue('Type review or approve in B1, then Enter. skipIssue rows are excluded. Do not re-approve a row that already has issueUrl.');
  sheet.getRange('A3').setValue('Demo');
  sheet.getRange('B3').setValue('Walk completed rows to show what happened. Use a new row only if you need to watch B1 fire live.');
  sheet.getRange('A4').setValue('Last scan');
  sheet.getRange('A5').setValue('Detail');
  sheet.getRange('A6').setValue('At');
  sheet.getRange('A1:A6').setFontWeight('bold');
  sheet.getRange('B1').setBackground('#e8f5e9');
  sheet.setFrozenRows(0);
  sheet.setColumnWidth(1, 160);
  sheet.setColumnWidth(2, 480);
}

/**
 * One-click presenter polish. Run from the Apps Script editor once (not during the demo).
 * Hides ops columns/tabs; does not change webhooks or B1 routing.
 */
function applyDemoPresentationFormatting() {
  const spreadsheet = getReviewSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  applySheetFormatting(spreadsheet);
  Logger.log('Demo presentation formatting applied.');
}

function ensureTab(spreadsheet, name, headers) {
  let sheet = spreadsheet.getSheetByName(name);
  if (!sheet) sheet = spreadsheet.insertSheet(name);
  const existing = sheet.getLastColumn() >= 1
    ? sheet.getRange(1, 1, 1, Math.max(headers.length, sheet.getLastColumn())).getValues()[0]
        .map((value) => String(value || '').trim())
    : [];
  if (existing.join('|') !== headers.join('|')) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  sheet.setFrozenRows(1);
}

function applySheetFormatting(spreadsheet) {
  const reviewSheet = spreadsheet.getSheetByName(TAB_REVIEW_ITEMS);
  if (!reviewSheet) return;
  const lastCol = Math.max(reviewSheet.getLastColumn(), REVIEW_SURFACE_HEADERS.length);
  const lastRow = Math.max(reviewSheet.getLastRow(), 2);
  const headerRange = reviewSheet.getRange(1, 1, 1, lastCol);
  headerRange.setFontWeight('bold');
  headerRange.setBackground('#e8eaed');
  reviewSheet.setFrozenRows(1);
  reviewSheet.setRowHeight(1, 28);

  const skipIndex = getHeaderIndex(reviewSheet, 'skipIssue') + 1;
  if (skipIndex > 0) {
    reviewSheet.getRange(2, skipIndex, Math.max(lastRow, 100) - 1, 1)
      .setDataValidation(SpreadsheetApp.newDataValidation().requireCheckbox().build());
  }
  const commandIndex = getHeaderIndex(reviewSheet, 'command') + 1;
  if (commandIndex > 0) {
    reviewSheet.getRange(2, commandIndex, Math.max(lastRow, 100) - 1, 1).setNote(
      'Leftover storage only. Trigger is Controls!B1 (review | approve | reject).'
    );
  }

  const widthByHeader = {
    itemId: 80,
    round: 60,
    title: 280,
    classification: 130,
    status: 140,
    skipIssue: 90,
    reviewerComment: 220,
    cursorComment: 280,
    command: 90,
    iterationCount: 90,
    issueNumber: 90,
    issueUrl: 280,
    updatedAt: 140,
  };
  REVIEW_SURFACE_HEADERS.forEach((name, idx) => {
    reviewSheet.setColumnWidth(idx + 1, widthByHeader[name] || 120);
  });
  reviewSheet.getRange(2, 1, Math.max(lastRow, 100) - 1, lastCol).setWrap(true);

  applyStatusConditionalFormat(reviewSheet);
  linkifyIssueUrls(reviewSheet);
  hideDemoOpsColumns(reviewSheet);

  const detail = spreadsheet.getSheetByName(TAB_REVIEW_DETAIL);
  if (detail) detail.hideSheet();

  const issues = spreadsheet.getSheetByName(TAB_ISSUES);
  if (issues) {
    issues.setFrozenRows(1);
    issues.getRange(1, 1, 1, ISSUE_HEADERS.length).setFontWeight('bold').setBackground('#e8eaed');
    issues.setColumnWidth(5, 280);
  }
}

function applyStatusConditionalFormat(reviewSheet) {
  const statusCol = getHeaderIndex(reviewSheet, 'status') + 1;
  if (statusCol <= 0) return;
  const lastRow = Math.max(reviewSheet.getLastRow(), 100);
  const range = reviewSheet.getRange(2, statusCol, lastRow - 1, 1);
  const paints = [
    { texts: ['needs-review', 'changes-requested', 'creating'], bg: '#fce8b2' },
    { texts: ['clarification'], bg: '#d2e3fc' },
    { texts: ['approved', 'created'], bg: '#ceead6' },
    { texts: ['rejected', 'failed', 'duplicate'], bg: '#f6d0d0' },
  ];
  const rules = paints.flatMap((paint) => paint.texts.map((text) => (
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo(text)
      .setBackground(paint.bg)
      .setRanges([range])
      .build()
  )));
  reviewSheet.setConditionalFormatRules(rules);
}

function linkifyIssueUrls(reviewSheet) {
  const urlCol = getHeaderIndex(reviewSheet, 'issueUrl') + 1;
  if (urlCol <= 0) return;
  const lastRow = reviewSheet.getLastRow();
  if (lastRow < 2) return;
  const values = reviewSheet.getRange(2, urlCol, lastRow - 1, 1).getValues();
  values.forEach((row, idx) => {
    const url = String(row[0] || '').trim();
    if (!/^https:\/\//i.test(url)) return;
    const rich = SpreadsheetApp.newRichTextValue()
      .setText(url)
      .setLinkUrl(url)
      .build();
    reviewSheet.getRange(idx + 2, urlCol).setRichTextValue(rich);
  });
}

function hideDemoOpsColumns(reviewSheet) {
  const hideNames = [
    'itemId', 'round', 'command', 'iterationCount',
    'skipIssue', 'issueNumber', 'updatedAt',
  ];
  hideNames.forEach((name) => {
    const col = getHeaderIndex(reviewSheet, name) + 1;
    if (col > 0) reviewSheet.hideColumns(col);
  });
}

function upsertItems(spreadsheet, items, round) {
  ensureLedgerTabs(spreadsheet);
  items.forEach((item) => {
    const merged = mergeItemFields(item, round);
    writeSurfaceRow(spreadsheet, merged, round);
    writeDetailPayload(spreadsheet, merged.itemId, buildPayloadFields(merged, round));
  });
}

function applyItemUpdates(spreadsheet, items, round) {
  items.forEach((item) => {
    const itemId = String(item.itemId || item.id || '').trim();
    if (!itemId) return;
    const existing = readItemById(spreadsheet, itemId);
    const merged = { ...existing, ...item, itemId };
    if (Object.prototype.hasOwnProperty.call(item, 'cursorComment')) {
      merged.cursorComment = truncateCursorComment(item.cursorComment);
    }
    if (merged.iterationCount === undefined && shouldIncrementIteration(item)) {
      merged.iterationCount = Number(existing.iterationCount || 0) + 1;
    }
    writeSurfaceRow(spreadsheet, merged, round);
    if (hasPayloadFields(item)) {
      writeDetailPayload(spreadsheet, itemId, buildPayloadFields({ ...existing, ...item }, round));
    }
  });
}

function truncateCursorComment(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (text.length <= CURSOR_COMMENT_MAX) return text;
  return `${text.slice(0, CURSOR_COMMENT_MAX - 1)}…`;
}

function shouldIncrementIteration(item) {
  return Object.prototype.hasOwnProperty.call(item, 'cursorComment') ||
    Object.prototype.hasOwnProperty.call(item, 'status');
}

function hasPayloadFields(item) {
  return REVIEW_PAYLOAD_FIELDS.some((name) => Object.prototype.hasOwnProperty.call(item, name));
}

function mergeItemFields(item, round) {
  const flat = flattenItemFields(item);
  const itemId = flat.itemId;
  return {
    ...flat,
    itemId,
    round: flat.round !== undefined ? flat.round : round,
    iterationCount: flat.iterationCount !== undefined ? flat.iterationCount : 0,
    updatedAt: new Date().toISOString(),
  };
}

function flattenItemFields(item) {
  const flat = { ...(item || {}) };
  if (flat.payload && typeof flat.payload === 'object' && !Array.isArray(flat.payload)) {
    Object.assign(flat, flat.payload);
  }
  flat.itemId = String(flat.itemId || flat.id || '').trim();
  if (!flat.title && flat.sourceExcerpt) {
    const parts = String(flat.sourceExcerpt).split('|').map((part) => part.trim());
    if (parts.length >= 2) flat.title = parts[1];
  }
  return flat;
}

function formatSurfaceCell(name, flat, round) {
  if (name === 'itemId') return flat.itemId;
  if (name === 'round') return flat.round !== undefined ? flat.round : round;
  if (name === 'iterationCount') return flat.iterationCount !== undefined ? flat.iterationCount : 0;
  if (name === 'updatedAt') return new Date().toISOString();
  if (name === 'skipIssue') return isSkipIssue(flat);
  if (Object.prototype.hasOwnProperty.call(flat, name)) {
    return formatCellValue(flat[name]);
  }
  if (name === 'status') return String(flat.status || '').trim() || 'needs-review';
  return '';
}

function writeSurfaceRow(spreadsheet, item, round) {
  const sheet = spreadsheet.getSheetByName(TAB_REVIEW_ITEMS);
  if (!sheet) throw new Error('ReviewItems tab is missing');
  const flat = flattenItemFields(item);
  if (!flat.itemId) return;

  let rowNumber = findRowNumber(sheet, flat.itemId);
  if (rowNumber <= 0) rowNumber = Math.max(sheet.getLastRow() + 1, 2);

  const header = getHeaderRow(sheet);
  if (!header.length) throw new Error('ReviewItems header row is missing');

  const row = header.map((name) => formatSurfaceCell(name, flat, round));
  sheet.getRange(rowNumber, 1, 1, header.length).setValues([row]);
}

/**
 * One-click repair: copy ReviewItemsDetail payloads onto ReviewItems surface rows.
 * Run from the orchestrator editor after a successful intake POST if surface rows
 * are missing while detail rows exist.
 */
function repairSurfaceFromDetail() {
  const spreadsheet = openConfiguredSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  const detailSheet = spreadsheet.getSheetByName(TAB_REVIEW_DETAIL);
  if (!detailSheet || detailSheet.getLastRow() < 2) {
    Logger.log('No ReviewItemsDetail rows to repair.');
    return 0;
  }
  const rowCount = detailSheet.getLastRow() - 1;
  const values = detailSheet.getRange(2, 1, rowCount, 2).getValues();
  let repaired = 0;
  values.forEach((cells) => {
    const itemId = String(cells[0] || '').trim();
    const payloadText = String(cells[1] || '').trim();
    if (!itemId || !payloadText) return;
    let payload = {};
    try {
      payload = JSON.parse(payloadText);
    } catch (_) {
      payload = {};
    }
    writeSurfaceRow(spreadsheet, { itemId, ...payload }, payload.round || 1);
    repaired += 1;
  });
  Logger.log(`Repaired ${repaired} ReviewItems surface row(s).`);
  return repaired;
}

const PILOT_LOADING_ITEM_ID = '1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:0';
const PILOT_LOADING_REVIEWER_COMMENT =
  'Pilot AC: boolean loading prop default false. While loading disable input and show suffix modus-wc-loader. aria-busy on wrapper; loader aria-label Loading. Loader replaces clear/search suffix icons when loading.';

/**
 * Repair mangled ReviewItems surface fields for the pilot loading row without
 * clearing issueUrl/issueNumber/status. Also dedupes Issues tab by idempotencyKey.
 * Run once from the editor after deploy.
 */
function repairPilotLoadingSurfaceKeepIssue() {
  const spreadsheet = openConfiguredSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  const existing = readItemById(spreadsheet, PILOT_LOADING_ITEM_ID);
  applyItemUpdates(spreadsheet, [{
    itemId: PILOT_LOADING_ITEM_ID,
    classification: 'repo-work',
    reviewerComment: PILOT_LOADING_REVIEWER_COMMENT,
  }], Number(existing.round || readState(spreadsheet).round || 1));
  const deduped = dedupeIssuesTab(spreadsheet);
  Logger.log(
    `Repaired pilot loading surface (issueUrl=${existing.issueUrl || 'n/a'}); deduped ${deduped} Issues row(s).`
  );
  return { itemId: PILOT_LOADING_ITEM_ID, issueUrl: existing.issueUrl, deduped };
}

/**
 * DESTRUCTIVE — fresh retry only. Clears Issues tab and resets row to needs-review.
 * Do not run on rows that already have issueUrl (e.g. issue #48).
 */
function pilotPrepareLoadingRow() {
  const spreadsheet = openConfiguredSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  const itemId = PILOT_LOADING_ITEM_ID;
  const detail = readDetailPayloads(spreadsheet)[itemId] || {};
  applyItemUpdates(spreadsheet, [{
    itemId,
    classification: 'repo-work',
    status: 'needs-review',
    skipIssue: false,
    reviewerComment: PILOT_LOADING_REVIEWER_COMMENT,
    acceptanceCriteria: detail.acceptanceCriteria || [],
    designNeeded: detail.designNeeded !== false,
    componentHints: detail.componentHints || ['modus-wc-text-input'],
  }], Number(readState(spreadsheet).round || 1));
  const issuesSheet = spreadsheet.getSheetByName(TAB_ISSUES);
  if (issuesSheet && issuesSheet.getLastRow() > 1) {
    issuesSheet.getRange(2, 1, issuesSheet.getLastRow() - 1, ISSUE_HEADERS.length).clearContent();
  }
  resetCursorDispatch();
  Logger.log('Prepared loading row for approve. Type approve in Controls!B1 or run triggerApproveFromScript().');
}

/** Set Controls!B1=approve and dispatch immediately (bound-script helper). */
function triggerApproveFromScript() {
  const spreadsheet = openConfiguredSpreadsheet();
  const controls = spreadsheet.getSheetByName(TAB_CONTROLS);
  if (controls) controls.getRange('B1').setValue('approve');
  runReviewScan(false, true);
}

const PILOT_MEETING_DOC_ID = '1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4';
const PILOT_REVIEW_ID = `meeting:${PILOT_MEETING_DOC_ID}`;

/**
 * Seed synthetic pipeline-test rows (T3a/T3b/T3d) without manual paste.
 * Safe to re-run: upserts by itemId; does not touch ReviewItems:0 or :1.
 * After run: review optional → human AC on T3a → approve per row.
 */
function seedPilotTestRows() {
  const spreadsheet = openConfiguredSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  const round = Number(readState(spreadsheet).round || 1);
  const docPrefix = `${PILOT_MEETING_DOC_ID}:`;
  const t3aId = `${docPrefix}ReviewItems:2`;
  const t3bId = `${docPrefix}ReviewItems:3`;
  const t3dId = `${docPrefix}ReviewItems:4`;
  const t3aReviewerComment =
    'Pilot T3a: Add disabled prop to modus-wc-button. When disabled, prevent click and set aria-disabled. Show not-allowed cursor on hover.';
  const items = [
    {
      itemId: t3aId,
      title: 'Add disabled prop to button',
      classification: 'repo-work',
      status: 'needs-review',
      skipIssue: false,
      reviewerComment: t3aReviewerComment,
      sourceExcerpt: 'Sprint Planning | Add disabled prop to button | modus-wc-button',
      summary: 'Expose a boolean disabled prop on modus-wc-button with accessible disabled state.',
      designNeeded: false,
      componentHints: ['modus-wc-button'],
      acceptanceCriteria: [
        'disabled prop defaults to false',
        'When disabled, click handlers do not fire',
        'Host sets aria-disabled=true when disabled',
        'Visual style matches Modus disabled token (opacity/cursor)',
      ],
      rationale: 'Common control gap; aligns with Modus button patterns.',
    },
    {
      itemId: t3bId,
      title: 'Vague spinner sizing ask',
      classification: 'repo-work',
      status: 'needs-review',
      skipIssue: false,
      reviewerComment: 'Needs sizing guidance.',
      sourceExcerpt: 'Sprint Planning | Maybe fix spinner sizes',
      summary: 'Unclear spinner sizing request without acceptance criteria.',
      designNeeded: false,
      componentHints: ['modus-wc-loader'],
      acceptanceCriteria: [],
      rationale: 'Thin intake item for clarification-path test.',
    },
    {
      itemId: t3dId,
      title: 'Update team wiki process',
      classification: 'process/meta',
      status: 'needs-review',
      skipIssue: true,
      reviewerComment: 'Process note only — skip issue creation.',
      sourceExcerpt: 'Sprint Planning | Update wiki onboarding steps',
      summary: 'Meta process item; must not reach Scaffolding.',
      designNeeded: false,
      acceptanceCriteria: [],
      rationale: 'skipIssue control row for T3d.',
    },
  ];
  upsertItems(spreadsheet, items, round);
  writeState(spreadsheet, {
    ...readState(spreadsheet),
    reviewId: PILOT_REVIEW_ID,
    round,
  });
  Logger.log(
    `Seeded pilot test rows: ${t3aId}, ${t3bId}, ${t3dId}. ` +
    `Expected idempotency keys: ${buildIdempotencyKey(PILOT_REVIEW_ID, t3aId)}`
  );
  return {
    reviewId: PILOT_REVIEW_ID,
    rows: items.map((item) => ({
      itemId: item.itemId,
      idempotencyKey: buildIdempotencyKey(PILOT_REVIEW_ID, item.itemId),
    })),
  };
}

const T1_MEETING_DOC_ID = '1AMbbKrWc8fmS2CI_jzwoC7KvdygL4Wz9kY3Y861gjYg';
const T1_REVIEW_ID = `meeting:${T1_MEETING_DOC_ID}`;

/** Seed T1 intake rows when live coordinator POST fails (token/doc issues). */
function seedT1IntakeRows() {
  const spreadsheet = openConfiguredSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  const round = Number(readState(spreadsheet).round || 1);
  const prefix = `${T1_MEETING_DOC_ID}:`;
  const items = [
    {
      itemId: `${prefix}ReviewItems:0`,
      title: 'Add tooltip show-delay prop',
      classification: 'repo-work',
      status: 'needs-review',
      skipIssue: false,
      sourceExcerpt: 'Sprint Planning | tooltip show-delay | modus-wc-tooltip',
      summary: 'Expose number showDelay prop default 300ms on modus-wc-tooltip.',
      componentHints: ['modus-wc-tooltip'],
      acceptanceCriteria: ['showDelay prop defaults to 300', 'Delay applies before open'],
      designNeeded: false,
    },
    {
      itemId: `${prefix}ReviewItems:1`,
      title: 'Breadcrumb truncation Figma spec',
      classification: 'design-work',
      status: 'needs-review',
      skipIssue: false,
      sourceExcerpt: 'Sprint Planning | breadcrumb truncation pattern',
      summary: 'Design spec for breadcrumb truncation before implementation.',
      designNeeded: true,
      acceptanceCriteria: ['Document truncation breakpoints', 'Staged Figma folder link'],
    },
    {
      itemId: `${prefix}ReviewItems:2`,
      title: 'Update sprint retro wiki',
      classification: 'process/meta',
      status: 'needs-review',
      skipIssue: true,
      sourceExcerpt: 'Sprint Planning | wiki template',
      summary: 'Process/meta — no engineering ticket.',
    },
  ];
  upsertItems(spreadsheet, items, round);
  writeState(spreadsheet, { ...readState(spreadsheet), reviewId: T1_REVIEW_ID, round });
  Logger.log(`Seeded T1 intake rows under ${T1_REVIEW_ID}`);
  return { reviewId: T1_REVIEW_ID, itemCount: items.length };
}

/** Seed T1 happy-path row (ReviewItems:3) with T3a-equivalent AC for no-clarification approve test. */
function seedT1HappyPathRow() {
  const spreadsheet = openConfiguredSpreadsheet();
  ensureLedgerTabs(spreadsheet);
  const round = Number(readState(spreadsheet).round || 1);
  const prefix = `${T1_MEETING_DOC_ID}:`;
  const itemId = `${prefix}ReviewItems:3`;
  const reviewerComment =
    'Pilot T3a: Add disabled prop to modus-wc-button. When disabled, prevent click and set aria-disabled. Show not-allowed cursor on hover.';
  const item = {
    itemId,
    title: 'Add disabled prop to button',
    classification: 'repo-work',
    status: 'needs-review',
    skipIssue: false,
    reviewerComment,
    sourceExcerpt: 'Sprint Planning | Add disabled prop to button | modus-wc-button',
    summary: 'Expose a boolean disabled prop on modus-wc-button with accessible disabled state.',
    designNeeded: false,
    componentHints: ['modus-wc-button'],
    acceptanceCriteria: [
      'disabled prop defaults to false',
      'When disabled, click handlers do not fire',
      'Host sets aria-disabled=true when disabled',
      'Visual style matches Modus disabled token (opacity/cursor)',
    ],
    rationale: 'T1 happy-path row; mirrors proven T3a AC for scaffolding without clarification.',
  };
  upsertItems(spreadsheet, [item], round);
  writeState(spreadsheet, { ...readState(spreadsheet), reviewId: T1_REVIEW_ID, round });
  Logger.log(
    `Seeded T1 happy-path row ${itemId}. Expected idempotency key: ${buildIdempotencyKey(T1_REVIEW_ID, itemId)}`
  );
  return {
    reviewId: T1_REVIEW_ID,
    itemId,
    idempotencyKey: buildIdempotencyKey(T1_REVIEW_ID, itemId),
  };
}

/** Temporarily skip T3b when isolating T3a approve (restore with restoreT3bSkipIssue). */
function skipT3bTempForT3aApprove() {
  const spreadsheet = openConfiguredSpreadsheet();
  applyItemUpdates(spreadsheet, [{
    itemId: '1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:3',
    skipIssue: true,
  }], Number(readState(spreadsheet).round || 1));
  Logger.log('T3b skipIssue=TRUE for isolated T3a approve');
}

function restoreT3bSkipIssue() {
  const spreadsheet = openConfiguredSpreadsheet();
  applyItemUpdates(spreadsheet, [{
    itemId: '1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4:ReviewItems:3',
    skipIssue: false,
  }], Number(readState(spreadsheet).round || 1));
  Logger.log('T3b skipIssue=FALSE restored');
}

const APPROVE_ISOLATE_SNAPSHOT_KEY = 'APPROVE_ISOLATE_SNAPSHOT';

/**
 * Temporarily set skipIssue=TRUE on every non-skip row except itemId so B1=approve
 * sends only one row. Restore with restoreIsolatedApproveSkips().
 */
function isolateSingleRowForApprove(itemId) {
  const only = String(itemId || '').trim();
  if (!only) throw new Error('itemId is required');
  const spreadsheet = openConfiguredSpreadsheet();
  const round = Number(readState(spreadsheet).round || 1);
  const snapshot = {};
  readTableRows(spreadsheet, TAB_REVIEW_ITEMS).forEach((row) => {
    const id = String(row.itemId || row._itemId || '').trim();
    if (!id) return;
    const skipped = isSkipIssue(row);
    if (id === only) {
      // A previous isolated test may have left this target skipped. Re-arm it
      // while preserving its current value for cleanup.
      snapshot[id] = skipped;
      if (skipped) {
        applyItemUpdates(spreadsheet, [{ itemId: id, skipIssue: false }], round);
      }
      return;
    }
    if (skipped) return;
    snapshot[id] = false;
    applyItemUpdates(spreadsheet, [{ itemId: id, skipIssue: true }], round);
  });
  PropertiesService.getScriptProperties().setProperty(
    APPROVE_ISOLATE_SNAPSHOT_KEY,
    JSON.stringify(snapshot)
  );
  Logger.log(`Isolated approve to ${only}. Type approve in Controls!B1.`);
  return { ok: true, onlyItemId: only, skippedCount: Object.keys(snapshot).length };
}

/** One-click: approve only T1 tooltip row (1AMbbKr…:ReviewItems:0). */
function isolateT1TooltipForApprove() {
  return isolateSingleRowForApprove(
    '1AMbbKrWc8fmS2CI_jzwoC7KvdygL4Wz9kY3Y861gjYg:ReviewItems:0'
  );
}

/** One-click: approve only T1 happy-path row (ReviewItems:3). */
function isolateT1HappyPathForApprove() {
  return isolateSingleRowForApprove(
    '1AMbbKrWc8fmS2CI_jzwoC7KvdygL4Wz9kY3Y861gjYg:ReviewItems:3'
  );
}

function restoreIsolatedApproveSkips() {
  const raw = PropertiesService.getScriptProperties().getProperty(APPROVE_ISOLATE_SNAPSHOT_KEY);
  if (!raw) {
    Logger.log('No approve isolate snapshot to restore.');
    return { ok: false, reason: 'no snapshot' };
  }
  const snapshot = JSON.parse(raw);
  const spreadsheet = openConfiguredSpreadsheet();
  const round = Number(readState(spreadsheet).round || 1);
  Object.keys(snapshot).forEach((id) => {
    applyItemUpdates(spreadsheet, [{ itemId: id, skipIssue: snapshot[id] }], round);
  });
  PropertiesService.getScriptProperties().deleteProperty(APPROVE_ISOLATE_SNAPSHOT_KEY);
  Logger.log(`Restored skipIssue for ${Object.keys(snapshot).length} row(s).`);
  return { ok: true, restoredCount: Object.keys(snapshot).length };
}

function writeDetailPayload(spreadsheet, itemId, payload) {
  const sheet = spreadsheet.getSheetByName(TAB_REVIEW_DETAIL);
  if (!sheet) throw new Error('ReviewItemsDetail tab is missing');
  let rowNumber = findRowNumber(sheet, itemId);
  if (rowNumber <= 0) {
    rowNumber = Math.max(sheet.getLastRow() + 1, 2);
  }
  sheet.getRange(rowNumber, 1, 1, 2).setValues([[itemId, JSON.stringify(payload)]]);
}

function buildPayloadFields(item, round) {
  const payload = {};
  REVIEW_PAYLOAD_FIELDS.forEach((name) => {
    const value = item[name] ?? (name === 'round' ? round : '');
    if (value !== '') payload[name] = value;
  });
  return payload;
}

function appendIssueResults(spreadsheet, results) {
  const sheet = spreadsheet.getSheetByName(TAB_ISSUES);
  if (!sheet) throw new Error('Issues tab is missing');
  results.forEach((result) => {
    const row = ISSUE_HEADERS.map((name) => formatCellValue(result[name] ?? ''));
    const idempotencyKey = String(result.idempotencyKey || '').trim();
    let rowNumber = idempotencyKey
      ? findRowNumberByColumn(sheet, 'idempotencyKey', idempotencyKey)
      : -1;
    if (rowNumber <= 0 && result.itemId) {
      rowNumber = findRowNumber(sheet, result.itemId);
    }
    if (rowNumber > 0) {
      sheet.getRange(rowNumber, 1, 1, ISSUE_HEADERS.length).setValues([row]);
    } else {
      sheet.appendRow(row);
    }
  });
}

/** Remove duplicate Issues rows, keeping the first row per idempotencyKey. */
function dedupeIssuesTab(spreadsheet) {
  const sheet = spreadsheet.getSheetByName(TAB_ISSUES);
  if (!sheet || sheet.getLastRow() < 3) return 0;
  const keyIndex = getHeaderIndex(sheet, 'idempotencyKey');
  if (keyIndex < 0) return 0;
  const lastRow = sheet.getLastRow();
  const values = sheet.getRange(2, keyIndex + 1, lastRow - 1, 1).getValues();
  const seen = new Set();
  const rowsToDelete = [];
  values.forEach((cells, offset) => {
    const key = String(cells[0] || '').trim();
    if (!key) return;
    const rowNumber = offset + 2;
    if (seen.has(key)) rowsToDelete.push(rowNumber);
    else seen.add(key);
  });
  rowsToDelete.sort((a, b) => b - a).forEach((rowNumber) => sheet.deleteRow(rowNumber));
  return rowsToDelete.length;
}

function readTableRows(spreadsheet, tabName) {
  const sheet = spreadsheet.getSheetByName(tabName);
  if (!sheet || sheet.getLastRow() < 2) return [];
  const header = getHeaderRow(sheet);
  const width = header.length;
  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, width).getValues();
  const detailByItemId = tabName === TAB_REVIEW_ITEMS
    ? readDetailPayloads(spreadsheet)
    : {};
  return values.map((cells, offset) => {
    const value = {};
    header.forEach((key, index) => {
      value[key] = formatCellValue(cells[index]);
    });
    value._row = offset + 2;
    value._itemId = value.itemId;
    if (value.itemId && detailByItemId[value.itemId]) {
      Object.assign(value, detailByItemId[value.itemId]);
    }
    return value;
  });
}

function readItemById(spreadsheet, itemId) {
  return readTableRows(spreadsheet, TAB_REVIEW_ITEMS)
    .find((row) => row.itemId === itemId) || { itemId, iterationCount: 0 };
}

function readDetailPayloads(spreadsheet) {
  const sheet = spreadsheet.getSheetByName(TAB_REVIEW_DETAIL);
  if (!sheet || sheet.getLastRow() < 2) return {};
  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues();
  const payloads = {};
  values.forEach((row) => {
    const itemId = String(row[0] || '').trim();
    const payloadText = String(row[1] || '').trim();
    if (!itemId || !payloadText) return;
    try {
      payloads[itemId] = JSON.parse(payloadText);
    } catch (_) {
      payloads[itemId] = {};
    }
  });
  return payloads;
}

function getHeaderRow(sheet) {
  const lastColumn = Math.max(sheet.getLastColumn(), 1);
  return sheet.getRange(1, 1, 1, lastColumn).getValues()[0]
    .map((value) => String(value || '').trim());
}

function getHeaderIndex(sheet, name) {
  return getHeaderRow(sheet).indexOf(name);
}

function findRowNumber(sheet, itemId) {
  return findRowNumberByColumn(sheet, 'itemId', itemId);
}

function findRowNumberByColumn(sheet, columnName, targetValue) {
  const target = String(targetValue || '').trim();
  if (!target) return -1;
  const column = getHeaderIndex(sheet, columnName) + 1;
  if (column <= 0) return -1;
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return -1;
  const values = sheet.getRange(2, column, lastRow - 1, 1).getValues();
  for (let i = 0; i < values.length; i += 1) {
    if (String(values[i][0] || '').trim() === target) return i + 2;
  }
  return -1;
}

function readState(spreadsheet) {
  const key = stateKey(spreadsheet.getId());
  return JSON.parse(
    PropertiesService.getScriptProperties().getProperty(key) ||
    JSON.stringify({
      reviewId: `meeting:${spreadsheet.getId()}`,
      round: 0,
      state: 'idle',
      lastProcessedRevision: '',
      claimedAt: '',
      claimedBy: '',
      lastError: null,
    })
  );
}

function writeState(spreadsheet, value) {
  PropertiesService.getScriptProperties().setProperty(
    stateKey(spreadsheet.getId()),
    JSON.stringify(value)
  );
}

function stateKey(sheetId) {
  return `REVIEW_STATE:${sheetId}`;
}

function dispatchKey(sheetId) {
  return `CURSOR_DISPATCH:${sheetId}`;
}

function readDispatch(spreadsheet) {
  try {
    return JSON.parse(
      PropertiesService.getScriptProperties().getProperty(dispatchKey(spreadsheet.getId())) || '{}'
    );
  } catch (_) {
    return {};
  }
}

function writeDispatch(spreadsheet, value) {
  PropertiesService.getScriptProperties().setProperty(
    dispatchKey(spreadsheet.getId()),
    JSON.stringify(value || {})
  );
}

function isDispatchInFlight(dispatch) {
  if (!dispatch || !dispatch.inFlight) return false;
  const started = Date.parse(dispatch.claimedAt || '') || 0;
  if (!started) return true;
  return Date.now() - started < 45 * 60 * 1000;
}

function triggerFingerprint(triggerCommand, rows) {
  const parts = (rows || [])
    .map((row) => String(row.itemId || row._itemId || '').trim())
    .filter((itemId) => itemId)
    .sort();
  return `${normalizeTriggerCommand(triggerCommand)}|${parts.join(',')}`;
}

function diagnosticKey(sheetId) {
  return `CURSOR_SCAN_DIAG:${sheetId}`;
}

function writeScanDiagnostic(spreadsheet, outcome, detail) {
  const stamp = new Date().toISOString();
  const payload = {
    outcome: String(outcome || ''),
    detail: String(detail || '').slice(0, 500),
    at: stamp,
  };
  const sheet = spreadsheet.getSheetByName(TAB_CONTROLS);
  if (sheet) {
    sheet.getRange('B4').setValue(payload.outcome);
    sheet.getRange('B5').setValue(payload.detail);
    sheet.getRange('B6').setValue(payload.at);
  }
  PropertiesService.getScriptProperties().setProperty(
    diagnosticKey(spreadsheet.getId()),
    JSON.stringify(payload)
  );
  Logger.log(`[scan] ${payload.outcome}: ${payload.detail}`);
}

function readScanDiagnostic(spreadsheet) {
  try {
    return JSON.parse(
      PropertiesService.getScriptProperties().getProperty(diagnosticKey(spreadsheet.getId())) || '{}'
    );
  } catch (_) {
    return {};
  }
}

function getReviewSpreadsheet() {
  const configuredId = getProperty('REVIEW_SHEET_ID');
  if (configuredId) return SpreadsheetApp.openById(configuredId);
  try {
    const active = SpreadsheetApp.getActiveSpreadsheet();
    if (active) {
      PropertiesService.getScriptProperties().setProperty('REVIEW_SHEET_ID', active.getId());
      return active;
    }
  } catch (_) {}
  const created = SpreadsheetApp.create('Review Ledger Demo');
  PropertiesService.getScriptProperties().setProperty('REVIEW_SHEET_ID', created.getId());
  return created;
}

function openConfiguredSpreadsheet() {
  return getReviewSpreadsheet();
}

function createReviewLedgerDemo() {
  const spreadsheet = getReviewSpreadsheet();

  ensureLedgerTabs(spreadsheet);
  upsertItems(spreadsheet, [
    {
      itemId: 'demo-item-001',
      round: 1,
      sourceExcerpt: 'Add loading and error states to text input.',
      classification: 'repo-work',
      rationale: 'Explicit repository change requested in meeting notes.',
      duplicateCandidates: [],
      title: 'Add loading state to text input',
      summary: 'Users need visible progress while async validation runs.',
      owner: 'James',
      designNeeded: false,
      acceptanceCriteria: ['Loading spinner visible', 'Field disabled while loading'],
      status: 'needs-review',
      skipIssue: false,
      reviewerComment: 'Add accessibility details before approval.',
      cursorComment: '',
      command: '',
      iterationCount: 0,
    },
    {
      itemId: 'demo-item-002',
      round: 1,
      sourceExcerpt: 'Prioritize tickets for sprint.',
      classification: 'process/meta',
      rationale: 'Meeting mechanics — do not create an issue.',
      duplicateCandidates: [],
      title: 'Prioritize backlog',
      summary: 'Process note only.',
      designNeeded: false,
      acceptanceCriteria: [],
      status: 'needs-review',
      skipIssue: true,
      reviewerComment: 'No issue needed.',
      cursorComment: '',
      command: '',
      iterationCount: 0,
    },
  ], 1);

  appendIssueResults(spreadsheet, [{
    itemId: 'demo-item-001',
    idempotencyKey: `gemini:demo:demo-item-001`,
    status: 'pending',
    issueNumber: '',
    issueUrl: '',
    createdAt: new Date().toISOString(),
    lastError: '',
    reviewComment: '',
  }]);

  writeState(spreadsheet, {
    reviewId: `meeting:${spreadsheet.getId()}`,
    round: 0,
    state: 'idle',
    lastProcessedRevision: '',
    claimedAt: '',
    claimedBy: '',
    lastError: null,
  });

  Logger.log(`Review ledger demo ready: ${spreadsheet.getUrl()}`);
  return spreadsheet.getUrl();
}

function isDryRunForCommand(triggerCommand) {
  const flag = getProperty('DRY_RUN_REVIEW').toLowerCase();
  if (flag === 'true') return true;
  if (flag === 'false') return false;
  return !getCursorCallbackUrl(triggerCommand);
}

function isDryRunEnabled() {
  const flag = getProperty('DRY_RUN_REVIEW').toLowerCase();
  if (flag === 'true') return true;
  if (flag === 'false') return false;
  return !getProperty('CURSOR_REVIEW_CALLBACK_URL') ||
    !getProperty('CURSOR_APPROVE_CALLBACK_URL');
}

function normalizePollMinutes(value) {
  const allowed = [1, 5, 10, 15, 30];
  const minutes = Number(value);
  return allowed.indexOf(minutes) === -1 ? 5 : minutes;
}

function removeTriggersFor(functionName) {
  ScriptApp.getProjectTriggers()
    .filter((trigger) => trigger.getHandlerFunction() === functionName)
    .forEach((trigger) => ScriptApp.deleteTrigger(trigger));
}

function assertAllowedSpreadsheet(sheetId) {
  const configured = getProperty('REVIEW_SOURCE_ALLOWLIST');
  const allowed = configured
    ? configured.split(',').map((item) => item.trim())
    : [getProperty('REVIEW_SHEET_ID')];
  if (allowed.indexOf(sheetId) === -1) throw new Error('Spreadsheet is not allowlisted');
}

function parseJsonBody(e) {
  const contents = e && e.postData && e.postData.contents;
  if (!contents) throw new Error('JSON request body is required');
  const value = JSON.parse(contents);
  if (!value || typeof value !== 'object') throw new Error('JSON body must be an object');
  return value;
}

function requireToken(token) {
  const reviewToken = getReviewIngressToken();
  const approveToken = getProperty('CURSOR_APPROVE_INGRESS_TOKEN');
  if (!token || (token !== reviewToken && token !== approveToken)) {
    throw new Error('Invalid ingress token');
  }
}

function getProperty(name) {
  return String(PropertiesService.getScriptProperties().getProperty(name) || '').trim();
}

/** Read the global trigger command from Controls!B1. Returns "" if not set. */
function readTriggerCell(spreadsheet) {
  const sheet = spreadsheet.getSheetByName(TAB_CONTROLS);
  if (!sheet) return '';
  return String(sheet.getRange('B1').getValue() || '').trim().toLowerCase();
}

/** Clear the trigger cell after the scan has claimed the rows. */
function clearTriggerCell(spreadsheet) {
  const sheet = spreadsheet.getSheetByName(TAB_CONTROLS);
  if (sheet) sheet.getRange('B1').clearContent();
}

/**
 * URL for Cursor intake/review write-back (this deployment's doPost).
 * Cursor cloud is outside Trimble SSO, so never send
 * script.google.com/a/macros/trimble.com/... (that 404s as "Page Not Found").
 * Prefer REVIEW_LEDGER_POST_URL = the "Anyone" /exec URL from Deploy.
 */
function getReviewProxyUrl() {
  const configured = getProperty('REVIEW_LEDGER_POST_URL');
  if (configured) return publicExecUrl(configured);
  try {
    return publicExecUrl(ScriptApp.getService().getUrl());
  } catch (_) {
    return '';
  }
}

function publicExecUrl(url) {
  return String(url || '').trim().replace(
    '://script.google.com/a/macros/trimble.com/s/',
    '://script.google.com/macros/s/'
  );
}

function safeError(error) {
  return String(error && error.message ? error.message : error).slice(0, 500);
}

/** Public pilot Issue Scaffolding webhook (Bearer token is a secret — set in Script Properties or Approve env). */
const PILOT_ISSUE_SCAFFOLDING_WEBHOOK_URL =
  'https://api2.cursor.sh/automations/webhook/288c955b-aaad-11f1-b532-320a589b8025';

function scaffoldingResultFileName(idempotencyKey) {
  const slug = String(idempotencyKey || '')
    .replace(/:/g, '-')
    .replace(/[^\w-]/g, '');
  return `scaffolding-result-${slug}.json`;
}

function readScaffoldingResult(idempotencyKey) {
  const folder = getWritebackPendingFolder();
  const name = scaffoldingResultFileName(idempotencyKey);
  const files = folder.getFilesByName(name);
  if (!files.hasNext()) return null;
  return JSON.parse(files.next().getBlob().getDataAsString());
}

/**
 * Poll Drive for scaffolding-result-*.json (Approve automation primary signal).
 * Default: 8 attempts × 15s (~2 min).
 */
function pollScaffoldingResult(idempotencyKey, maxAttempts, sleepMs) {
  const attempts = Number(maxAttempts || 8);
  const pause = Number(sleepMs || 15000);
  const expectedFile = scaffoldingResultFileName(idempotencyKey);
  for (let i = 0; i < attempts; i += 1) {
    const result = readScaffoldingResult(idempotencyKey);
    if (result) {
      return { ok: true, attempt: i + 1, expectedFile, result };
    }
    Utilities.sleep(pause);
  }
  return { ok: false, error: 'timeout', idempotencyKey, expectedFile, attempts };
}

/** Set ISSUE_SCAFFOLDING_WEBHOOK_URL on the orchestrator (token must be added separately). */
function configureScaffoldingWebhookUrl() {
  PropertiesService.getScriptProperties().setProperty(
    'ISSUE_SCAFFOLDING_WEBHOOK_URL',
    PILOT_ISSUE_SCAFFOLDING_WEBHOOK_URL
  );
  Logger.log(`Set ISSUE_SCAFFOLDING_WEBHOOK_URL. Add ISSUE_SCAFFOLDING_WEBHOOK_TOKEN in Script Properties.`);
  return readScaffoldingSheetTestPreflight();
}

/**
 * Preflight for Issue Scaffolding v2 sheet-pilot test (see docs/pilot/scaffolding-sheet-test-execution.md).
 */
function readScaffoldingSheetTestPreflight() {
  const config = readConfigStatus();
  const folderId = getWritebackPendingFolderId();
  return {
    ok: config.configured && Boolean(folderId),
    orchestratorConfigured: config.configured,
    dispatchInFlight: (() => {
      try {
        return isDispatchInFlight(readDispatch(openConfiguredSpreadsheet()));
      } catch (_) {
        return null;
      }
    })(),
    writebackFolderId: folderId || '',
    issueScaffoldingUrlSet: config.issueScaffoldingUrlSet,
    issueScaffoldingTokenSet: config.issueScaffoldingTokenSet,
    approveEnvFallback:
      'If Script Properties are unset, Approve Cloud Agent env ISSUE_SCAFFOLDING_WEBHOOK_* must be set.',
    pilotWebhookUrl: PILOT_ISSUE_SCAFFOLDING_WEBHOOK_URL,
    missing: config.missing,
  };
}

/** Phase A — T3b clarification: seed pilot rows, isolate spinner row, dispatch approve. */
function runScaffoldingSheetTestPhaseA_T3bClarify() {
  seedPilotTestRows();
  const itemId = `${PILOT_MEETING_DOC_ID}:ReviewItems:3`;
  isolateSingleRowForApprove(itemId);
  resetCursorDispatch();
  triggerApproveFromScript();
  const idempotencyKey = buildIdempotencyKey(PILOT_REVIEW_ID, itemId);
  Logger.log(
    `Phase A dispatched. Poll with pollScaffoldingResult('${idempotencyKey}'). ` +
    `Expect verdict need_clarification.`
  );
  return { phase: 'A', itemId, idempotencyKey, expectedFile: scaffoldingResultFileName(idempotencyKey) };
}

/** Phase B — T3a happy path on pilot meeting doc (ReviewItems:2). */
function runScaffoldingSheetTestPhaseB_T3aHappy() {
  seedPilotTestRows();
  const itemId = `${PILOT_MEETING_DOC_ID}:ReviewItems:2`;
  isolateSingleRowForApprove(itemId);
  resetCursorDispatch();
  triggerApproveFromScript();
  const idempotencyKey = buildIdempotencyKey(PILOT_REVIEW_ID, itemId);
  Logger.log(
    `Phase B dispatched. Poll with pollScaffoldingResult('${idempotencyKey}'). ` +
    `Expect verdict issue_created and GitHub issue with Sources.`
  );
  return { phase: 'B', itemId, idempotencyKey, expectedFile: scaffoldingResultFileName(idempotencyKey) };
}

/** Phase B alt — T1 happy-path row (ReviewItems:3) after Phase A passes. */
function runScaffoldingSheetTestPhaseB_T1Happy() {
  seedT1HappyPathRow();
  const itemId = `${T1_MEETING_DOC_ID}:ReviewItems:3`;
  isolateSingleRowForApprove(itemId);
  resetCursorDispatch();
  triggerApproveFromScript();
  const idempotencyKey = buildIdempotencyKey(T1_REVIEW_ID, itemId);
  Logger.log(`Phase B (T1) dispatched. Poll idempotencyKey=${idempotencyKey}`);
  return { phase: 'B-T1', itemId, idempotencyKey, expectedFile: scaffoldingResultFileName(idempotencyKey) };
}

/** Phase C — re-approve same row; Approve should skip second Scaffolding POST (T4a). */
function runScaffoldingSheetTestPhaseC_T4aIdempotency() {
  const itemId = `${PILOT_MEETING_DOC_ID}:ReviewItems:2`;
  isolateSingleRowForApprove(itemId);
  resetCursorDispatch();
  triggerApproveFromScript();
  Logger.log('Phase C dispatched. Expect Approve skip (no new issue). Check Approve run log.');
  return { phase: 'C', itemId, note: 'Verify Approve skipped POST when issueUrl already set' };
}

function runScaffoldingSheetTestCleanup() {
  return restoreIsolatedApproveSkips();
}

/** After approve dispatch, run from editor: poll + relay write-back. */
function pollScaffoldingResultAndRelayWriteback(idempotencyKey) {
  const polled = pollScaffoldingResult(idempotencyKey);
  if (polled.ok) {
    scanWritebackPendingRelay();
  }
  return polled;
}

function assertScaffoldingVerdict(polled, expectedVerdict) {
  if (!polled.ok) {
    throw new Error(`Poll failed: ${JSON.stringify(polled)}`);
  }
  const verdict = String(polled.result.verdict || '').trim();
  if (verdict !== expectedVerdict) {
    throw new Error(`Expected verdict ${expectedVerdict}, got ${verdict}: ${JSON.stringify(polled.result)}`);
  }
  return polled;
}

/**
 * Phase A with poll (~2 min blocking). Run from editor after deploying orchestrator.
 * Logs PASS/FAIL to Execution log.
 */
function runScaffoldingSheetTestPhaseAWithPoll() {
  const dispatched = runScaffoldingSheetTestPhaseA_T3bClarify();
  const polled = pollScaffoldingResultAndRelayWriteback(dispatched.idempotencyKey);
  assertScaffoldingVerdict(polled, 'need_clarification');
  if (polled.result.issueUrl) {
    throw new Error('Clarification path must not set issueUrl');
  }
  Logger.log(`PASS Phase A T3b clarification: ${JSON.stringify(polled.result)}`);
  return { pass: true, phase: 'A', polled };
}

/**
 * Phase B with poll (~2 min blocking). Run after Phase A passes.
 */
function runScaffoldingSheetTestPhaseBWithPoll() {
  const dispatched = runScaffoldingSheetTestPhaseB_T3aHappy();
  const polled = pollScaffoldingResultAndRelayWriteback(dispatched.idempotencyKey);
  assertScaffoldingVerdict(polled, 'issue_created');
  if (!polled.result.issueUrl) {
    throw new Error('Happy path must set issueUrl');
  }
  Logger.log(`PASS Phase B T3a happy: ${JSON.stringify(polled.result)}`);
  return { pass: true, phase: 'B', polled };
}

function formatCellValue(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value;
  if (Array.isArray(value) || typeof value === 'object') return JSON.stringify(value);
  return value;
}

function jsonResponse(value, status) {
  return ContentService.createTextOutput(JSON.stringify({ ...value, status: status || 200 }))
    .setMimeType(ContentService.MimeType.JSON);
}
