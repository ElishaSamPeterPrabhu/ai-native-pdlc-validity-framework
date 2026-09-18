(function attachCapabilityEngine(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.ModusCapabilityEngine = api;
  }
})(typeof globalThis === 'object' ? globalThis : window, function createCapabilityEngine() {
  function normalize(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[-_\s]/g, '');
  }

  function tagFor(declaration) {
    return declaration?.tagName || declaration?.tag || '';
  }

  function propertiesFor(declaration) {
    return []
      .concat(declaration?.members || [])
      .concat(declaration?.properties || [])
      .concat(declaration?.attributes || [])
      .filter((property) => property && property.name && property.kind !== 'method');
  }

  function sourceFor(moduleIndex, declarationIndex) {
    return `src/custom-elements.json#/modules/${moduleIndex}/declarations/${declarationIndex}`;
  }

  function declarationsFor(manifest) {
    return (manifest?.modules || []).flatMap((module, moduleIndex) =>
      (module.declarations || [])
        .filter((declaration) => tagFor(declaration))
        .map((declaration, declarationIndex) => ({
          ...declaration,
          tag: tagFor(declaration),
          source: sourceFor(moduleIndex, declarationIndex),
        })),
    );
  }

  function parseQuery(query) {
    const value = String(query || '').trim();
    const tagMatch = value.match(/(modus-wc-[a-z0-9-]+)(?:\s*[/|]\s*|\s+)?(.*)$/i);
    if (!tagMatch) {
      return { raw: value, tag: null, requested: value };
    }
    return {
      raw: value,
      tag: tagMatch[1].toLowerCase(),
      requested: String(tagMatch[2] || '').trim(),
    };
  }

  function propertyMatch(declaration, requested) {
    const normalizedRequested = normalize(requested);
    if (!normalizedRequested) return null;
    return propertiesFor(declaration).find(
      (property) => normalize(property.name) === normalizedRequested,
    ) || null;
  }

  function declarationMatches(declaration, query) {
    const candidate = normalize(query);
    if (!candidate) return false;
    return [
      tagFor(declaration),
      declaration.name,
      declaration.description,
      ...propertiesFor(declaration).flatMap((property) => [
        property.name,
        property.description,
      ]),
    ].some((value) => normalize(value).includes(candidate));
  }

  function contextComponent(context, tag) {
    if (!context || !tag) return null;
    if (Array.isArray(context.components)) {
      return context.components.find((component) => component.tag === tag) || null;
    }
    return context.components?.[tag] || null;
  }

  function contextItems(component, key) {
    const value = component?.[key];
    return Array.isArray(value) ? value : [];
  }

  function ruleMatches(rule, tag, requested) {
    const tagMatch = !rule.modusTags?.length || rule.modusTags.includes(tag);
    const nativeMatch = !rule.nativeElements?.length || rule.nativeElements.includes(
      tag.replace(/^modus-wc-/, ''),
    );
    const propertyMatchValue = !rule.properties?.length || rule.properties.some(
      (property) => normalize(property) === normalize(requested),
    );
    return tagMatch && nativeMatch && propertyMatchValue;
  }

  function matchingRules(rules, tag, requested) {
    return (rules?.rules || []).filter((rule) => ruleMatches(rule, tag, requested));
  }

  function capabilityMatches(query, manifest) {
    const parsed = parseQuery(query);
    const declarations = declarationsFor(manifest);
    const target = parsed.tag
      ? declarations.filter((declaration) => tagFor(declaration) === parsed.tag)
      : declarations.filter((declaration) => declarationMatches(declaration, parsed.raw));

    return target.flatMap((declaration) => {
      const property = propertyMatch(declaration, parsed.requested);
      if (parsed.tag && parsed.requested && property) {
        return [{
          tag: tagFor(declaration),
          supported: true,
          property: property.name,
          description: property.description || '',
          source: declaration.source,
        }];
      }
      if (parsed.tag && parsed.requested) return [];
      return [{
        tag: tagFor(declaration),
        supported: true,
        property: null,
        description: declaration.description || '',
        source: declaration.source,
      }];
    });
  }

  function buildResult({ query, selectedNode, manifest, context, rules }) {
    const parsed = parseQuery(query);
    const declarations = declarationsFor(manifest);
    const declaration = parsed.tag
      ? declarations.find((candidate) => tagFor(candidate) === parsed.tag)
      : null;
    const matches = capabilityMatches(query, manifest);
    const component = contextComponent(context, parsed.tag);
    const exactProperty = propertyMatch(declaration, parsed.requested);
    const isTargetedRequest = Boolean(parsed.tag && parsed.requested);
    let capabilityStatus = 'source-stale';

    if (manifest) {
      if (isTargetedRequest && !declaration) {
        capabilityStatus = 'ambiguous';
      } else if (isTargetedRequest && exactProperty) {
        capabilityStatus = 'existing';
      } else if (isTargetedRequest && declaration) {
        capabilityStatus = 'new-api-candidate';
      } else if (matches.length === 1) {
        capabilityStatus = 'existing';
      } else if (matches.length > 1) {
        capabilityStatus = 'ambiguous';
      } else {
        capabilityStatus = 'new-api-candidate';
      }
    }

    const rulesForRequest = manifest
      ? matchingRules(rules, parsed.tag, parsed.requested)
      : [];
    const standardsStatus = rulesForRequest.length
      ? rulesForRequest.some((rule) => rule.status === 'unsupported')
        ? 'unsupported'
        : 'warning'
      : manifest && isTargetedRequest
        ? 'compatible'
        : 'unknown';
    const contextSources = [
      ...(component?.sources || []),
      ...(component?.docs ? Object.values(component.docs) : []),
    ].filter(Boolean);
    const sources = [
      ...matches.map((match) => match.source),
      ...contextSources,
      ...rulesForRequest.flatMap((rule) => rule.sources || []).map((source) => source.url),
    ].filter((source, index, all) => all.indexOf(source) === index);

    const result = {
      query: String(query || ''),
      selectedNode: selectedNode || null,
      modusCapability: {
        status: capabilityStatus,
        tag: parsed.tag,
        property: exactProperty?.name || null,
        state: parsed.requested || null,
        matches,
        context: component
          ? {
              stateMatrix: contextItems(component, 'stateMatrix'),
              tokenHints: contextItems(component, 'tokenHints'),
              precedent: component.precedent || null,
              impact: component.impact || null,
              sourceCommit: context.sourceCommit || null,
            }
          : null,
      },
      standards: {
        status: standardsStatus,
        rules: rulesForRequest,
        alternatives: rulesForRequest.flatMap((rule) => rule.alternatives || []),
      },
      sources,
      sourceCommit: context?.sourceCommit || null,
      generatedAt: context?.generatedAt || null,
    };

    result.handoff = {
      markdown: formatHandoff(result),
      json: JSON.parse(JSON.stringify(result)),
    };
    return result;
  }

  function formatHandoff(result) {
    const capability = result.modusCapability;
    const standards = result.standards;
    const lines = [
      '## DESIGN CAPABILITY HANDOFF',
      '',
      `- Request: ${result.query || '(empty)'}`,
      `- Modus capability: ${capability.status}`,
      `- Standards result: ${standards.status}`,
    ];
    if (capability.tag) lines.push(`- Component: \`${capability.tag}\``);
    if (capability.property) lines.push(`- Property: \`${capability.property}\``);
    if (capability.context?.sourceCommit) {
      lines.push(`- Source commit: \`${capability.context.sourceCommit}\``);
    }
    if (standards.rules.length) {
      lines.push('', '### Constraints');
      standards.rules.forEach((rule) => lines.push(`- ${rule.title}: ${rule.message}`));
    }
    if (standards.alternatives.length) {
      lines.push('', '### Suggested options');
      standards.alternatives.forEach((alternative) => {
        lines.push(`- ${alternative.title}: ${alternative.description}`);
      });
    }
    if (capability.context?.impact) {
      lines.push('', '### Impact');
      lines.push(JSON.stringify(capability.context.impact));
    }
    if (result.sources.length) {
      lines.push('', '### Sources');
      result.sources.forEach((source) => lines.push(`- ${source}`));
    }
    return lines.join('\n');
  }

  return {
    normalize,
    declarationsFor,
    parseQuery,
    capabilityMatches,
    matchingRules,
    buildResult,
    formatHandoff,
  };
});
