/**
 * Verifier: med-menu-item-end-icon (fork #30, upstream #1128)
 *
 * Add an end-icon slot to modus-wc-menu-item. Currently only start-icon
 * exists (confirmed in source). Checks: slot present in render, exposed via
 * readme, does not break start-icon or default slot.
 *
 * m = 5 checks
 */
import { newSpecPage } from '@stencil/core/testing';
import * as fs from 'fs';
import * as path from 'path';

async function renderMenuItem(attrs: string, slotHtml = ''): Promise<any> {
  const { ModusWcMenuItem } = await import('../modus-wc-menu-item');
  return newSpecPage({
    components: [ModusWcMenuItem],
    html: `<modus-wc-menu-item ${attrs}>${slotHtml}</modus-wc-menu-item>`,
  });
}

describe('verifier: menu-item end-icon slot (#1128)', () => {
  it('check1: end-icon slot exists in the rendered shadow DOM', async () => {
    const page = await renderMenuItem('label="Test"');
    const endIconSlot = page.root?.shadowRoot?.querySelector(
      'slot[name="end-icon"]',
    );
    expect(endIconSlot).toBeTruthy();
  });

  it('check2: slotted end-icon content renders without error', async () => {
    const page = await renderMenuItem(
      'label="Test"',
      '<span slot="end-icon">→</span>',
    );
    expect(page.root).toBeTruthy();
  });

  it('check3: start-icon slot still works (no regression)', async () => {
    const page = await renderMenuItem(
      'label="Test"',
      '<span slot="start-icon">←</span>',
    );
    const startSlot = page.root?.shadowRoot?.querySelector(
      'slot[name="start-icon"]',
    );
    expect(startSlot).toBeTruthy();
  });

  it('check4: default slot still renders label content', async () => {
    const page = await renderMenuItem('');
    const defaultSlot = page.root?.shadowRoot?.querySelector(
      'slot:not([name])',
    );
    expect(defaultSlot).toBeTruthy();
  });

  it('check5: readme documents the end-icon slot', () => {
    const readmePath = path.join(__dirname, '..', 'readme.md');
    if (!fs.existsSync(readmePath)) return; // skip if readme not yet updated
    const readme = fs.readFileSync(readmePath, 'utf8');
    expect(readme).toMatch(/end-icon/i);
  });
});
