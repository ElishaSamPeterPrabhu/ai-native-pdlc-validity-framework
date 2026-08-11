# Setup questionnaire (online automations)

Cursor Automations live in the console. We usually **cannot** list their
definitions via API. Fill this (or copy into `user-intake.json`) so AI can
diagnose your setup without console access.

## 1. Repo

- Owner / name / default branch:
- GitHub URL:

## 2. Automations (from cursor.com/…/automations)

For each automation (Dev / QA / Fix / Scaffold / other):

| Field | Your answer |
| --- | --- |
| Name | |
| Role (`dev` / `qa` / `fix` / `scaffold` / `review`) | |
| Trigger | |
| Repo scope | |
| Tools / MCP enabled | |
| Stop rule (when may it say done?) | |
| Repair cap (fix only) | |
| Enabled? | |
| 5–15 line instructions excerpt (stop/done/QA handoff) | |
| Console URL | |

## 3. Declared local setup (yes/no)

- `.cursor/rules` or equivalent:
- MCP config / server:
- Completion hooks:
- CI required checks:
- Review bot:
- Label handoff (`approved`, `qa-failed`, …):
- Human review on every PR:

## 4. Goals

What should diagnosis optimize for? (examples: review depth, fewer false completions, faster merge with safe review)
