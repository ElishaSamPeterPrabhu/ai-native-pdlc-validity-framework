/**
 * Verifier: low-alert-blend (rebroken fix of upstream #1227 / commit 87b26a41b).
 *
 * The defect and fix are stylesheet-only, so the checks assert on the alert
 * stylesheet source (implementation-agnostic at the level that matters: the
 * rendered background must be the pale token at the design opacity, not a
 * gray-blended precomputed color). Any implementation that produces the correct
 * colors passes; the pre-fix gray-light blends fail.
 */
import * as fs from 'fs';
import * as path from 'path';

const scss = fs.readFileSync(
  path.join(__dirname, '..', 'modus-wc-alert.scss'),
  'utf8',
);

function variantBlock(variant: string): string {
  const start = scss.indexOf(`modus-wc-alert-${variant}`);
  if (start === -1) return '';
  return scss.slice(start, start + 700);
}

describe('verifier: alert background blend (#1227)', () => {
  it('check1: error variant does not blend with gray-light', () => {
    const block = variantBlock('error');
    expect(block).not.toContain('--modus-wc-color-gray-light');
    expect(block).not.toContain('#fce0e2');
  });

  it('check2: success variant does not blend with gray-light', () => {
    const block = variantBlock('success');
    expect(block).not.toContain('--modus-wc-color-gray-light');
    expect(block).not.toContain('#e6efd9');
  });

  it('check3: warning variant does not blend with gray-light', () => {
    const block = variantBlock('warning');
    expect(block).not.toContain('--modus-wc-color-gray-light');
    expect(block).not.toContain('#f9f0e8');
  });

  it('check4: variants keep a pale-token background at design opacity', () => {
    // Accept either the rgb()-with-alpha fallback or a color-mix with
    // transparent — both express "pale token at opacity" without a gray blend.
    for (const variant of ['error', 'success', 'warning']) {
      const block = variantBlock(variant);
      const ok =
        /rgb\([^)]+\/\s*0?\.\d+\)/.test(block) ||
        /color-mix\([^)]*transparent/.test(block);
      expect(ok).toBe(true);
    }
  });
});
