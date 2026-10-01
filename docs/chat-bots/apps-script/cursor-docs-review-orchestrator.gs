/**
 * Document-led Cursor review orchestrator.
 *
 * Cursor POSTs the initial intake payload; Apps Script writes the review ledger
 * and polls the command column for the next review round.
 *
 * Required Script Properties:
 *   REVIEW_DOC_ID
 *   CURSOR_REVIEW_CALLBACK_URL
 *   CURSOR_INGRESS_TOKEN
 *
 * Optional:
 *   REVIEW_SOURCE_ALLOWLIST (comma-separated document IDs)
 *   REVIEW_POLL_MINUTES (1, 5, 10, 15, 30)
 *   DRY_RUN_REVIEW (true — skip Cursor POST and echo updates into the doc)
 */

const REVIEW_HEADERS = [
  'itemId', 'round', 'sourceExcerpt', 'classification', 'rationale',
  'duplicateCandidates', 'title', 'summary', 'owner', 'designNeeded',
  'acceptanceCriteria', 'status', 'skipIssue', 'reviewerComment', 'cursorComment',
  'command', 'iterationCount', 'issueStatus', 'issueNumber', 'issueUrl',
  'lastError', 'updatedAt',
];

/** Columns reviewers edit in the main table; the rest live in ReviewItemsDetail.payload. */
const REVIEW_SURFACE_HEADERS = [
  'itemId', 'round', 'title', 'classification', 'status', 'skipIssue',
  'reviewerComment', 'cursorComment', 'command', 'iterationCount',
  'issueNumber', 'issueUrl', 'updatedAt',
];

const TRIGGER_COMMANDS = [
  '@cursor-review',
  'review',
  'approve',
  'reject',
];

const REVIEW_PAYLOAD_FIELDS = REVIEW_HEADERS.filter(
  (name) => REVIEW_SURFACE_HEADERS.indexOf(name) === -1
);

const ISSUE_HEADERS = [
  'itemId', 'idempotencyKey', 'status', 'issueNumber', 'issueUrl',
  'createdAt', 'lastError', 'reviewComment',
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    const body = parseJsonBody(e);
    requireToken(body.ingressToken);
    const reviewId = String(body.reviewId || '').trim();
    const docId = String(body.docId || '').trim();
    if (!reviewId || !docId) throw new Error('reviewId and docId are required');
    assertAllowedDocument(docId);

    const document = DocumentApp.openById(docId);
    ensureLedgerTables(document);
    const items = Array.isArray(body.items) ? body.items : [];
    upsertItems(document, items, Number(body.round || 1));
    writeState(document, {
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
  return jsonResponse({
    ok: true,
    service: 'cursor-docs-review-orchestrator',
    configured: Boolean(getProperty('REVIEW_DOC_ID') &&
      getProperty('CURSOR_REVIEW_CALLBACK_URL') &&
      getProperty('CURSOR_INGRESS_TOKEN')),
    dryRun: isDryRunEnabled(),
    pollMinutes: normalizePollMinutes(getProperty('REVIEW_POLL_MINUTES') || 5),
  });
}

function installReviewTrigger() {
  ScriptApp.getProjectTriggers()
    .filter((trigger) => trigger.getHandlerFunction() === 'scanReviewDocument')
    .forEach((trigger) => ScriptApp.deleteTrigger(trigger));

  const minutes = normalizePollMinutes(getProperty('REVIEW_POLL_MINUTES') || 5);
  ScriptApp.newTrigger('scanReviewDocument')
    .timeBased()
    .everyMinutes(minutes)
    .create();
}

/**
 * One-time setup for poll-based dry-run testing.
 * Sets DRY_RUN_REVIEW=true, polls every minute, then waits for command edits.
 */
function installDryRunPolling() {
  const props = PropertiesService.getScriptProperties();
  props.setProperty('DRY_RUN_REVIEW', 'true');
  props.setProperty('REVIEW_POLL_MINUTES', '1');
  installReviewTrigger();
}

function scanReviewDocument() {
  runReviewScan(false);
}

/**
 * Dry-run the review trigger loop without Cursor.
 * Run from the Apps Script editor after setting command to @cursor-review.
 */
function testReviewTriggerNow() {
  runReviewScan(true);
}

function runReviewScan(forceDryRun) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    const docId = getProperty('REVIEW_DOC_ID');
    if (!docId) throw new Error('REVIEW_DOC_ID is not configured');
    const document = DocumentApp.openById(docId);
    const dryRun = forceDryRun || isDryRunEnabled();
    let state = readState(document);
    if (dryRun && (state.state === 'claimed' || state.state === 'running')) {
      state = { ...state, state: 'idle', lastError: null };
      writeState(document, state);
    }
    const rows = readTableRows(document, 'ReviewItems');
    const changedRows = findTriggeredRows(rows);
    if (!changedRows.length || state.state === 'running' || state.state === 'claimed') return;

    const nextRound = Number(state.round || 0) + 1;
    markRowsInProgress(document, changedRows, nextRound);
    writeState(document, {
      ...state,
      round: nextRound,
      state: 'claimed',
      claimedAt: new Date().toISOString(),
      claimedBy: dryRun ? 'apps-script-dry-run' : 'apps-script',
      lastError: null,
    });

    const payload = {
      reviewId: state.reviewId || `meeting:${docId}`,
      docId,
      round: nextRound,
      command: 'mixed',
      items: changedRows.map((row) => ({
        ...row,
        rowAction: normalizeCommand(row),
      })),
      reviewRevision: document.getRevisionId ? document.getRevisionId() : '',
    };
    const response = dryRun ? buildDryRunReviewResponse(payload) : callCursor(payload);
    writeState(document, {
      ...state,
      round: nextRound,
      state: response.ok ? 'completed' : 'failed',
      lastProcessedRevision: response.reviewRevision || '',
      claimedAt: state.claimedAt,
      claimedBy: dryRun ? 'apps-script-dry-run' : 'apps-script',
      lastError: response.ok ? null : response.error,
    });
    if (response.itemUpdates) upsertItems(document, response.itemUpdates, nextRound);
    if (response.issueResults) appendIssueResults(document, response.issueResults);
    if (response.ok) clearProcessedCommands(document, changedRows);
    if (dryRun) appendDryRunNotice(document, nextRound, changedRows.length, response.ok);
  } catch (error) {
    const docId = getProperty('REVIEW_DOC_ID');
    if (docId) {
      const document = DocumentApp.openById(docId);
      const state = readState(document);
      writeState(document, { ...state, state: 'failed', lastError: safeError(error) });
    }
    throw error;
  } finally {
    lock.releaseLock();
  }
}

function isDryRunEnabled() {
  const flag = getProperty('DRY_RUN_REVIEW').toLowerCase();
  if (flag === 'true') return true;
  if (flag === 'false') return false;
  return !getProperty('CURSOR_REVIEW_CALLBACK_URL');
}

function normalizePollMinutes(value) {
  const allowed = [1, 5, 10, 15, 30];
  const minutes = Number(value);
  return allowed.indexOf(minutes) === -1 ? 5 : minutes;
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
      return {
        itemId: item.itemId || item._itemId,
        command: '',
        status,
        iterationCount,
        cursorComment: `[dry-run ${action} round ${payload.round} @ ${stamp}]`,
      };
    }),
  };
}

function findTriggeredRows(rows) {
  return rows.filter((row) => {
    const command = normalizeCommand(row);
    if (!command) return false;
    if (command === 'approve-all') return false;
    if (command === 'approve' && isSkipIssue(row)) return false;
    if (TRIGGER_COMMANDS.indexOf(command) !== -1) return true;
    return command.indexOf('changes-requested:') === 0 || command.indexOf('duplicate:') === 0;
  });
}

function normalizeCommand(row) {
  return String(row.command || '').trim().toLowerCase();
}

function isSkipIssue(row) {
  const value = String(row.skipIssue || '').trim().toLowerCase();
  return value === 'true' || value === 'yes' || value === '1' || value === 'x';
}

function markRowsInProgress(document, rows, round) {
  upsertItems(document, rows.map((row) => ({
    itemId: row.itemId || row._itemId,
    status: 'in-progress',
  })), round);
}

function appendDryRunNotice(document, round, itemCount, ok) {
  const body = document.getBody();
  body.appendParagraph(
    `Dry-run round ${round} ${ok ? 'completed' : 'failed'} for ${itemCount} item(s) @ ${new Date().toISOString()}`
  ).setItalic(true);
}

/** Clear trigger commands so the next poll does not fire the same row again. */
function clearProcessedCommands(document, rows) {
  const table = findTable(document.getBody().getTables(), 'ReviewItems');
  if (!table) return;
  const header = readHeaderRow(table);
  const index = indexByHeader(header);
  if (index.command === undefined) return;
  rows.forEach((row) => {
    const itemId = String(row.itemId || row._itemId || '').trim();
    if (!itemId) return;
    const existing = findRow(table, index.itemId, itemId);
    if (!existing) return;
    existing.getCell(index.command).setText('');
  });
}

function callCursor(payload) {
  const response = UrlFetchApp.fetch(getProperty('CURSOR_REVIEW_CALLBACK_URL'), {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: { Authorization: `Bearer ${getProperty('CURSOR_INGRESS_TOKEN')}` },
    payload: JSON.stringify(payload),
  });
  const code = response.getResponseCode();
  const body = response.getContentText();
  let parsed = {};
  try { parsed = JSON.parse(body); } catch (_) {}
  if (code < 200 || code >= 300 || parsed.ok === false) {
    return { ok: false, error: `Cursor callback failed (${code})` };
  }
  return parsed;
}

function ensureLedgerTables(document) {
  const body = document.getBody();
  const tables = body.getTables();
  let reviewTable = findTable(tables, 'ReviewItems');
  if (!reviewTable) {
    reviewTable = body.appendTable([['ReviewItems'].concat(REVIEW_SURFACE_HEADERS)]);
  }
  reflowLedgerTable(document, reviewTable);

  let detailTable = findTable(body.getTables(), 'ReviewItemsDetail');
  if (!detailTable) {
    detailTable = body.appendTable([['ReviewItemsDetail', 'itemId', 'payload']]);
  }
  reflowLedgerTable(document, detailTable);

  let issuesTable = findTable(body.getTables(), 'Issues');
  if (!issuesTable) {
    issuesTable = body.appendTable([['Issues'].concat(ISSUE_HEADERS)]);
  }
  reflowLedgerTable(document, issuesTable);
}

function upsertItems(document, items, round) {
  const table = findTable(document.getBody().getTables(), 'ReviewItems');
  if (!table) throw new Error('ReviewItems table is missing');
  const detailTable = findTable(document.getBody().getTables(), 'ReviewItemsDetail');
  if (!detailTable) throw new Error('ReviewItemsDetail table is missing');
  const header = readHeaderRow(table);
  const index = indexByHeader(header);
  items.forEach((item) => {
    const itemId = String(item.itemId || item.id || '').trim();
    if (!itemId) return;
    const existing = findRow(table, index.itemId, itemId);
    const row = existing || table.appendTableRow();
    ensureRowCells(row, header.length);
    REVIEW_SURFACE_HEADERS.forEach((name) => {
      const cell = cellFor(row, index[name]);
      if (!cell) return;
      if (!Object.prototype.hasOwnProperty.call(item, name) && name !== 'updatedAt') {
        if (name === 'round' && item.round === undefined) {
          cell.setText(formatValue(round));
        }
        return;
      }
      const value = item[name] ?? (name === 'round' ? round : '');
      cell.setText(formatValue(value));
    });
    const updatedAtCell = cellFor(row, index.updatedAt);
    if (updatedAtCell) updatedAtCell.setText(new Date().toISOString());
    if (!existing && cellFor(row, index.status) && !String(item.status || '').trim()) {
      cellFor(row, index.status).setText('needs-review');
    }
    upsertDetailPayload(detailTable, itemId, buildPayloadFields(item, round));
  });
}

function buildPayloadFields(item, round) {
  const payload = {};
  REVIEW_PAYLOAD_FIELDS.forEach((name) => {
    const value = item[name] ?? (name === 'round' ? round : '');
    if (value !== '') payload[name] = value;
  });
  return payload;
}

function upsertDetailPayload(table, itemId, payload) {
  const header = readHeaderRow(table);
  const index = indexByHeader(header);
  const existing = findRow(table, index.itemId, itemId);
  const row = existing || table.appendTableRow();
  ensureRowCells(row, header.length);
  row.getCell(0).setText('');
  cellFor(row, index.itemId).setText(itemId);
  cellFor(row, index.payload).setText(JSON.stringify(payload));
}

function appendIssueResults(document, results) {
  const table = findTable(document.getBody().getTables(), 'Issues');
  if (!table) throw new Error('Issues table is missing');
  const header = readHeaderRow(table);
  const index = indexByHeader(header);
  results.forEach((result) => {
    const row = table.appendTableRow();
    ensureRowCells(row, header.length);
    ISSUE_HEADERS.forEach((name) => {
      const value = result[name] ?? '';
      cellFor(row, index[name]).setText(formatValue(value));
    });
  });
}

function readTableRows(document, name) {
  const table = findTable(document.getBody().getTables(), name);
  if (!table) return [];
  const header = readHeaderRow(table);
  const index = indexByHeader(header);
  const legacyWideTable = name === 'ReviewItems' && header.indexOf('sourceExcerpt') !== -1;
  const detailByItemId = legacyWideTable
    ? {}
    : readDetailPayloads(findTable(document.getBody().getTables(), 'ReviewItemsDetail'));
  const rows = [];
  for (let i = 1; i < table.getNumRows(); i += 1) {
    const row = table.getRow(i);
    const value = {};
    header.forEach((key, position) => {
      value[key] = row.getCell(position).getText().trim();
    });
    value._row = i;
    value._itemId = value.itemId;
    if (!legacyWideTable && value.itemId && detailByItemId[value.itemId]) {
      Object.assign(value, detailByItemId[value.itemId]);
    }
    rows.push(value);
  }
  return rows;
}

function readDetailPayloads(table) {
  if (!table) return {};
  const header = readHeaderRow(table);
  const index = indexByHeader(header);
  const payloads = {};
  for (let i = 1; i < table.getNumRows(); i += 1) {
    const itemId = table.getCell(i, index.itemId).getText().trim();
    const payloadText = table.getCell(i, index.payload).getText().trim();
    if (!itemId || !payloadText) continue;
    try {
      payloads[itemId] = JSON.parse(payloadText);
    } catch (_) {
      payloads[itemId] = {};
    }
  }
  return payloads;
}

function readHeaderRow(table) {
  const row = table.getRow(0);
  const header = [];
  for (let column = 0; column < row.getNumCells(); column += 1) {
    header.push(row.getCell(column).getText().trim());
  }
  return header;
}

function readState(document) {
  const state = PropertiesService.getDocumentProperties();
  return JSON.parse(state.getProperty('REVIEW_STATE') || JSON.stringify({
    reviewId: `meeting:${document.getId()}`,
    round: 0,
    state: 'idle',
    lastProcessedRevision: '',
    claimedAt: '',
    claimedBy: '',
    lastError: null,
  }));
}

function writeState(_, value) {
  PropertiesService.getDocumentProperties().setProperty('REVIEW_STATE', JSON.stringify(value));
}

function findTable(tables, name) {
  return tables.find((table) => table.getCell(0, 0).getText().trim() === name);
}

function findRow(table, itemColumn, itemId) {
  for (let i = 1; i < table.getNumRows(); i += 1) {
    if (table.getCell(i, itemColumn).getText().trim() === itemId) return table.getRow(i);
  }
  return null;
}

function cellFor(row, position) {
  return position === undefined ? null : row.getCell(position);
}

function ensureRowCells(row, count) {
  while (row.getNumCells() < count) row.appendTableCell('');
}

function indexByHeader(header) {
  return header.reduce((result, name, position) => {
    result[name] = position;
    return result;
  }, {});
}

function formatValue(value) {
  return Array.isArray(value) || typeof value === 'object' ? JSON.stringify(value) : String(value);
}

function parseJsonBody(e) {
  const contents = e && e.postData && e.postData.contents;
  if (!contents) throw new Error('JSON request body is required');
  const value = JSON.parse(contents);
  if (!value || typeof value !== 'object') throw new Error('JSON body must be an object');
  return value;
}

function requireToken(token) {
  if (!token || token !== getProperty('CURSOR_INGRESS_TOKEN')) {
    throw new Error('Invalid ingress token');
  }
}

function assertAllowedDocument(docId) {
  const configured = getProperty('REVIEW_SOURCE_ALLOWLIST');
  const allowed = configured ? configured.split(',').map((item) => item.trim()) : [getProperty('REVIEW_DOC_ID')];
  if (!allowed.includes(docId)) throw new Error('Document is not allowlisted');
}

function getProperty(name) {
  return String(PropertiesService.getScriptProperties().getProperty(name) || '').trim();
}

function safeError(error) {
  return String(error && error.message ? error.message : error).slice(0, 500);
}

function jsonResponse(value, status) {
  return ContentService.createTextOutput(JSON.stringify({ ...value, status: status || 200 }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Demo helper: run once from the Apps Script editor.
 * Extensions → Apps Script → createReviewLedgerDemo → Run.
 */
function createReviewLedgerDemo() {
  const docId = getProperty('REVIEW_DOC_ID');
  const document = docId
    ? DocumentApp.openById(docId)
    : DocumentApp.getActiveDocument();
  const body = document.getBody();

  body.appendParagraph('Review ledger demo')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph(
    'Edit ReviewItems below. reviewerComment never triggers; only command does. ' +
    'Set skipIssue=TRUE for rows that must not become issues.'
  );

  body.appendParagraph('ReviewItems (review surface)')
    .setHeading(DocumentApp.ParagraphHeading.HEADING3);
  const reviewTable = body.appendTable([['ReviewItems'].concat(REVIEW_SURFACE_HEADERS)]);
  reflowLedgerTable(document, reviewTable);

  body.appendParagraph('ReviewItemsDetail (machine payload)')
    .setHeading(DocumentApp.ParagraphHeading.HEADING3);
  const detailTable = body.appendTable([['ReviewItemsDetail', 'itemId', 'payload']]);
  reflowLedgerTable(document, detailTable);

  upsertItems(document, [
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

  body.appendParagraph('Created issues')
    .setHeading(DocumentApp.ParagraphHeading.HEADING3);
  const issuesTable = body.appendTable([
    ['Issues'].concat(ISSUE_HEADERS),
    ['Issues', 'demo-item-001', 'gemini:demo:demo-item-001', 'pending', '', '', new Date().toISOString(), '', ''],
  ]);
  reflowLedgerTable(document, issuesTable);

  writeState(document, {
    reviewId: `meeting:${document.getId()}`,
    round: 0,
    state: 'idle',
    lastProcessedRevision: '',
    claimedAt: '',
    claimedBy: '',
    lastError: null,
  });
}

/**
 * Resize an existing ledger table to fit the current page width.
 * Run from the Apps Script editor after pasting an older ledger into a doc.
 */
function reflowExistingLedgerTables() {
  const docId = getProperty('REVIEW_DOC_ID');
  const document = docId
    ? DocumentApp.openById(docId)
    : DocumentApp.getActiveDocument();
  const tables = document.getBody().getTables();
  const reviewTable = findTable(tables, 'ReviewItems');
  const detailTable = findTable(tables, 'ReviewItemsDetail');
  const issuesTable = findTable(tables, 'Issues');
  if (reviewTable) reflowLedgerTable(document, reviewTable);
  if (detailTable) reflowLedgerTable(document, detailTable);
  if (issuesTable) reflowLedgerTable(document, issuesTable);
}

function getPageContentWidthPt(document) {
  const body = document.getBody();
  return body.getPageWidth() - body.getMarginLeft() - body.getMarginRight();
}

function reflowLedgerTable(document, table) {
  sizeLedgerTable(document, table);
  compactLedgerTable(table);
}

function compactLedgerTable(table) {
  for (let rowIndex = 0; rowIndex < table.getNumRows(); rowIndex += 1) {
    const row = table.getRow(rowIndex);
    for (let column = 0; column < row.getNumCells(); column += 1) {
      row.getCell(column).editAsText().setFontSize(9);
    }
  }
}

/** Scale column widths to the page so the table stays inside the document body. */
function sizeLedgerTable(document, table) {
  const header = readHeaderRow(table);
  const tableName = header[0];
  const maxWidth = getPageContentWidthPt(document);

  if (tableName === 'ReviewItemsDetail') {
    const labelWidth = 36;
    const itemIdWidth = 96;
    table.setColumnWidth(0, labelWidth);
    table.setColumnWidth(1, itemIdWidth);
    table.setColumnWidth(2, Math.max(120, maxWidth - labelWidth - itemIdWidth));
    return;
  }

  const preferred = {
    0: 36,
    itemId: 96,
    round: 36,
    title: 120,
    classification: 88,
    status: 72,
    skipIssue: 48,
    reviewerComment: 120,
    cursorComment: 120,
    command: 88,
    iterationCount: 48,
    issueNumber: 56,
    issueUrl: 120,
    updatedAt: 96,
    idempotencyKey: 120,
    createdAt: 96,
    lastError: 96,
    reviewComment: 120,
  };
  const columnCount = table.getRow(0).getNumCells();
  const weights = [];
  for (let column = 0; column < columnCount; column += 1) {
    const key = header[column] || String(column);
    weights.push(preferred[key] || 72);
  }
  const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
  const scale = totalWeight > maxWidth ? maxWidth / totalWeight : 1;
  let assigned = 0;
  for (let column = 0; column < columnCount; column += 1) {
    const isLast = column === columnCount - 1;
    const width = isLast
      ? Math.max(36, maxWidth - assigned)
      : Math.max(36, Math.round(weights[column] * scale));
    table.setColumnWidth(column, width);
    assigned += width;
  }
}
