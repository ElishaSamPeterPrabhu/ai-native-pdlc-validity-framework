# Console apply checklist — trimble-oss/modus-wc-2.0

Apply in https://cursor.com/t/trimble/automations then **Save**. Do not leave new comment triggers on Anyone.

Two live automations: **Dev** + **QA**. Fix is unused (Inactive).

| Agent | ID | Role |
|-------|-----|------|
| Dev Agent | `69f213ff-4748-4bed-a065-9ba8b97d6bfe` | `/approve`, `/ask`, `/refine`, `qa-failed` |
| QA Agent | `aac94e20-8523-48e4-a239-26daa40f1675` | `qa-full`, `qa-rerun`, `qa-skip` |
| Fix Agent | `915ae382-a9d0-4d76-9742-3e6121108a3b` | **Inactive** — do not use |

Paste from [`AUTOMATION-PROMPTS.md`](AUTOMATION-PROMPTS.md). **Replace** Dev’s instruction box (drop architecture.mdc bootstrap). Follow `.cursor/rules/automation.mdc`. API stability when present: no new exported types. Labels: comment signals; Action attaches. Never GitHub MCP.

## Comment kinds (not interchangeable)

- **Comment on issues** — issue conversation (not a PR)
- **Comment on pull requests** — top-level PR conversation
- **PR review comment** — inline note on a file in the diff

`/approve` is the **only** path that extracts the GitHub issue (title, AC, notes). `/refine` and `/ask` skip that.

## Same window vs new run

Automations UI **cannot** resume a previous agent window. Each matching trigger starts a **new** cloud run.

After `/approve`, Dev **subscribes** to that PR’s comments/reviews (the agent does this; no Subscribe toggle). Later `/refine` / `/ask` on that PR should wake **the same Dev conversation**. You can also follow up in Agents Window or `@cursor` on a PR that agent opened.

`/refine` and `/ask` **comment triggers** are **fallback** (new run, dispatch skips issue-setup).

**Double-fire:** if subscribe is alive **and** the `/refine` trigger is on, one comment can start two Dev runs. Smoke once. If two runs: **turn off** PR `/refine` and `/ask` comment triggers; keep subscribe + `/approve` + `qa-failed`. Do not subscribe to labels.

Do not rely on IDE Cursor Memories for cloud runs. Automation Memories are a short note file, not the old chat.

## Dev Agent triggers

| Type in UI | Match | Repo | By | When |
|------------|--------|------|-----|------|
| **Comment on issues** | `/approve` | trimble-oss/modus-wc-2.0 | **Me** | start work (extract issue) |
| **Comment on issues** | `/ask` or `/ask\|/clarify` | trimble-oss/modus-wc-2.0 | **Me** | Q&A on issue |
| **Comment on pull requests** | `/ask` or `/ask\|/clarify` | trimble-oss/modus-wc-2.0 | **Me** | fallback Q&A on PR |
| **Comment on pull requests** | `/refine` | trimble-oss/modus-wc-2.0 | **Me** | fallback refine |
| **PR review comment** | `/refine` | trimble-oss/modus-wc-2.0 | **Me** | fallback inline refine |
| **Label added** | `qa-failed` | trimble-oss/modus-wc-2.0 | n/a | repair QA (moved off Fix) |

Do not add review-comment `/refine` to QA. Do not fire `/refine` for Anyone.

## QA Agent triggers

Label added only. Do **not** trigger on PR opened.

| Type | Match | Repo | By |
|------|--------|------|-----|
| Label added | `qa-full` | trimble-oss/modus-wc-2.0 | n/a |
| Label added | `qa-rerun` | trimble-oss/modus-wc-2.0 | n/a |
| Label added | `qa-skip` | trimble-oss/modus-wc-2.0 | n/a |

## Fix Agent

Toggle **Inactive**. `qa-failed` lives on Dev. Do not delete yet.

## After Save

1. Unclear `/approve` → `## NEED CLARIFICATION` + `needs-human` (no PR).
2. Blocked `/approve` → `## NOT FEASIBLE` + `needs-human`.
3. After a PR: prefer commenting `/refine` on the **same** subscribed Dev run (one Agents Window). If two Dev runs appear, drop the comment `/refine`/`/ask` triggers.
4. `/ask` on a PR → reply **on the PR**.
5. QA re-runs only after `QA-rerun: add` **pulses** `qa-rerun` (Action deletes then adds, even if the label is already on the PR). Conversation comment or PR review body both count.

Fork triggers on ElishaSamPeterPrabhu/modus-wc-2.0 may stay; do not add new ones there.

Do not test by commenting `/refine` asking the agent to add files.
