#!/usr/bin/env node
/**
 * Local Modus designer copilot — grounded structured suggestions.
 * POST /suggest { query, selection?, facts? }
 */

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { buildFacts, generateSuggestions } = require('./copilot-suggest.js');

const PORT = Number(process.env.COPILOT_PORT || 3777);
const root = __dirname;

function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
}

let manifest;
let context;
let rules;

function loadPack() {
  manifest = readJson('custom-elements.json');
  context = readJson('designer-context.json');
  rules = readJson('standards-rules.json');
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'));
      } catch (error) {
        reject(error);
      }
    });
    request.on('error', reject);
  });
}

function sendJson(response, status, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  });
  response.end(body);
}

async function maybeEnhanceWithLlm(facts, base) {
  if (process.env.COPILOT_USE_LLM !== '1' || !process.env.OPENAI_API_KEY) {
    return base;
  }

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: process.env.COPILOT_MODEL || 'gpt-4o-mini',
        response_format: { type: 'json_object' },
        messages: [
          {
            role: 'system',
            content: [
              'You refine Modus designer suggestions.',
              'Use ONLY facts in the user JSON.',
              'Return {"suggestions":[...]} matching schema kinds and citations.',
              'Never invent component APIs.',
            ].join(' '),
          },
          {
            role: 'user',
            content: JSON.stringify({ facts, baseSuggestions: base.suggestions }),
          },
        ],
      }),
    });
    if (!response.ok) return base;
    const payload = await response.json();
    const content = payload.choices?.[0]?.message?.content;
    if (!content) return base;
    const parsed = JSON.parse(content);
    if (!Array.isArray(parsed.suggestions)) return base;
    return generateSuggestions(
      { ...facts, suggestions: parsed.suggestions },
      facts.selectedNode,
    );
  } catch {
    return base;
  }
}

loadPack();

const server = http.createServer(async (request, response) => {
  if (request.method === 'OPTIONS') {
    sendJson(response, 204, {});
    return;
  }

  if (request.method === 'GET' && request.url === '/health') {
    sendJson(response, 200, {
      ok: true,
      sourceCommit: context?.sourceCommit || null,
      tagCount: Object.keys(context?.components || {}).length,
    });
    return;
  }

  if (request.method !== 'POST' || request.url !== '/suggest') {
    sendJson(response, 404, { error: 'not_found' });
    return;
  }

  try {
    const body = await readBody(request);
    const query = String(body.query || '').trim();
    const selection = body.selection || null;
    const facts = body.facts || buildFacts({
      query,
      selectedNode: selection,
      manifest,
      context,
      rules,
    });

    let result = generateSuggestions(facts, selection);
    result = await maybeEnhanceWithLlm(facts, result);

    sendJson(response, 200, {
      ...facts,
      suggestions: result.suggestions,
      annotation: result.annotation,
    });
  } catch (error) {
    sendJson(response, 400, { error: String(error.message || error) });
  }
});

server.listen(PORT, () => {
  console.log(`Modus copilot listening on http://localhost:${PORT}`);
  console.log(`Health: http://localhost:${PORT}/health`);
});
