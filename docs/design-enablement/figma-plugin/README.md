# Modus Capability Check Figma plugin scaffold

This directory is a source scaffold, not a published plugin. `manifest.json`
and `code.js` are ready for a plugin build; `ui.html` expects the build to
produce a local `modus-bundle.js`.

The eventual plugin repository must:

1. pin `@trimble-oss/moduswebcomponents`;
2. import `modus-wc-styles.css` once;
3. call `defineCustomElements()` during startup;
4. bundle the Modus custom elements into `modus-bundle.js`;
5. set the official raw GitHub URLs in `ui.html`;
6. test network access and source-staleness behavior before publishing.

No GitHub or Figma credentials belong in this directory.
