# Console apply checklist — trimble-oss/modus-wc-2.0

Apply in https://cursor.com/t/trimble/automations then **Save**. Do not leave new comment triggers on Anyone.

Automations (existing IDs if still current):

| Agent | ID |
|-------|-----|
| Dev Agent | `69f213ff-4748-4bed-a065-9ba8b97d6bfe` |
| QA Agent | `aac94e20-8523-48e4-a239-26daa40f1675` |
| Fix Agent | `915ae382-a9d0-4d76-9742-3e6121108a3b` |

## Dev Agent triggers

| Type | Match | Repo | By |
|------|--------|------|-----|
| Issue comment | `/approve` | trimble-oss/modus-wc-2.0 | **Me** |
| Issue comment | `/ask` (and `/clarify` if the UI allows one regex: `/ask|/clarify`) | trimble-oss/modus-wc-2.0 | **Me** |
| PR comment | `/ask` (same regex) | trimble-oss/modus-wc-2.0 | **Me** |
| PR comment | `/refine` | trimble-oss/modus-wc-2.0 | **Me** |

Paste instruction blocks from [`AUTOMATION-PROMPTS.md`](AUTOMATION-PROMPTS.md): official-repo gate, `/ask` on **issue and PR**, `/refine`. Agents must reply on the **PR** when the human wrote on the PR.

## QA Agent triggers

| Type | Match | Repo | By |
|------|--------|------|-----|
| PR opened | — | trimble-oss/modus-wc-2.0 | **Anyone** (exception: bot-opened PRs) |
| Label added | `qa-full` | trimble-oss/modus-wc-2.0 | n/a |
| Label added | `qa-rerun` | trimble-oss/modus-wc-2.0 | n/a |

No QA comment-command trigger.

## Fix Agent triggers

| Type | Match | Repo | By |
|------|--------|------|-----|
| Label added | `qa-failed` | trimble-oss/modus-wc-2.0 | n/a |

Paste not-feasible + `qa-rerun` remove-then-add from [`AUTOMATION-PROMPTS.md`](AUTOMATION-PROMPTS.md).

## After Save

Human must click **Save** on each automation. Then smoke on official issues/PRs:

1. Unclear issue → expect `## NEED CLARIFICATION` + `needs-human` (no PR).
2. Blocked scope → expect `## NOT FEASIBLE` + `needs-human`.
3. Your `/refine` on a PR → Dev routes or patches; QA re-runs only after `qa-rerun` add.
4. Your questions on a PR → comment `/ask` on that PR; expect the reply **on the PR**, not the issue.

Fork triggers on ElishaSamPeterPrabhu/modus-wc-2.0 may stay; do not add new ones there.
