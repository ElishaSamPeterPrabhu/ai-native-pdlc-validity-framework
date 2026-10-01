const fs = require('node:fs');
const path = require('node:path');

const root = __dirname;

function propertiesFor(declaration) {
  return []
    .concat(declaration?.members || [])
    .concat(declaration?.properties || [])
    .concat(declaration?.attributes || [])
    .filter((property) => property && property.name && property.kind !== 'method');
}

function tagFor(declaration) {
  return declaration?.tagName || declaration?.tag || '';
}

function buildIndex(manifest, context) {
  const tags = [];
  const propertiesByTag = {};
  const statesByTag = {};

  for (const module of manifest?.modules || []) {
    for (const declaration of module.declarations || []) {
      const tag = tagFor(declaration);
      if (!tag) continue;
      tags.push(tag);
      propertiesByTag[tag] = propertiesFor(declaration).map((property) => property.name);
    }
  }

  for (const [tag, component] of Object.entries(context?.components || {})) {
    statesByTag[tag] = (component.stateMatrix || []).map((state) => state.name);
  }

  return {
    schemaVersion: '1.0',
    sourceCommit: context?.sourceCommit || null,
    generatedAt: context?.generatedAt || null,
    tags: [...new Set(tags)].sort(),
    propertiesByTag,
    statesByTag,
  };
}

const manifest = JSON.parse(fs.readFileSync(path.join(root, 'custom-elements.json'), 'utf8'));
const context = JSON.parse(fs.readFileSync(path.join(root, 'designer-context.json'), 'utf8'));
const index = buildIndex(manifest, context);

fs.writeFileSync(path.join(root, 'component-index.json'), `${JSON.stringify(index, null, 2)}\n`);
console.log(`Wrote component-index.json (${index.tags.length} tags)`);
