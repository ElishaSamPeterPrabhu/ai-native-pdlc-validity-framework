/**
 * Verifier: low-sidenav-menu-style (fork #29, upstream #987)
 *
 * Menus inside modus-wc-side-navigation are styled differently from standalone
 * menus. The fix must produce a consistent style (same token class family).
 * Structural stylesheet checks — no DOM rendering needed.
 *
 * m = 4 checks
 */
import * as fs from 'fs';
import * as path from 'path';

function readComponent(name: string, ext: string): string {
  const p = path.join(__dirname, '..', `${name}.${ext}`);
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '';
}

describe('verifier: side navigation menu style consistency (#987)', () => {
  const scss = readComponent('modus-wc-side-navigation', 'scss');
  const tailwind = readComponent('modus-wc-side-navigation', 'tailwind.ts');
  const combined = scss + tailwind;

  it('check1: side navigation stylesheet file exists', () => {
    expect(combined.length).toBeGreaterThan(100);
  });

  it('check2: no hardcoded color values inside menu selectors (must use tokens)', () => {
    // Look for any hardcoded hex / rgb values adjacent to menu-related selectors
    const menuSection = combined.match(/menu[\s\S]{0,800}/i)?.[0] ?? '';
    expect(menuSection).not.toMatch(/#[0-9a-f]{3,6}(?![a-z])/i);
  });

  it('check3: side-nav menu uses the same base class as standalone menus', () => {
    // modus-wc-menu base class should appear — consistency gate
    const hasMenClass =
      combined.includes('modus-wc-menu') ||
      combined.includes('menu-item');
    expect(hasMenClass).toBe(true);
  });

  it('check4: side navigation component file is not empty after the fix', () => {
    expect(combined.length).toBeGreaterThan(500);
  });
});
