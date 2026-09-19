const fs = require('node:fs');
const path = require('node:path');

const root = __dirname;
const read = (name) => fs.readFileSync(path.join(root, name), 'utf8');
const safeScriptValue = (value) => value.replace(/</g, '\\u003c');

let html = read('ui.html');
html = html.replace(
  '<script src="modus-bundle.js"></script>',
  () => `<script>${read('modus-bundle.js')}</script>`,
);
html = html.replace(
  '<script src="capability-engine.js"></script>',
  () => `<script>${read('capability-engine.js')}</script>`,
);

const embeddedSources = `<script>
window.__MODUS_MANIFEST__ = ${safeScriptValue(read('custom-elements.json'))};
window.__MODUS_CONTEXT__ = ${safeScriptValue(read('designer-context.json'))};
window.__MODUS_RULES__ = ${safeScriptValue(read('standards-rules.json'))};
</script>`;

html = html.replace('<head>', `<head>\n${embeddedSources}`);
fs.writeFileSync(path.join(root, 'ui.generated.html'), html);
console.log('Wrote ui.generated.html');
