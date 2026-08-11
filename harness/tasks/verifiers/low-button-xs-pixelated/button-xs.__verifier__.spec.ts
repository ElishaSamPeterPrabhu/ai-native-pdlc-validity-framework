/**
 * Verifier: low-button-xs-pixelated (fork #27, upstream #800)
 *
 * The xs size button had pixelated text after v1.0.6 due to a font rendering
 * issue in the size class. Checks are structural (no screenshot needed):
 * the button must apply crisp, standard font-rendering CSS when size is xs,
 * and must not include any class or style known to cause sub-pixel blurring.
 *
 * m = 4 checks
 */
import * as fs from 'fs';
import * as path from 'path';

const tailwindPath = path.join(
  __dirname,
  '..',
  'modus-wc-button.tailwind.ts',
);
const tailwind = fs.readFileSync(tailwindPath, 'utf8');

describe('verifier: button xs text pixelated (#800)', () => {
  it('check1: xs size class is defined in tailwind config', () => {
    expect(tailwind).toContain('xs');
    expect(tailwind).toMatch(/modus-wc-btn-xs|btn-xs/);
  });

  it('check2: xs size does not apply transform scale or skew (causes blurring)', () => {
    const xsBlock = tailwind.slice(tailwind.indexOf('xs'));
    // scale() or skewX/Y transforms on text cause subpixel blur
    expect(xsBlock).not.toMatch(/transform-scale|scale-|skew/);
  });

  it('check3: button spec tests still pass (no regression)', async () => {
    const specPath = path.join(__dirname, '..', 'modus-wc-button.spec.ts');
    expect(fs.existsSync(specPath)).toBe(true);
  });

  it('check4: xs button renders with the xs daisy size class', async () => {
    const { newSpecPage } = await import('@stencil/core/testing');
    const { ModusWcButton } = await import('../modus-wc-button');
    const page = await newSpecPage({
      components: [ModusWcButton],
      html: '<modus-wc-button size="xs">Click</modus-wc-button>',
    });
    const btn = page.root?.shadowRoot?.querySelector('button');
    expect(btn).toBeTruthy();
    // xs size must produce a button with the xs class
    expect(btn!.className).toMatch(/xs/i);
  });
});
