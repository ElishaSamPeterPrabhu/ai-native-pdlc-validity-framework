# Follow-up PRs for `trimble-oss/modus-wc-2.0`

This is the implementation backlog for the target repository. The current
research repository supplies the contracts and sanitized automation artifacts;
these changes must be made and reviewed in the official Modus repository.

## PR 1 — Generate and publish `custom-elements.md`

**Target paths**

- `src/custom-elements.json`
- a build or docs script under the target repository
- generated `custom-elements.md`
- CI workflow or package script

**Work**

- Render one deterministic component section per declaration.
- Include tag, description, properties/attributes, events, slots, methods, and
  a state/property lookup summary.
- Explicitly report `supports readonly: yes/no` based only on property names in
  the manifest; do not infer it from a sibling.
- Include source manifest path, commit SHA, generated timestamp, and a warning
  when a declaration has no tag.
- Make output stable so a manifest-only change produces a reviewable diff.

**Acceptance criteria**

- `custom-elements.md` is generated from the checked-in manifest in CI.
- A drift check fails when the committed file is stale.
- The file is reachable from the raw GitHub URL used by the Figma plugin and
  chat bots.
- A fixture test covers a property, event, slot, missing tag, and read-only
  lookup.

## PR 2 — Add a `component-capabilities` MCP tool

**Target paths**

- the in-repo component-docs MCP entrypoint (currently inspected as
  `mcp/src/index.ts`; confirm the target tree before editing)
- tool schemas and tests
- component documentation loader

**Proposed tool**

```text
component_name?: string
query?: string
property?: string
state?: string
include_siblings?: boolean
```

The tool returns:

```json
{
  "query": "readonly",
  "matches": [
    {
      "tag": "modus-wc-text-input",
      "supported": true,
      "property": "readOnly",
      "source": "src/custom-elements.json#..."
    }
  ],
  "notFound": ["modus-wc-select"],
  "sourceCommit": "..."
}
```

**Acceptance criteria**

- `_all_components` behavior remains backward compatible.
- Exact property/state matches are distinguished from text search matches.
- Responses cite manifest paths and source commit.
- Missing component/property returns an empty result with
  `notFound`, not a guessed answer.
- Unit tests cover exact match, sibling search, no match, and malformed query.

## PR 3 — Add design-research automation guidance

**Target paths**

- `.cursor/rules/automation.mdc`
- official Cursor automation instruction source
- repository label documentation

**Work**

- Add the `design-research` label and `/design` trigger guidance.
- Require manifest/MCP citations for capability claims.
- Require `## DESIGN RESEARCH`, `## NEED CLARIFICATION`, and
  `## NOT FEASIBLE` headers.
- State that agents emit routing comments and the label-router Action owns
  label mutations.
- Document the reply-surface rule: issue unless an open PR is the active
  surface.

**Acceptance criteria**

- A capability check runs before a design issue is approved.
- An unclear design request produces questions and no PR.
- A non-feasible request stops without an invented workaround.

## PR 4 — Install Issue Scaffolding v2

**Target paths**

- Issue Scaffolding automation instructions
- issue template / generated issue sections
- optional webhook input documentation

**Work**

- Research manifest, MCP, component docs, graph, and duplicate issues before
  writing.
- Add Context, Proposed Change, AC, Design Notes, Technical Notes, Test Plan,
  and Sources.
- Support `issue_url` enrichment for existing one-line issues.
- Stop with `## NEED CLARIFICATION` when target behavior, product scope, or
  design decisions remain unknown.

**Acceptance criteria**

- A one-line issue such as #1459 becomes dual-audience and source-cited.
- An issue with insufficient design scope asks questions rather than
  inventing tokens or states.
- `auto_approve` remains false for bot and sheet intake.

## PR 5 — Maintain component graph evidence

**Target paths**

- `docs/component-graph/component-graph.json`
- graph generation/check workflow
- Dev/QA automation guidance

**Work**

- Generate direct runtime `reverseImpact` entries from the target source.
- Keep graph output deterministic and review changes.
- Require Dev and QA to read direct reverse impact for changed tags.

**Acceptance criteria**

- Missing/empty reverse-impact entries are distinguishable from a failed
  generation.
- QA does not invent dependents when the graph is empty.
- A graph change is included in the PR review surface.

## PR 6 — Publish designer capability distribution

**Target paths**

- plugin repository or agreed `modus-wc-2.0` subdirectory
- package/build configuration
- plugin documentation

**Work**

- Choose ownership and release process for the Figma plugin scaffold.
- Pin the Modus Web Components package if the plugin UI uses Modus elements.
- Configure the raw manifest/markdown URL and allowed hosts.
- Document refresh behavior and stale-cache handling.

**Acceptance criteria**

- Designers can search current capabilities from Figma.
- A missing or stale manifest is visible and never treated as support.
- Plugin output links to the target component docs/Storybook.
- No GitHub token or private API credential is embedded in the plugin.

## Ordering and dependencies

1. PR 1 establishes the readable capability artifact.
2. PR 2 exposes exact capability queries.
3. PRs 3 and 4 install the agent controls that consume both surfaces.
4. PR 5 supplies impact context for the Dev/QA loop.
5. PR 6 distributes the same truth to designers.

Each PR should remain independently reviewable. The n8n workflows in this
repository may be imported in observe mode before all six PRs land, but issue
creation must remain human-confirmed until the source and duplicate checks are
available.
