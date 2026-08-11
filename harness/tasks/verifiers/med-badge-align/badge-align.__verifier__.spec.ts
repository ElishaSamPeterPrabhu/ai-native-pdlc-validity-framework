/**
 * Verifier: med-badge-align (upstream #1268).
 *
 * Behavior-level assertions via Stencil spec rendering: badge exposes the
 * sizing scale, applies size classes, and stays consistent across sizes.
 * (Pixel-exact alignment is validated by the a11y/visual gates; this verifier
 * covers the API-observable acceptance criteria.)
 */
import { newSpecPage } from '@stencil/core/testing';
import { ModusWcBadge } from '../modus-wc-badge';

async function renderBadge(attrs: string): Promise<any> {
  const page = await newSpecPage({
    components: [ModusWcBadge],
    html: `<modus-wc-badge ${attrs}>3</modus-wc-badge>`,
  });
  return page;
}

describe('verifier: badge alignment and sizing scale (#1268)', () => {
  it('check1: badge renders sm/md/lg size variants with distinct classes', async () => {
    const classes: string[] = [];
    for (const size of ['sm', 'md', 'lg']) {
      const page = await renderBadge(`size="${size}"`);
      const el = page.root?.querySelector('.modus-wc-badge');
      expect(el).toBeTruthy();
      classes.push(el!.className);
    }
    expect(new Set(classes).size).toBe(3);
  });

  it('check2: counter badge variant renders', async () => {
    const page = await renderBadge('variant="counter"');
    const el = page.root?.querySelector('.modus-wc-badge');
    expect(el).toBeTruthy();
    expect(el!.className).toMatch(/counter/i);
  });

  it('check3: counter badge respects the size prop', async () => {
    const sm = await renderBadge('variant="counter" size="sm"');
    const lg = await renderBadge('variant="counter" size="lg"');
    expect(
      sm.root!.querySelector('.modus-wc-badge')!.className,
    ).not.toEqual(lg.root!.querySelector('.modus-wc-badge')!.className);
  });

  it('check4: badge content is vertically centered via flex alignment classes', async () => {
    const page = await renderBadge('size="md"');
    const el = page.root?.querySelector('.modus-wc-badge');
    // Accept any class-based vertical centering (items-center / align variants).
    expect(el!.className).toMatch(/items-center|align-middle|self-center/);
  });

  it('check5: default badge keeps text content intact (no clipping wrapper)', async () => {
    const page = await renderBadge('');
    expect(page.root?.textContent).toContain('3');
  });
});
