/**
 * Gemini meeting-notes → Cursor intake coordinator (Apps Script).
 *
 * Replaces the n8n Gmail watcher for the sheet-led review path. Polls Gmail for
 * Modus Sprint Planning / Sprint Estimating notes from Gemini, extracts the
 * linked Google Doc ID, deduplicates, and POSTs to the Cursor Meeting Intake
 * automation webhook. Cursor classifies notes and writes
 * intake-pending-<docId>.json to Drive; this project relays rows to the review
 * ledger via UrlFetchApp (external Cursor POST to GAS /exec fails on 302/405).
 *
 * Deploy as a **standalone** Apps Script project (not bound to the sheet).
 *
 * Required Script Properties:
 *   CURSOR_MEETING_INTAKE_WEBHOOK_URL   Cursor automation webhook URL
 *   CURSOR_INGRESS_TOKEN                Bearer token for Cursor webhook
 *   REVIEW_SHEET_ID                     Review ledger spreadsheet ID
 *   REVIEW_LEDGER_POST_URL              Deployed web app URL (sheet orchestrator doPost)
 *   CURSOR_REVIEW_INGRESS_TOKEN         Must match orchestrator review token (ledger relay)
 *   INTAKE_PENDING_FOLDER_ID            Drive folder for intake-pending-<docId>.json
 *
 * Optional:
 *   GEMINI_GMAIL_QUERY                  Override Gmail search query
 *   GEMINI_POLL_MINUTES                 5 | 10 | 15 | 30 (default 5)
 *   TARGET_REPO                         owner/repo for Cursor (pilot default below)
 *   TARGET_BRANCH                       default main
 *   SPRINT_PLANNING_SERIES_ID           Calendar recurringEventId allowlist entry
 *   SPRINT_ESTIMATING_SERIES_ID         Calendar recurringEventId allowlist entry
 *   MODUS_ROSTER                        comma-separated emails for calendar fallback
 *
 * Setup:
 *   1. Enable Gmail API / authorize GmailApp on first run
 *   2. Set script properties above
 *   3. Run installGeminiIntakePolling() once
 *   4. Deploy sheet orchestrator as web app; paste exec URL into REVIEW_LEDGER_POST_URL
 *
 * Manual test (no Gmail):
 *   testDispatchDocId('YOUR_MEETING_DOC_ID')
 *
 * One-time pilot property seed (no secrets):
 *   setupPilotProperties()
 */

function setupPilotProperties() {
  const props = PropertiesService.getScriptProperties();
  props.setProperty('REVIEW_SHEET_ID', '1et7NnaPDzpLjZUitRYrRdIExQ6ay2iEmYtCONTSitZ4');
  props.setProperty('TARGET_REPO', 'ElishaSamPeterPrabhu/modus-wc-2.0');
  props.setProperty('TARGET_BRANCH', 'main');
  props.setProperty('GEMINI_POLL_MINUTES', '5');
  Logger.log('Set REVIEW_SHEET_ID and defaults. Still required: CURSOR_MEETING_INTAKE_WEBHOOK_URL, CURSOR_INGRESS_TOKEN, CURSOR_REVIEW_INGRESS_TOKEN, REVIEW_LEDGER_POST_URL, INTAKE_PENDING_FOLDER_ID');
}

const GEMINI_FROM = 'gemini-notes@google.com';
const ALLOWED_TITLES = ['Sprint Planning', 'Sprint Estimating'];
const DOC_ID_PATTERN = /docs\.google\.com\/document\/d\/([a-zA-Z0-9_-]+)/i;
const TITLE_PATTERN = /^Notes:\s*[“"]?(Sprint Planning|Sprint Estimating)[”"]?\b/i;

function doGet() {
  return jsonResponse({
    ok: true,
    service: 'cursor-gemini-meeting-intake-coordinator',
    configured: Boolean(
      getProperty('CURSOR_MEETING_INTAKE_WEBHOOK_URL') &&
      getProperty('CURSOR_INGRESS_TOKEN') &&
      getProperty('REVIEW_SHEET_ID') &&
      getProperty('REVIEW_LEDGER_POST_URL') &&
      getProperty('INTAKE_PENDING_FOLDER_ID')
    ),
    pollMinutes: normalizePollMinutes(getProperty('GEMINI_POLL_MINUTES') || 5),
    processedDocCount: Object.keys(readDocRegistry()).length,
  });
}

function installGeminiIntakePolling() {
  removeTriggersFor('scanGeminiMeetingNotes');
  const minutes = normalizePollMinutes(getProperty('GEMINI_POLL_MINUTES') || 5);
  ScriptApp.newTrigger('scanGeminiMeetingNotes')
    .timeBased()
    .everyMinutes(minutes)
    .create();
  Logger.log(`Gemini intake polling enabled every ${minutes} minute(s).`);
}

function scanGeminiMeetingNotes() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    const query = getProperty('GEMINI_GMAIL_QUERY') ||
      `from:${GEMINI_FROM} newer_than:7d`;
    const threads = GmailApp.search(query, 0, 25);
    threads.forEach((thread) => {
      thread.getMessages().forEach((message) => processGeminiMessage(message));
    });
    scanIntakePendingRelay();
  } finally {
    lock.releaseLock();
  }
}

function processGeminiMessage(message) {
  if (!message) return;
  const messageId = message.getId();
  if (isMessageProcessed(messageId)) return;

  const subject = String(message.getSubject() || '').trim();
  const titleMatch = subject.match(TITLE_PATTERN);
  if (!titleMatch) return;

  const meetingType = titleMatch[1];
  const body = [message.getBody(), message.getPlainBody()].join('\n');
  const docMatch = body.match(DOC_ID_PATTERN);
  const docId = docMatch ? docMatch[1] : '';
  if (!docId) {
    markMessageSkipped(messageId, 'missing-doc-id');
    return;
  }

  const docRecord = getDocRecord(docId);
  if (docRecord && docRecord.status !== 'failed') {
    markMessageProcessed(messageId, docId, 'duplicate-doc');
    return;
  }

  if (!verifyMeetingIdentity(meetingType, message.getDate())) {
    markMessageSkipped(messageId, 'calendar-gate-failed');
    return;
  }

  const payload = buildCursorIntakePayload({
    docId,
    docUrl: `https://docs.google.com/document/d/${docId}/edit`,
    meetingType,
    meetingDate: message.getDate().toISOString(),
    emailId: messageId,
    subject,
  });

  setDocRecord(docId, {
    status: 'dispatching',
    meetingType,
    messageId,
    startedAt: new Date().toISOString(),
  });

  const result = callCursorMeetingIntake(payload);
  if (result.ok) {
    setDocRecord(docId, {
      status: 'dispatched',
      meetingType,
      messageId,
      reviewId: payload.reviewId,
      dispatchedAt: new Date().toISOString(),
      cursorStatus: result.status,
    });
    markMessageProcessed(messageId, docId, 'dispatched');
    Logger.log(`Dispatched ${docId} → Cursor (${payload.reviewId})`);
    return;
  }

  setDocRecord(docId, {
    status: 'failed',
    meetingType,
    messageId,
    lastError: result.error,
    failedAt: new Date().toISOString(),
  });
  markMessageProcessed(messageId, docId, 'failed');
  Logger.log(`Cursor dispatch failed for ${docId}: ${result.error}`);
}

/**
 * Manual pilot: dispatch one meeting Doc ID without waiting for Gmail poll.
 */
function testDispatchDocId(docId) {
  const normalized = String(docId || '').trim();
  if (!normalized) throw new Error('docId is required');
  const payload = buildCursorIntakePayload({
    docId: normalized,
    docUrl: `https://docs.google.com/document/d/${normalized}/edit`,
    meetingType: 'Sprint Planning',
    meetingDate: new Date().toISOString(),
    emailId: 'manual-test',
    subject: 'Notes: "Sprint Planning" (manual test)',
  });
  const result = callCursorMeetingIntake(payload);
  Logger.log(JSON.stringify(result));
  return result;
}

/** One-click pilot test from the Apps Script editor. */
function runPilotTest() {
  return testDispatchDocId('1Mb2ywudedEXNeZeWKpmmEyWIeUNbxWtrBWauaoZMqD4');
}

/** T1 pipeline test — new meeting Doc (see pilot-test-runbook.md). */
function runT1PipelineTest() {
  return testDispatchDocId('1AMbbKrWc8fmS2CI_jzwoC7KvdygL4Wz9kY3Y861gjYg');
}

function buildCursorIntakePayload(identity) {
  const sheetId = getProperty('REVIEW_SHEET_ID');
  if (!sheetId) throw new Error('REVIEW_SHEET_ID is not configured');
  const reviewProxyUrl = getProperty('REVIEW_LEDGER_POST_URL');
  if (!reviewProxyUrl) throw new Error('REVIEW_LEDGER_POST_URL is not configured');
  const repo = getProperty('TARGET_REPO') || 'ElishaSamPeterPrabhu/modus-wc-2.0';
  const branch = getProperty('TARGET_BRANCH') || 'main';
  const intakePendingFolderId = getProperty('INTAKE_PENDING_FOLDER_ID');
  return {
    reviewId: `meeting:${identity.docId}`,
    docId: identity.docId,
    docUrl: identity.docUrl,
    sheetId,
    meetingType: identity.meetingType,
    meetingDate: identity.meetingDate,
    emailId: identity.emailId,
    subject: identity.subject,
    reviewProxyUrl,
    ingressToken: getProperty('CURSOR_REVIEW_INGRESS_TOKEN') ||
      getProperty('CURSOR_INGRESS_TOKEN'),
    intakePendingFolderId,
    repo,
    branch,
    source: 'Gemini meeting notes',
  };
}

/**
 * POST classified items to the sheet orchestrator (Google-side; handles 302).
 */
function postItemsToLedger(items, reviewId, round) {
  const url = getProperty('REVIEW_LEDGER_POST_URL');
  const token = getProperty('CURSOR_REVIEW_INGRESS_TOKEN') ||
    getProperty('CURSOR_INGRESS_TOKEN');
  const sheetId = getProperty('REVIEW_SHEET_ID');
  if (!url) throw new Error('REVIEW_LEDGER_POST_URL is not configured');
  if (!token) throw new Error('CURSOR_REVIEW_INGRESS_TOKEN or CURSOR_INGRESS_TOKEN is not configured');
  if (!sheetId) throw new Error('REVIEW_SHEET_ID is not configured');

  const payload = {
    ingressToken: token,
    reviewId: String(reviewId || '').trim(),
    sheetId,
    round: Number(round || 1),
    items: Array.isArray(items) ? items : [],
  };
  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    followRedirects: true,
    muteHttpExceptions: true,
  });
  const status = response.getResponseCode();
  const body = response.getContentText();
  let parsed = {};
  try {
    parsed = JSON.parse(body);
  } catch (_) {
    parsed = {};
  }
  const ok = status >= 200 && status < 300 && parsed.ok !== false;
  return { ok, status, body, parsed };
}

function intakePendingFileName(docId) {
  return `intake-pending-${String(docId || '').trim()}.json`;
}

function intakeRelayedFileName(docId) {
  return `intake-relayed-${String(docId || '').trim()}.json`;
}

function getIntakePendingFolder() {
  const folderId = getProperty('INTAKE_PENDING_FOLDER_ID');
  if (!folderId) throw new Error('INTAKE_PENDING_FOLDER_ID is not configured');
  return DriveApp.getFolderById(folderId);
}

function readIntakePendingPayload(docId) {
  const normalized = String(docId || '').trim();
  if (!normalized) throw new Error('docId is required');
  const folder = getIntakePendingFolder();
  const files = folder.getFilesByName(intakePendingFileName(normalized));
  if (!files.hasNext()) return null;
  const file = files.next();
  return JSON.parse(file.getBlob().getDataAsString());
}

function archiveIntakePendingFile(docId) {
  const normalized = String(docId || '').trim();
  const folder = getIntakePendingFolder();
  const files = folder.getFilesByName(intakePendingFileName(normalized));
  if (!files.hasNext()) return;
  const file = files.next();
  const relayedName = intakeRelayedFileName(normalized);
  const existing = folder.getFilesByName(relayedName);
  while (existing.hasNext()) {
    existing.next().setTrashed(true);
  }
  file.setName(relayedName);
}

/**
 * Read intake-pending-<docId>.json from Drive and POST items to the ledger.
 */
function relayIntakePendingForDoc(docId) {
  const normalized = String(docId || '').trim();
  if (!normalized) throw new Error('docId is required');
  const payload = readIntakePendingPayload(normalized);
  if (!payload) {
    return { ok: false, error: 'pending file not found', docId: normalized };
  }
  const reviewId = String(payload.reviewId || `meeting:${normalized}`).trim();
  const result = postItemsToLedger(payload.items, reviewId, payload.round || 1);
  if (result.ok) {
    archiveIntakePendingFile(normalized);
    setDocRecord(normalized, {
      status: 'relayed',
      reviewId,
      relayedAt: new Date().toISOString(),
      ledgerStatus: result.status,
      itemCount: (payload.items || []).length,
    });
  } else {
    setDocRecord(normalized, {
      status: 'relay-failed',
      reviewId,
      lastRelayError: result.body || String(result.status),
      relayFailedAt: new Date().toISOString(),
    });
  }
  Logger.log(JSON.stringify({ docId: normalized, ...result }));
  return result;
}

/** Process every intake-pending-*.json in INTAKE_PENDING_FOLDER_ID. */
function scanIntakePendingRelay() {
  const folderId = getProperty('INTAKE_PENDING_FOLDER_ID');
  if (!folderId) return { ok: false, skipped: true, reason: 'INTAKE_PENDING_FOLDER_ID unset' };
  const folder = DriveApp.getFolderById(folderId);
  const processed = [];
  const iterator = folder.getFiles();
  while (iterator.hasNext()) {
    const file = iterator.next();
    const match = String(file.getName() || '').match(/^intake-pending-([a-zA-Z0-9_-]+)\.json$/);
    if (!match) continue;
    const docId = match[1];
    try {
      const result = relayIntakePendingForDoc(docId);
      processed.push({ docId, ok: result.ok, status: result.status });
    } catch (error) {
      processed.push({ docId, ok: false, error: safeError(error) });
    }
  }
  if (processed.length) Logger.log(`scanIntakePendingRelay: ${JSON.stringify(processed)}`);
  return { ok: true, processed };
}

function callCursorMeetingIntake(payload) {
  const url = getProperty('CURSOR_MEETING_INTAKE_WEBHOOK_URL');
  if (!url) return { ok: false, error: 'CURSOR_MEETING_INTAKE_WEBHOOK_URL is not configured' };
  const token = getProperty('CURSOR_INGRESS_TOKEN');
  if (!token) return { ok: false, error: 'CURSOR_INGRESS_TOKEN is not configured' };

  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: { Authorization: `Bearer ${token}` },
    payload: JSON.stringify(payload),
  });
  const status = response.getResponseCode();
  const body = response.getContentText();
  if (status < 200 || status >= 300) {
    return { ok: false, error: `Cursor webhook failed (${status})`, body };
  }
  return { ok: true, status, body };
}

function verifyMeetingIdentity(meetingType, meetingDate) {
  const planningId = getProperty('SPRINT_PLANNING_SERIES_ID');
  const estimatingId = getProperty('SPRINT_ESTIMATING_SERIES_ID');
  if (!planningId && !estimatingId) {
    return ALLOWED_TITLES.indexOf(meetingType) !== -1;
  }
  try {
    const start = new Date(meetingDate);
    const end = new Date(start.getTime() + 6 * 60 * 60 * 1000);
    const events = CalendarApp.getDefaultCalendar().getEvents(start, end);
    const allowedSeries = [];
    if (planningId) allowedSeries.push(planningId);
    if (estimatingId) allowedSeries.push(estimatingId);
    for (let i = 0; i < events.length; i += 1) {
      const event = events[i];
      const recurringId = event.getRecurringEventId ? event.getRecurringEventId() : '';
      if (allowedSeries.indexOf(recurringId) !== -1) return true;
      const title = String(event.getTitle() || '');
      if (title.indexOf(meetingType) !== -1) return true;
    }
    const roster = getProperty('MODUS_ROSTER')
      .split(',')
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean);
    if (!roster.length) return false;
    for (let j = 0; j < events.length; j += 1) {
      const guests = events[j].getGuestList(true).map((guest) =>
        String(guest.getEmail() || '').toLowerCase()
      );
      if (guests.some((email) => roster.indexOf(email) !== -1)) return true;
    }
    return false;
  } catch (error) {
    Logger.log(`Calendar verification skipped: ${safeError(error)}`);
    return ALLOWED_TITLES.indexOf(meetingType) !== -1;
  }
}

function readDocRegistry() {
  const raw = PropertiesService.getScriptProperties().getProperty('GEMINI_DOC_REGISTRY');
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (_) {
    return {};
  }
}

function getDocRecord(docId) {
  return readDocRegistry()[docId] || null;
}

function setDocRecord(docId, record) {
  const registry = readDocRegistry();
  registry[docId] = { ...(registry[docId] || {}), ...record };
  PropertiesService.getScriptProperties().setProperty(
    'GEMINI_DOC_REGISTRY',
    JSON.stringify(registry)
  );
}

function isMessageProcessed(messageId) {
  const key = `gemini-msg:${messageId}`;
  return Boolean(PropertiesService.getScriptProperties().getProperty(key));
}

function markMessageProcessed(messageId, docId, reason) {
  PropertiesService.getScriptProperties().setProperty(
    `gemini-msg:${messageId}`,
    JSON.stringify({ docId, reason, at: new Date().toISOString() })
  );
}

function markMessageSkipped(messageId, reason) {
  markMessageProcessed(messageId, '', reason);
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

function getProperty(name) {
  return String(PropertiesService.getScriptProperties().getProperty(name) || '').trim();
}

function jsonResponse(value, status) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}

function safeError(error) {
  return String((error && error.message) || error || 'unknown error');
}
