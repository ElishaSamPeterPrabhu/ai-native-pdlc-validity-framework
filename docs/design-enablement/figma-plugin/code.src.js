const engine = typeof ModusCapabilityEngine !== 'undefined'
  ? ModusCapabilityEngine
  : null;

function selectedNodeSummary() {
  const node = figma.currentPage.selection[0];
  return node
    ? { id: node.id, name: node.name, type: node.type }
    : null;
}

function filterSuggestions(items, query) {
  const needle = String(query || '').toLowerCase();
  if (!needle) return items.slice(0, 20);
  return items.filter((item) => item.name.toLowerCase().includes(needle)).slice(0, 20);
}

function buildLocalSuggestions(query) {
  if (!engine || !__MODUS_INDEX__) return [];
  const tags = __MODUS_INDEX__.tags || [];
  const normalizedQuery = engine.normalize(query);
  const suggestions = [];

  for (const tag of tags) {
    if (!normalizedQuery || engine.normalize(tag).includes(normalizedQuery)) {
      suggestions.push({
        name: `${tag} — component`,
        data: tag,
      });
    }
  }

  const parsed = engine.parseQuery(query);
  if (parsed.tag) {
    const properties = __MODUS_INDEX__.propertiesByTag?.[parsed.tag] || [];
    for (const property of properties) {
      if (!parsed.requested || engine.normalize(property).includes(engine.normalize(parsed.requested))) {
        suggestions.push({
          name: `${parsed.tag} / ${property} — existing`,
          data: `${parsed.tag} / ${property}`,
        });
      }
    }
    const states = __MODUS_INDEX__.statesByTag?.[parsed.tag] || [];
    for (const state of states) {
      if (!parsed.requested || engine.normalize(state).includes(engine.normalize(parsed.requested))) {
        suggestions.push({
          name: `${parsed.tag} / ${state} — story state`,
          data: `${parsed.tag} / ${state}`,
        });
      }
    }
    if (parsed.requested && __MODUS_RULES__) {
      const rules = engine.matchingRules(__MODUS_RULES__, parsed.tag, parsed.requested);
      if (rules.length) {
        suggestions.unshift({
          name: `${parsed.tag} / ${parsed.requested} — standards ${rules[0].status}`,
          data: `${parsed.tag} / ${parsed.requested}`,
        });
      }
    }
  }

  const seen = new Set();
  return suggestions.filter((item) => {
    const key = item.data || item.name;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 20);
}

function runLocalCopilot(query, selection) {
  const facts = ModusCopilotSuggest.buildFacts({
    query,
    selectedNode: selection,
    manifest: __MODUS_MANIFEST__,
    context: __MODUS_CONTEXT__,
    rules: __MODUS_RULES__,
  });
  const result = ModusCopilotSuggest.generateSuggestions(facts, selection);
  return {
    ...facts,
    suggestions: result.suggestions,
    annotation: result.annotation,
  };
}

function buildCursorPrompt(query, selection, payload) {
  const lines = [
    'Run design-capability-check for this Modus design question.',
    '',
    `Query: ${query}`,
  ];
  if (selection?.name) {
    lines.push(`Figma selection: ${selection.name}`);
  }
  if (payload.modusCapability?.status) {
    lines.push(`Initial Modus status: ${payload.modusCapability.status}`);
  }
  if (payload.standards?.status && payload.standards.status !== 'unknown') {
    lines.push(`Initial standards status: ${payload.standards.status}`);
  }
  lines.push('');
  lines.push('Help me decide what to design, what already exists in Modus, standards constraints, and suggested next steps.');
  if (payload.annotation) {
    lines.push('');
    lines.push('Quick context from Figma:');
    lines.push(payload.annotation);
  }
  return lines.join('\n');
}

function openCursorHandoff(query, selection, payload) {
  const prompt = buildCursorPrompt(query, selection, payload);
  figma.showUI(__html__, { width: 420, height: 300, title: 'Continue in Cursor' });
  figma.ui.postMessage({ type: 'init', prompt });
}

async function runWithParameters(parameters) {
  const query = String(parameters.query || '').trim();
  if (!query) {
    figma.notify('Enter a Modus component, property, or state.');
    figma.closePlugin();
    return;
  }

  const selection = selectedNodeSummary();
  const payload = runLocalCopilot(query, selection);
  openCursorHandoff(query, selection, payload);
  figma.notify('Copy the prompt into Cursor for interactive help.');
}

function start() {
  figma.on('run', ({ parameters }) => {
    if (!parameters || !parameters.query) {
      figma.notify('Tab into Modus Designer Copilot and enter a query.');
      figma.closePlugin();
      return;
    }
    runWithParameters(parameters);
  });

  figma.ui.onmessage = (message) => {
    if (message?.type === 'copied') {
      figma.notify('Paste in Cursor chat to continue with the agent.');
    }
  };

  figma.parameters.on('input', ({ key, query, result }) => {
    if (key !== 'query') return;
    const suggestions = buildLocalSuggestions(query);
    if (!suggestions.length) {
      result.setSuggestions(filterSuggestions([{ name: query, data: query }], query));
      return;
    }
    result.setSuggestions(filterSuggestions(suggestions, query));
  });
}
