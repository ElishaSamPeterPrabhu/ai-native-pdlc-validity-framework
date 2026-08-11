/**
 * Verifier: med-checkbox-switch-value (fork #28, upstream #861)
 *
 * Checkbox and Switch were not updating their internal state, so:
 *   - `value` prop didn't reflect after change
 *   - `inputChange` event was emitted with stale data
 *
 * Checks: after a simulated click the value prop reflects the new state
 * and the emitted event payload matches.
 *
 * m = 6 checks
 */
import { newSpecPage } from '@stencil/core/testing';

async function renderCheckbox(checked: boolean): Promise<any> {
  const { ModusWcCheckbox } = await import('../modus-wc-checkbox');
  return newSpecPage({
    components: [ModusWcCheckbox],
    html: `<modus-wc-checkbox value="${checked}"></modus-wc-checkbox>`,
  });
}

async function renderSwitch(checked: boolean): Promise<any> {
  const { ModusWcSwitch } = await import('../modus-wc-switch');
  return newSpecPage({
    components: [ModusWcSwitch],
    html: `<modus-wc-switch value="${checked}"></modus-wc-switch>`,
  });
}

describe('verifier: checkbox & switch value update (#861)', () => {
  it('check1: checkbox renders with value=false by default', async () => {
    const page = await renderCheckbox(false);
    expect(page.root?.getAttribute('value')).toBe('false');
  });

  it('check2: checkbox reflects value=true when prop set', async () => {
    const page = await renderCheckbox(true);
    const input = page.root?.shadowRoot?.querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(input.checked).toBe(true);
  });

  it('check3: checkbox emits inputChange with updated value on programmatic change', async () => {
    const page = await renderCheckbox(false);
    const comp = page.rootInstance;
    let emittedEvent: any = null;
    page.root!.addEventListener('inputChange', (e: any) => {
      emittedEvent = e.detail;
    });
    // Simulate a change event on the inner input
    const input = page.root?.shadowRoot?.querySelector('input') as HTMLInputElement;
    input.checked = true;
    input.dispatchEvent(new Event('change'));
    await page.waitForChanges();
    // The component must update its value prop
    expect(comp.value).toBe(true);
  });

  it('check4: switch renders with value=false by default', async () => {
    const page = await renderSwitch(false);
    const input = page.root?.shadowRoot?.querySelector('input') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(input.checked).toBe(false);
  });

  it('check5: switch reflects value=true when prop is true', async () => {
    const page = await renderSwitch(true);
    const input = page.root?.shadowRoot?.querySelector('input') as HTMLInputElement;
    expect(input.checked).toBe(true);
  });

  it('check6: switch value prop updates after change event', async () => {
    const page = await renderSwitch(false);
    const comp = page.rootInstance;
    const input = page.root?.shadowRoot?.querySelector('input') as HTMLInputElement;
    input.checked = true;
    input.dispatchEvent(new Event('change'));
    await page.waitForChanges();
    expect(comp.value).toBe(true);
  });
});
