# Runbook: retarget the automations onto the modus fork

The five automations (Issue Scaffolding, Dev Agent, QA Agent, Fix Agent, Project
Onboarding) are Cursor cloud objects edited at cursor.com/automations — they cannot be
changed from this repo. This runbook is the exact change list; ~15 minutes of console
work. Items marked [file] are already handled in this workspace/fork.

## 0. Preconditions

- [x] [file] Fork synced with upstream on branch `experiment-base` (includes `mcp/`).
- [x] [file] Experiment labels created on `ElishaSamPeterPrabhu/modus-wc-2.0`:
      `task:low|medium|high`, `spec:raw|refined`, `approved`, `needs-review`,
      `qa-failed`, `needs-human`, `experiment-run`.
- [ ] Cursor GitHub app has access to `ElishaSamPeterPrabhu/modus-wc-2.0`
      (Dashboard → Settings → Integrations → GitHub → repository access).

## 1. Per-automation changes (cursor.com/automations)

### Issue Scaffolding
- Trigger: keep webhook; no repo scoping needed (payload carries the issue URL).
- Instructions: append —
  "If the issue has an `experiment-run` label, do NOT reword the acceptance criteria;
   validate structure only. If the issue carries a `spec:raw` label, do not enrich it —
   leave the description as-is and only add the `approved` label if auto_approve=true."
  (This keeps the σ_spec manipulation clean: scaffolding must not silently refine raw specs
   in arms where spec_refinement is OFF.)
- Tools: fix the failing `github` MCP tool (red "Failing" chip): Disconnect → re-add →
  re-authenticate. Verify with a manual run against a test issue.
- Model: confirm Composer 2.5.

### Dev Agent
- Repo/branch: add `ElishaSamPeterPrabhu/modus-wc-2.0`, base branch `experiment-base`
  (NOT main — every experiment run branches from the pinned base).
- Trigger: add `Matching /^\/approve$/ by Me on issue in ElishaSamPeterPrabhu/modus-wc-2.0`.
- Instructions: append —
  "Base all work on the `experiment-base` branch. Name the feature branch
   `exp/<issue-number>-<slug>`. Commit in small, frequent increments (after each logical
   change), not one big commit. Open the PR against `experiment-base`."
- Tools: fix the failing `github` MCP tool (same procedure as above).
- Model: confirm Composer 2.5.

### QA Agent
- Trigger: add `PR opened in ElishaSamPeterPrabhu/modus-wc-2.0 by Anyone`.
- Instructions: append —
  "For this repository, functional QA means: `npm run tailwind:build && npm run embed:css
   && npm run embed:component-css` then `npm test` plus `npm run lint`. Do not run
   Storybook builds. Post `## QA PASSED` or `## QA FAILED` with the failing output, and
   add the `qa-failed` label on failure."
- Model: confirm Composer 2.5.

### Fix Agent
- Trigger: add `Label Added on PRs in ElishaSamPeterPrabhu/modus-wc-2.0 Matching "qa-failed"`.
- Instructions: verify the 3-iteration memory cap text is intact; the iteration-cap
  ablation arm (cap=1) is done by editing this number for that arm only, then restoring.
- Model: confirm Composer 2.5.

### Project Onboarding
- Not needed for the campaign (fork already has `.cursor/rules/code-guidelines.mdc`).
  Leave inactive for modus, or run once manually if Dev Agent's architecture.mdc
  prerequisite should be pre-satisfied (recommended: run once, merge its PR into
  `experiment-base`, so the Dev Agent never spends run time on it).

## 2. Factor-toggle mechanics (per experiment arm)

| Factor | ON | OFF |
| --- | --- | --- |
| spec_refinement | seed issue via scaffolding webhook with auto_approve | seed issue directly with `spec:raw` body, add `approved` label yourself |
| agentic_qa | QA Agent automation Active | toggle automation Inactive |
| fix_loop / cap | Fix Agent Active, cap=3 (or 1) | toggle Inactive |
| ci_gate | branch protection on `experiment-base` requires the test workflow | remove required check |
| mcp_context | `.cursor/mcp.json` in experiment-base points at `mcp/` server | commit removing it (arm-specific base branch `experiment-base-nomcp`) |
| rules_context | `.cursor/rules/` present | arm-specific base branch with rules removed |
| checkpointing | Dev Agent instruction includes frequent-commit clause | arm variant instruction without it |
| review_bot | Bugbot enabled on the fork | disabled |

Repo-side OFF toggles are implemented as tiny commits on arm-specific base branches
(`experiment-base-nomcp`, `experiment-base-norules`), so any run's provenance is a
branch name in the PR — no mutable global state.

## 3. Confound checklist (before the pilot)

- [ ] Disable `copilot-pr-review.yml` on experiment branches (baseline contamination —
      see research/pipeline-scan.md §4). Simplest: add `branches: [main]` restriction.
- [ ] Confirm no other automations (from test-automation-repo days) have triggers that
      also match this fork.
- [ ] Set the cloud-agent spend limit before the campaign (Dashboard → usage limits).
- [ ] Record in `data/campaign-meta.json`: model=Composer 2.5, automation versions,
      date, spend limit. (The driver template writes this automatically.)
