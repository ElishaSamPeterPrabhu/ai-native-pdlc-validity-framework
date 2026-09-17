/**
 * Private pilot meeting-intake approval proxy.
 *
 * Cursor posts a review payload to doPost(). The script posts the supplied
 * CardsV2 payload to a Google Chat incoming webhook. OpenLink approval URLs
 * call doGet(), which forwards the approval decision to n8n.
 *
 * Script properties:
 * - CHAT_INCOMING_WEBHOOK_URL
 * - APPROVAL_KEY
 * - TRIMBLE_N8N_CLIENT_ID
 * - TRIMBLE_N8N_CLIENT_SECRET
 * Optional:
 * - TRIMBLE_N8N_TOKEN_URL
 * - TRIMBLE_N8N_SCOPE
 * - WEBHOOK_BASE
 * - N8N_REVIEW_PATH
 */

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    const payload = parseJsonBody(e);
    const reviewId = String(payload.reviewId || '').trim();
    const card = payload.chatResponse || payload.reviewCard;
    if (!reviewId || !card) {
      return jsonResponse({ ok: false, error: 'reviewId and chatResponse are required' }, 400);
    }

    const props = PropertiesService.getScriptProperties();
    const reviewKey = `review:${reviewId}`;
    const existingRaw = props.getProperty(reviewKey);
    if (existingRaw) {
      const existing = JSON.parse(existingRaw);
      if (existing.chatDeliveredAt) {
        return jsonResponse({
          ok: true,
          reviewId,
          duplicate: true,
          chatStatus: existing.chatStatus || 200,
        }, 200);
      }
    }
    const chatWebhook = String(props.getProperty('CHAT_INCOMING_WEBHOOK_URL') || '').trim();
    if (!chatWebhook) {
      return jsonResponse({ ok: false, error: 'CHAT_INCOMING_WEBHOOK_URL is not configured' }, 500);
    }

    const reviewRecord = {
      reviewId,
      items: payload.items || [],
      createdAt: existingRaw ? JSON.parse(existingRaw).createdAt : new Date().toISOString(),
    };
    props.setProperty(reviewKey, JSON.stringify(reviewRecord));

    const response = UrlFetchApp.fetch(chatWebhook, {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      payload: JSON.stringify(card),
    });

    const code = response.getResponseCode();
    if (code < 200 || code >= 300) {
      props.setProperty(reviewKey, JSON.stringify({
        ...reviewRecord,
        deliveryError: `Chat webhook failed (${code})`,
      }));
      return jsonResponse({
        ok: false,
        error: `Chat webhook failed (${code})`,
        body: response.getContentText(),
      }, code);
    }

    props.setProperty(reviewKey, JSON.stringify({
      ...reviewRecord,
      chatDeliveredAt: new Date().toISOString(),
      chatStatus: code,
    }));
    return jsonResponse({ ok: true, reviewId, chatStatus: code }, 200);
  } catch (error) {
    return jsonResponse({ ok: false, error: String(error.message || error) }, 500);
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}

function doGet(e) {
  try {
    const parsed = parseApproval(e || {});
    if (!parsed.reviewId || !parsed.decision) {
      return htmlResponse('Missing reviewId or decision.', 400);
    }

    const review = PropertiesService.getScriptProperties().getProperty(
      `review:${parsed.reviewId}`
    );
    if (!review) {
      return htmlResponse('Review expired or was not found.', 404);
    }

    if (parsed.decision === 'request_changes' && !parsed.comment) {
      return approvalCommentForm(parsed);
    }

    const token = fetchTrimbleToken();
    const props = PropertiesService.getScriptProperties();
    const base = props.getProperty('WEBHOOK_BASE') ||
      'https://flows-webhook.stage.trimble-ai.com/agentic/workflows/v1/webhook';
    const path = props.getProperty('N8N_REVIEW_PATH') || 'modus-meeting-intake-review';
    const approvalKey = String(props.getProperty('APPROVAL_KEY') || '').trim();
    if (!approvalKey) throw new Error('APPROVAL_KEY is not configured');

    const response = UrlFetchApp.fetch(`${base}/${path}`, {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      headers: { Authorization: `Bearer ${token}` },
      payload: JSON.stringify({
        reviewId: parsed.reviewId,
        decision: parsed.decision,
        selectedItemIds: parsed.selectedItemIds,
        comment: parsed.comment,
        approvalToken: approvalKey,
      }),
    });

    const code = response.getResponseCode();
    return htmlResponse(
      code >= 200 && code < 300
        ? `Decision sent to n8n: ${parsed.decision}`
        : `n8n rejected the decision (${code}): ${response.getContentText()}`,
      code
    );
  } catch (error) {
    return htmlResponse(String(error.message || error), 500);
  }
}

function parseJsonBody(e) {
  const body = e && e.postData && e.postData.contents;
  if (!body) throw new Error('JSON request body is required');
  const value = JSON.parse(body);
  if (!value || typeof value !== 'object') throw new Error('JSON body must be an object');
  return value;
}

function parseApproval(e) {
  const params = (e && e.parameter) || {};
  const data = String(params.data || '').trim();
  let decision = String(params.decision || '').trim();
  let reviewId = String(params.reviewId || '').trim();
  let selectedItemIds = String(params.selectedItemIds || '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
  let comment = String(params.comment || '').trim();

  if (data) {
    const pieces = data.split(':');
    decision = pieces.shift() || decision;
    reviewId = pieces.shift() || reviewId;
    selectedItemIds = pieces.join(':').split(',').map((value) => value.trim()).filter(Boolean);
  }

  return { decision, reviewId, selectedItemIds, comment };
}

function fetchTrimbleToken() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get('trimble_n8n_token');
  if (cached) return cached;

  const props = PropertiesService.getScriptProperties();
  const clientId = String(props.getProperty('TRIMBLE_N8N_CLIENT_ID') || '').trim();
  const clientSecret = String(props.getProperty('TRIMBLE_N8N_CLIENT_SECRET') || '').trim();
  const tokenUrl = props.getProperty('TRIMBLE_N8N_TOKEN_URL') ||
    'https://stage.id.trimblecloud.com/oauth/token';
  const scope = props.getProperty('TRIMBLE_N8N_SCOPE') || 'Agentic-N8N-Webhook';
  if (!clientId || !clientSecret) throw new Error('Trimble OAuth credentials are not configured');

  const response = UrlFetchApp.fetch(tokenUrl, {
    method: 'post',
    muteHttpExceptions: true,
    contentType: 'application/x-www-form-urlencoded',
    headers: {
      Authorization: `Basic ${Utilities.base64Encode(`${clientId}:${clientSecret}`)}`,
    },
    payload: `grant_type=client_credentials&scope=${encodeURIComponent(scope)}`,
  });
  const code = response.getResponseCode();
  const body = response.getContentText();
  if (code < 200 || code >= 300) throw new Error(`OAuth failed (${code}): ${body}`);

  const token = JSON.parse(body).access_token;
  if (!token) throw new Error('OAuth response did not contain access_token');
  cache.put('trimble_n8n_token', token, 3000);
  return token;
}

function jsonResponse(value, status) {
  return ContentService
    .createTextOutput(JSON.stringify({ ...value, status }))
    .setMimeType(ContentService.MimeType.JSON);
}

function htmlResponse(message, status) {
  const safe = String(message)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return HtmlService.createHtmlOutput(
    `<html><body><pre>${safe}</pre></body></html>`
  );
}

function approvalCommentForm(parsed) {
  const action = ScriptApp.getService().getUrl();
  const esc = (value) => String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  const selected = parsed.selectedItemIds.join(',');
  return HtmlService.createHtmlOutput(
    '<html><body style="font-family:sans-serif;padding:2rem">' +
      '<h2>Meeting review comment</h2>' +
      `<form method="get" action="${esc(action)}">` +
      `<input type="hidden" name="decision" value="${esc(parsed.decision)}">` +
      `<input type="hidden" name="reviewId" value="${esc(parsed.reviewId)}">` +
      `<input type="hidden" name="selectedItemIds" value="${esc(selected)}">` +
      '<label for="comment">Comment</label><br>' +
      '<textarea id="comment" name="comment" rows="8" cols="60" required></textarea><br><br>' +
      '<button type="submit">Send comment</button>' +
      '</form></body></html>'
  );
}
