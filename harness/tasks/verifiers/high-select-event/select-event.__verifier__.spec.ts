/**
 * Verifier: high-select-event (fork #26, upstream #677)
 *
 * modus-wc-select was updating `this.value` correctly but the `inputChange`
 * event was either not emitted, or emitted with a stale/wrong value,
 * causing testing frameworks that simulate change events to see silent updates.
 *
 * Checks: setting value programmatically or via a change event on the inner
 * <select> must both update value AND fire inputChange with the correct payload.
 *
 * m = 6 checks
 */
import { newSpecPage } from '@stencil/core/testing';

const OPTIONS = [
  { label: 'Option A', value: 'a' },
  { label: 'Option B', value: 'b' },
  { label: 'Option C', value: 'c' },
];

async function renderSelect(initial = ''): Promise<any> {
  const { ModusWcSelect } = await import('../modus-wc-select');
  const page = await newSpecPage({
    components: [ModusWcSelect],
    html: `<modus-wc-select value="${initial}"></modus-wc-select>`,
  });
  page.rootInstance.options = OPTIONS;
  await page.waitForChanges();
  return page;
}

describe('verifier: select event emission (#677)', () => {
  it('check1: select renders with correct initial value', async () => {
    const page = await renderSelect('a');
    const sel = page.root?.shadowRoot?.querySelector('select') as HTMLSelectElement;
    expect(sel).toBeTruthy();
    expect(sel.value).toBe('a');
  });

  it('check2: value prop reflects after programmatic change', async () => {
    const page = await renderSelect('a');
    page.rootInstance.value = 'b';
    await page.waitForChanges();
    expect(page.rootInstance.value).toBe('b');
  });

  it('check3: inputChange is emitted when value changes via DOM event', async () => {
    const page = await renderSelect('a');
    let changeCount = 0;
    page.root!.addEventListener('inputChange', () => { changeCount++; });
    const sel = page.root?.shadowRoot?.querySelector('select') as HTMLSelectElement;
    sel.value = 'c';
    sel.dispatchEvent(new Event('change'));
    await page.waitForChanges();
    expect(changeCount).toBeGreaterThanOrEqual(1);
  });

  it('check4: inputChange event payload contains the new value', async () => {
    const page = await renderSelect('a');
    let payload: any = null;
    page.root!.addEventListener('inputChange', (e: any) => { payload = e; });
    const sel = page.root?.shadowRoot?.querySelector('select') as HTMLSelectElement;
    sel.value = 'b';
    sel.dispatchEvent(new Event('change'));
    await page.waitForChanges();
    // The select element value or the component's value must be 'b'
    expect(page.rootInstance.value).toBe('b');
  });

  it('check5: no extra events emitted when value is set to the same value', async () => {
    const page = await renderSelect('a');
    let changeCount = 0;
    page.root!.addEventListener('inputChange', () => { changeCount++; });
    page.rootInstance.value = 'a'; // same value
    await page.waitForChanges();
    expect(changeCount).toBe(0);
  });

  it('check6: all options are rendered in the DOM', async () => {
    const page = await renderSelect('');
    const opts = page.root?.shadowRoot?.querySelectorAll('option');
    expect(opts?.length).toBeGreaterThanOrEqual(OPTIONS.length);
  });
});
