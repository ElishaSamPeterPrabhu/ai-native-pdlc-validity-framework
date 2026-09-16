# Console apply checklist — trimble-oss/modus-wc-2.0 (v2)

Apply in https://cursor.com/t/trimble/automations then **Save**. Do not leave new comment triggers on Anyone.

Automations (existing IDs if still current):

| Agent | ID |
|-------|-----|
| Dev Agent | `69f213ff-4748-4bed-a065-9ba8b97d6bfe` |
| QA Agent | `aac94e20-8523-48e4-a239-26daa40f1675` |
| Issue Scaffolding | `80b1f7a5-3d2e-4ccf-acb5-18acad0eff8c` |
| Fix Agent | `915ae382-a9d0-4d76-9742-3e6121108a3b` (inactive by design) |
| Design-Research | create a new automation; record its ID here after Save |

## Dev Agent triggers (add ALL of these — PR rows are easy to miss)

The console “Comment” trigger has two kinds. **Issue comment ≠ PR comment.**
If you only add Issue comment `/ask`, typing `/ask` on a PR does nothing.

| Type in UI | Match | Repo | By | Command |
|------------|--------|------|-----|---------|
| **Comment on issues** | `/approve` | trimble-oss/modus-wc-2.0 | **Me** | start work |
| **Comment on issues** | `/ask` or `/ask|/clarify` | trimble-oss/modus-wc-2.0 | **Me** | Q&A on issue |
| **Comment on pull requests** | `/ask` or `/ask|/clarify` | trimble-oss/modus-wc-2.0 | **Me** | Q&A on PR |
| **Comment on pull requests** | `/refine` | trimble-oss/modus-wc-2.0 | **Me** | apply PR/QA comments |
| **Label added** | `qa-failed` | trimble-oss/modus-wc-2.0 | n/a | repair latest QA failure on same branch |

Save after adding the two **Comment on pull requests** rows.

## QA Agent triggers

| Type | Match | Repo | By |
|------|--------|------|-----|
| Label added | `qa-full` | trimble-oss/modus-wc-2.0 | n/a |
| Label added | `qa-rerun` | trimble-oss/modus-wc-2.0 | n/a |
| Label added | `qa-skip` | trimble-oss/modus-wc-2.0 | n/a |

There is no PR-opened trigger and no QA comment-command trigger. QA runs only
after a routing label is added.

## Fix Agent triggers

The Fix Agent is **inactive by design**. Dev Agent owns the `qa-failed` repair
path; do not add a Fix Agent trigger.

## Issue Scaffolding triggers

Issue Scaffolding is already webhook-triggered. Human actions:

- Retarget automation `80b1f7a5-3d2e-4ccf-acb5-18acad0eff8c` from
  `test-automation-repo` to `trimble-oss/modus-wc-2.0`.
- Replace its instructions with the Issue Scaffolding v2 block in
  [`AUTOMATION-PROMPTS.md`](AUTOMATION-PROMPTS.md) (now references
  `component-capabilities` after fork PR #53).
- Step-by-step checklist: [`docs/pilot/pr4-scaffolding-apply.md`](../docs/pilot/pr4-scaffolding-apply.md).
- Keep `auto_approve: false` for bot and sheet intake.

## Design-Research triggers

Create a new automation bound only to `trimble-oss/modus-wc-2.0`, paste the
Design-Research block from [`AUTOMATION-PROMPTS.md`](AUTOMATION-PROMPTS.md), and
add both triggers:

- **Label added:** `design-research`
- **Comment on issues:** `/design`, by **Me**

The agent comments capability evidence and clarification headers. It does not
create labels, open PRs, or create Figma files.

## Tools (Dev and QA)

Add **Google Drive MCP**. Do **not** add Figma MCP on Automations (OAuth is
forbidden in cloud; the approved catalog is Drive).

## After Save

Human must click **Save** on each automation after pasting the **thin Dev/QA blocks** from
[`AUTOMATION-PROMPTS.md`](AUTOMATION-PROMPTS.md) (top of "Live instruction paste").
Dev: `69f213ff-4748-4bed-a065-9ba8b97d6bfe`. QA: `aac94e20-8523-48e4-a239-26daa40f1675`.

Product repo must include `.cursor/skills/modus-*`, `.cursor/agents/*`, and `.cursor/hooks.json` on the branch the cloud clone uses (merge to `main` before `/approve` on `main` sees skills).

Smoke the official repository:

1. An unclear issue or Figma URL without a Drive folder produces
   `## NEED CLARIFICATION` on the correct surface and no PR.
2. A Drive folder causes Dev/QA to read `manifest.json` and only the matching
   variant.
3. A blocked scope produces `## NOT FEASIBLE`; the label-router handles
   `needs-human`.
4. `/refine` (new Dev run, not a parked subscribe) patches the same branch and emits `QA-rerun: add` only (not also `Routing: qa-full`); QA runs once after the label-router adds `qa-rerun`. Dev does not `/subscribe` after Open PR. Follow-ups are Me `/refine`/`/ask` GitHub triggers only.
   Dev invokes `graph-impact` + `storybook-smoke` before push on visual edits; hooks nudge after SCSS/Tailwind/component edits.
   QA invokes `graph-impact` + `storybook-smoke` for graph-aware Storybook coverage (max 3 parent targets).
5. `/ask` on a PR receives its answer on the PR, not only on the issue.
6. `design-research` produces a cited capability check before Figma work.
7. Local IDE chats no longer load the full automation rule — only code-guidelines + globbed api-stability unless a skill is invoked.

Fork triggers on `ElishaSamPeterPrabhu/modus-wc-2.0` may stay; do not add new
ones there.
