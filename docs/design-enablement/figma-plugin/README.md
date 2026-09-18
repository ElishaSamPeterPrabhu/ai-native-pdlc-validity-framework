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
6. bundle `capability-engine.js`, `standards-rules.json`, and the result
   schema;
7. test network access, source-staleness, standards warnings, and handoff
   copying before publishing.

No GitHub or Figma credentials belong in this directory.

The plugin consumes two kinds of evidence:

- `designer-context.json` from the official Modus repository for component
  properties, state matrix, token hints, precedent, impact, and source links;
- the curated standards registry for HTML/ARIA constraints such as
  `select` not supporting `readonly`.

The plugin is read-only and suggestive. AI reasoning remains in the Cursor
`design-capability-check` skill; the plugin does not create issues or mutate
Figma nodes.
