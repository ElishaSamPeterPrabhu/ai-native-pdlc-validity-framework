---
name: workflow-setup-other
description: >-
  Generate automation configs for teams not using Cursor Automations: GitHub
  Actions label router and agent jobs, Google Sheets / Apps Script product intake,
  Copilot or generic agent prompts. Keeps the same signal contract so measurement
  still works. Use when the team prefers another platform.
---

# Workflow setup — other platforms

Same stages and signals as `workflow-design.json`; only the runner changes. The
signal contract (`starter-kit/signal-contract.md`) is non-negotiable: the monitor
and the CLI read those exact headers and labels.

## Options

| Platform | What to generate |
| --- | --- |
| GitHub Actions | `starter-kit/workflows/label-router.yml` (filled) plus one job per agent stage that calls the team's agent CLI on `issue_comment` / `labeled` events. Allowlist human logins in `if:`. |
| Copilot coding agent | Issue templates with acceptance criteria + the Dev instruction block from `starter-kit/automations/dev.md` as repository instructions. QA stays a separate Action or human. |
| Sheets / Apps Script intake | A sheet with columns from `starter-kit/automations/product-intake.md`; a time-driven script that turns approved rows into issues. |
| Generic agent / CLI | The instruction blocks from `starter-kit/automations/*.md` as system prompts, triggered by a webhook or cron. |

## Steps

1. Confirm the platform from `process-map.json` (`platform`).
2. Fill templates with repo values; list `{{TODO: …}}` gaps.
3. Write to `<data_dir>/automations/` after approval; propose CI files for
   `workflows_dir` and install only on approval.
4. Hand off to `workflow-measure-handoff`.

## Do not

- Store tokens in files; use repository secrets or the user's CLI auth.
- Let any job merge or bypass required reviews.
