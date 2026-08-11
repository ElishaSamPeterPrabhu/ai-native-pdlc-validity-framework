/**
 * Verifier: low-card-hover (upstream #1244).
 *
 * Cards must not show hover effects in classic and connect themes; modern theme
 * behavior unchanged. Stylesheet-level assertions: hover rules must be absent or
 * scoped away from classic/connect themes.
 */
import * as fs from 'fs';
import * as path from 'path';

const scssPath = path.join(__dirname, '..', 'modus-wc-card.scss');
const scss = fs.readFileSync(scssPath, 'utf8');

/** Return the ~300 chars around each :hover rule for scope inspection. */
function hoverContexts(src: string): string[] {
  const contexts: string[] = [];
  let idx = src.indexOf(':hover');
  while (idx !== -1) {
    contexts.push(src.slice(Math.max(0, idx - 300), idx + 100));
    idx = src.indexOf(':hover', idx + 1);
  }
  return contexts;
}

describe('verifier: card hover removal for classic/connect (#1244)', () => {
  const contexts = hoverContexts(scss);

  it('check1: no unscoped card hover rule remains', () => {
    // Every remaining :hover must be visibly scoped to a specific theme
    // selector (data-theme) — a bare &:hover on the card fails.
    for (const ctx of contexts) {
      expect(/data-theme/.test(ctx)).toBe(true);
    }
  });

  it('check2: no hover rule scoped to a classic theme', () => {
    for (const ctx of contexts) {
      expect(/data-theme=['"]?modus-classic/.test(ctx)).toBe(false);
    }
  });

  it('check3: no hover rule scoped to a connect theme', () => {
    for (const ctx of contexts) {
      expect(/data-theme=['"]?connect/.test(ctx)).toBe(false);
    }
  });

  it('check4: card stylesheet still styles the card (sanity: not deleted)', () => {
    expect(scss).toContain('modus-wc-card');
    expect(scss.length).toBeGreaterThan(500);
  });
});
