# PR 4 — Apply Issue Scaffolding v2 (console)

Fork PRs **#52** (custom-elements.md) and **#53** (MCP `component-capabilities` tests)
are merged. Complete PR 4 in the Cursor Automations console — no repo token required.

## 1. Issue Scaffolding automation

| Field | Value |
| --- | --- |
| Automation ID | `80b1f7a5-3d2e-4ccf-acb5-18acad0eff8c` |
| Repo | `trimble-oss/modus-wc-2.0` |
| Trigger | Webhook (unchanged) |

**Instructions:** Replace the full instruction text with the **Issue Scaffolding v2**
block in [`harness/AUTOMATION-PROMPTS.md`](../../harness/AUTOMATION-PROMPTS.md)
(search for `Issue Scaffolding v2 — research-first`).

**Must keep:**

- `auto_approve: false` for sheet and bot intake
- Webhook `issue_url` enrichment path for one-line seeds
- `## NEED CLARIFICATION` / `## NOT FEASIBLE` stop rules

**Tools:** Re-auth the GitHub MCP tool if it shows Failing. Enable Modus
component-docs MCP (`component-capabilities`, `get_modus_component_data`).

Click **Save**.

## 2. Design-Research automation (PR 3 companion)

Create or update a separate automation on `trimble-oss/modus-wc-2.0`:

- Paste the **Design-Research agent** block from the same `AUTOMATION-PROMPTS.md`
- Triggers: label `design-research`, issue comment `/design` by **Me**
- Record the new automation ID in [`harness/CONSOLE-TRIGGERS.md`](../../harness/CONSOLE-TRIGGERS.md)

## 3. Local IDE skills (research repo)

For Cursor IDE issue drafting (not cloud scaffolding):

| Skill | Use |
| --- | --- |
| `design-capability-check` | Research before drafting |
| `design-to-issue` | Cited issue body in chat |

Sheet approve → Issue Scaffolding automation remains the production path.

## 4. Smoke tests

After Save:

1. **One-line seed** — paste a short issue; scaffolding should add Context, AC,
   Design notes, Technical notes, Test plan, Sources with manifest/MCP cites.
2. **Ambiguous scope** — scaffolding comments `## NEED CLARIFICATION`; no PR.
3. **Sheet approve row** — approve a reviewed row; webhook fires scaffolding;
   writeback shows issue URL or clarification (pilot path unchanged).

## 5. Not in scope (deferred)

- Phase 3 real sprint E2E
- Upstream PR from fork (pilot commits #45, graph transfer must be split out)
- Blazor CI on personal fork (skipped by design)
