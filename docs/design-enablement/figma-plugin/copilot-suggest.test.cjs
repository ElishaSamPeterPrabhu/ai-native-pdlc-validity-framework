const test = require('node:test');
const assert = require('node:assert/strict');
const rules = require('./standards-rules.json');
const {
  buildFacts,
  generateSuggestions,
  buildAutocompleteSuggestions,
} = require('./copilot-suggest.js');

const manifest = {
  modules: [
    {
      declarations: [
        {
          tagName: 'modus-wc-select',
          attributes: [
            { name: 'disabled', type: 'boolean' },
            { name: 'required', type: 'boolean' },
          ],
        },
        {
          tagName: 'modus-wc-text-input',
          attributes: [{ name: 'readOnly', type: 'boolean' }],
        },
      ],
    },
  ],
};

const context = {
  sourceCommit: 'abc123',
  generatedAt: '2026-09-18T00:00:00.000Z',
  components: {
    'modus-wc-select': {
      stateMatrix: [{ name: 'Default' }, { name: 'WithErrorFeedback' }],
      tokenHints: ['--modus-wc-input-height-md'],
      precedent: { sharedTypes: { DaisySize: ['xs', 'sm', 'md', 'lg'] } },
      impact: { usedBy: ['modus-wc-date'], sourceKind: 'readme' },
    },
  },
};

const index = {
  tags: ['modus-wc-select', 'modus-wc-text-input'],
  propertiesByTag: {
    'modus-wc-select': ['disabled', 'required'],
    'modus-wc-text-input': ['readOnly'],
  },
  statesByTag: {
    'modus-wc-select': ['Default', 'WithErrorFeedback'],
  },
};

test('generateSuggestions cites standards for select readonly', () => {
  const facts = buildFacts({
    query: 'modus-wc-select / readonly',
    manifest,
    context,
    rules,
  });
  const result = generateSuggestions(facts, { name: 'modus-wc-select / readonly' });
  assert.ok(result.suggestions.length >= 2);
  assert.ok(result.suggestions.every((item) => item.citations.length >= 1));
  assert.ok(result.suggestions.some((item) => item.kind === 'standards-warning'));
  assert.match(result.annotation, /Suggestion for select/i);
  assert.doesNotMatch(result.annotation, /\[state-matrix\]/);
});

test('generateSuggestions includes state matrix and tokens with citations', () => {
  const facts = buildFacts({
    query: 'modus-wc-select / disabled',
    manifest,
    context,
    rules,
  });
  const result = generateSuggestions(facts, { name: 'modus-wc-select' });
  assert.ok(result.suggestions.some((item) => item.kind === 'state-matrix'));
  assert.ok(result.suggestions.some((item) => item.kind === 'token-hint'));
});

test('autocomplete includes standards warning entry', () => {
  const suggestions = buildAutocompleteSuggestions(
    'modus-wc-select / readonly',
    index,
    rules,
  );
  assert.ok(suggestions.some((item) => item.name.includes('standards')));
});

test('reports gap when pack is stale', () => {
  const facts = buildFacts({
    query: 'modus-wc-select / readonly',
    manifest: null,
    context: null,
    rules,
  });
  const result = generateSuggestions(facts, null);
  assert.equal(result.suggestions[0].kind, 'gap');
  assert.equal(result.suggestions[0].grounding, 'source-stale');
});
