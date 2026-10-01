const test = require('node:test');
const assert = require('node:assert/strict');
const rules = require('./standards-rules.json');
const engine = require('./capability-engine.js');

const manifest = {
  modules: [
    {
      declarations: [
        {
          tagName: 'modus-wc-select',
          description: 'Select control',
          attributes: [
            { name: 'disabled', type: 'boolean' },
            { name: 'required', type: 'boolean' },
            { name: 'size', type: "'sm' | 'md' | 'lg'" },
          ],
        },
        {
          tagName: 'modus-wc-text-input',
          attributes: [
            { name: 'readOnly', type: 'boolean' },
            { name: 'size', type: "'sm' | 'md' | 'lg'" },
          ],
        },
        {
          tagName: 'modus-wc-button',
          attributes: [{ name: 'size', type: 'DaisySize' }],
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
      docs: { readme: 'src/components/modus-wc-select/readme.md' },
    },
  },
};

test('finds an existing Modus property', () => {
  const result = engine.buildResult({
    query: 'modus-wc-text-input / readonly',
    manifest,
    context,
    rules,
  });
  assert.equal(result.modusCapability.status, 'existing');
  assert.equal(result.modusCapability.property, 'readOnly');
  assert.equal(result.standards.status, 'compatible');
});

test('flags select readonly as a standards constraint', () => {
  const result = engine.buildResult({
    query: 'modus-wc-select / readonly',
    manifest,
    context,
    rules,
  });
  assert.equal(result.modusCapability.status, 'new-api-candidate');
  assert.equal(result.standards.status, 'unsupported');
  assert.equal(result.standards.alternatives.length, 3);
  assert.match(result.handoff.markdown, /MDN|WHATWG|Sources/);
});

test('shows sibling precedent without treating xs as select support', () => {
  const result = engine.buildResult({
    query: 'modus-wc-select / xs',
    manifest,
    context,
    rules,
  });
  assert.equal(result.modusCapability.status, 'new-api-candidate');
  assert.deepEqual(
    result.modusCapability.context.precedent.sharedTypes.DaisySize,
    ['xs', 'sm', 'md', 'lg'],
  );
});

test('reports source stale instead of making a capability claim', () => {
  const result = engine.buildResult({
    query: 'modus-wc-select / readonly',
    manifest: null,
    context: null,
    rules,
  });
  assert.equal(result.modusCapability.status, 'source-stale');
  assert.equal(result.standards.status, 'unknown');
});

test('parses an ambiguous layer hint without inventing a tag', () => {
  const parsed = engine.parseQuery('Form control / readonly');
  assert.equal(parsed.tag, null);
  assert.equal(parsed.requested, 'Form control / readonly');
});
