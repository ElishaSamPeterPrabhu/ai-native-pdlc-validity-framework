/**
 * Grounded suggestion generator for Modus designer copilot.
 * Uses capability-engine facts only — no invented APIs.
 */
(function attachCopilotSuggest(root, factory) {
  function loadEngine() {
    if (typeof module === 'object' && module.exports) {
      return require('./capability-engine.js');
    }
    return root.ModusCapabilityEngine;
  }

  const api = factory(loadEngine());
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.ModusCopilotSuggest = api;
  }
})(typeof globalThis === 'object' ? globalThis : typeof window === 'object' ? window : this, function createCopilotSuggest(engine) {
  const STATUS_LABEL = {
    existing: 'existing',
    'new-api-candidate': 'new-api',
    ambiguous: 'ambiguous',
    'source-stale': 'stale',
    compatible: 'ok',
    warning: 'standards',
    unsupported: 'blocked',
    unknown: 'unknown',
  };

  function citation(path) {
    return path;
  }

  function pushSuggestion(list, item) {
    if (!item.text || !item.citations?.length) return;
    list.push({
      kind: item.kind,
      text: item.text,
      rationale: item.rationale,
      citations: item.citations,
      grounding: item.grounding,
    });
  }

  function generateSuggestions(facts, selection) {
    const suggestions = [];
    const capability = facts.modusCapability || {};
    const standards = facts.standards || {};
    const context = capability.context || {};

    if (capability.status === 'source-stale') {
      pushSuggestion(suggestions, {
        kind: 'gap',
        text: 'Refresh the Modus context pack before claiming support',
        rationale: 'Manifest or designer-context snapshot is unavailable.',
        citations: [citation('designer-context.json#provenance')],
        grounding: 'source-stale',
      });
      return finalize(facts, selection, suggestions);
    }

    if (capability.status === 'existing' && capability.property) {
      pushSuggestion(suggestions, {
        kind: 'existing',
        text: `Keep ${capability.tag} / ${capability.property} — listed in manifest`,
        rationale: 'Exact property match in custom-elements.json.',
        citations: [
          citation(`custom-elements.json#${capability.tag}/${capability.property}`),
        ],
        grounding: 'existing',
      });
    }

    if (capability.status === 'new-api-candidate' && capability.tag) {
      pushSuggestion(suggestions, {
        kind: 'new-api-candidate',
        text: `${capability.requested || capability.state || 'Requested state'} is not listed on ${capability.tag}`,
        rationale: 'No matching property in manifest; treat as a new API candidate.',
        citations: [citation(`custom-elements.json#${capability.tag}`)],
        grounding: 'new-api-candidate',
      });
    }

    if (standards.status === 'unsupported' || standards.status === 'warning') {
      for (const rule of standards.rules || []) {
        pushSuggestion(suggestions, {
          kind: 'standards-warning',
          text: rule.title,
          rationale: rule.message,
          citations: [
            citation(`standards-rules.json#${rule.id}`),
            ...(rule.sources || []).map((source) => source.url).slice(0, 1),
          ].filter(Boolean),
          grounding: standards.status,
        });
        for (const alternative of rule.alternatives || []) {
          pushSuggestion(suggestions, {
            kind: 'standards-warning',
            text: alternative.title,
            rationale: alternative.description,
            citations: [
              citation(`standards-rules.json#${rule.id}`),
              citation(`standards-rules.json#${rule.id}/alternatives/${alternative.id}`),
            ],
            grounding: standards.status,
          });
        }
      }
    }

    for (const state of context.stateMatrix || []) {
      const name = typeof state === 'string' ? state : state.name;
      if (!name) continue;
      const normalizedSelection = String(selection?.name || '').toLowerCase();
      if (normalizedSelection.includes(name.toLowerCase())) continue;
      pushSuggestion(suggestions, {
        kind: 'state-matrix',
        text: `Add Storybook state: ${name}`,
        rationale: 'State exists in component stories; verify Figma variant coverage.',
        citations: [
          citation(
            `designer-context.json#${capability.tag}/stateMatrix/${name}`,
          ),
          ...(typeof state === 'object' && state.source ? [state.source] : []),
        ],
        grounding: 'observed',
      });
    }

    for (const token of (context.tokenHints || []).slice(0, 3)) {
      pushSuggestion(suggestions, {
        kind: 'token-hint',
        text: `Use token ${token}`,
        rationale: 'Token referenced in component styles/context bundle.',
        citations: [citation(`designer-context.json#${capability.tag}/tokenHints/${token}`)],
        grounding: 'observed',
      });
    }

    if (context.precedent?.sharedTypes) {
      for (const [typeName, values] of Object.entries(context.precedent.sharedTypes)) {
        pushSuggestion(suggestions, {
          kind: 'precedent',
          text: `Align ${typeName} with sibling values: ${values.join(', ')}`,
          rationale: 'Shared type precedent from sibling components in context pack.',
          citations: [
            citation(`designer-context.json#${capability.tag}/precedent/sharedTypes/${typeName}`),
          ],
          grounding: 'observed',
        });
      }
    }

    if (context.impact?.usedBy?.length) {
      pushSuggestion(suggestions, {
        kind: 'impact',
        text: `Check downstream: ${context.impact.usedBy.join(', ')}`,
        rationale: 'Reverse impact from context pack.',
        citations: [
          citation(`designer-context.json#${capability.tag}/impact`),
        ],
        grounding: 'observed',
      });
    }

    if (!suggestions.length && capability.status === 'ambiguous') {
      pushSuggestion(suggestions, {
        kind: 'gap',
        text: 'Disambiguate the Modus tag before adding variants',
        rationale: 'Query maps to multiple components or none.',
        citations: [citation('capability-engine.js#parseQuery')],
        grounding: 'ambiguous',
      });
    }

    return finalize(facts, selection, suggestions);
  }

  const KIND_PRIORITY = {
    'standards-warning': 0,
    'new-api-candidate': 1,
    existing: 2,
    impact: 3,
    precedent: 4,
    gap: 5,
    'state-matrix': 6,
    'token-hint': 7,
  };

  function displayName(tag) {
    if (!tag) return 'this component';
    return tag.replace(/^modus-wc-/, '').replace(/-/g, ' ');
  }

  function pickShowcaseSuggestions(suggestions) {
    const sorted = [...suggestions].sort(
      (left, right) => (KIND_PRIORITY[left.kind] ?? 99) - (KIND_PRIORITY[right.kind] ?? 99),
    );
    const picked = [];
    const seenKind = new Set();

    for (const item of sorted) {
      if (seenKind.has(item.kind)) continue;
      picked.push(item);
      seenKind.add(item.kind);
      if (picked.length >= 3) break;
    }

    return picked;
  }

  function designerLine(item, facts) {
    const component = displayName(facts.modusCapability?.tag);

    switch (item.kind) {
      case 'standards-warning':
        if (item.rationale) {
          return `${item.text}. ${item.rationale.split('.')[0]}.`;
        }
        return item.text;
      case 'state-matrix': {
        const stateName = item.text.replace('Add Storybook state: ', '');
        return `Add a "${stateName}" variant — it is documented in Storybook for ${component}.`;
      }
      case 'token-hint': {
        const token = item.text.replace('Use token ', '');
        return `Use ${token} for spacing and color — same tokens as in code.`;
      }
      case 'existing':
        return item.text
          .replace('Keep ', '')
          .replace('— listed in manifest', '— already supported in the component API.');
      case 'new-api-candidate':
        return `${item.text.replace(' is not listed on ', " isn't listed on ")} — check with the Modus team before adding it to Figma.`;
      case 'impact':
        return item.text.replace('Check downstream:', 'Changing this component may affect');
      case 'precedent':
        return item.text
          .replace('Align ', 'Match ')
          .replace('with sibling values:', 'to values used on sibling components:');
      case 'gap':
        return item.text;
      default:
        return item.text;
    }
  }

  function finalize(facts, selection, suggestions) {
    const tag = facts.modusCapability?.tag;
    const label = displayName(tag);
    const title = tag
      ? `Suggestion for ${label.charAt(0).toUpperCase()}${label.slice(1)}`
      : 'Modus suggestion';
    const showcase = pickShowcaseSuggestions(suggestions);
    const lines = [title, ''];

    if (selection?.name) {
      lines.push(`For layer: ${selection.name}`);
      lines.push('');
    }

    if (!showcase.length) {
      lines.push(`${label} is in the Modus library. Match your Figma variants to Storybook states.`);
    } else {
      for (const item of showcase) {
        lines.push(`• ${designerLine(item, facts)}`);
      }
    }

    const parsed = engine.parseQuery(facts.query || '');
    if (tag && !parsed.requested) {
      lines.push('');
      lines.push(`Try "${tag} / readonly" to check HTML and accessibility constraints.`);
    }

    return {
      suggestions,
      annotation: lines.join('\n'),
    };
  }

  function buildFacts({ query, selectedNode, manifest, context, rules }) {
    const facts = engine.buildResult({
      query,
      selectedNode,
      manifest,
      context,
      rules,
    });
    if (facts.modusCapability && !facts.modusCapability.requested) {
      const parsed = engine.parseQuery(query);
      facts.modusCapability.requested = parsed.requested || null;
    }
    return facts;
  }

  function buildAutocompleteSuggestions(query, index, rules, engineApi) {
    const api = engineApi || engine;
    const normalized = api.normalize(query);
    const suggestions = [];
    const tags = index?.tags || [];

    for (const tag of tags) {
      if (!normalized || api.normalize(tag).includes(normalized)) {
        suggestions.push({
          name: `${tag} — component`,
          data: tag,
        });
      }
    }

    const tagMatch = String(query || '').match(/(modus-wc-[a-z0-9-]+)\s*[/|]?\s*(.*)$/i);
    if (tagMatch) {
      const tag = tagMatch[1].toLowerCase();
      const fragment = api.normalize(tagMatch[2] || '');
      const properties = index?.propertiesByTag?.[tag] || [];
      for (const property of properties) {
        if (!fragment || api.normalize(property).includes(fragment)) {
          suggestions.push({
            name: `${tag} / ${property} — existing`,
            data: `${tag} / ${property}`,
          });
        }
      }
      const states = index?.statesByTag?.[tag] || [];
      for (const state of states) {
        if (!fragment || api.normalize(state).includes(fragment)) {
          suggestions.push({
            name: `${tag} / ${state} — story state`,
            data: `${tag} / ${state}`,
          });
        }
      }
      if (fragment && (fragment.includes('readonly') || fragment.includes('readOnly'))) {
        const parsed = api.parseQuery(`${tag} / ${tagMatch[2]}`);
        const matchedRules = api.matchingRules(rules, parsed.tag, parsed.requested);
        if (matchedRules.length) {
          suggestions.push({
            name: `${tag} / ${tagMatch[2]} — standards warning`,
            data: `${tag} / ${tagMatch[2]}`,
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

  return {
    STATUS_LABEL,
    generateSuggestions,
    buildFacts,
    buildAutocompleteSuggestions,
  };
});
