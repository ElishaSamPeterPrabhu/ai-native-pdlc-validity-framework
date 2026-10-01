---
name: workflow-setup-cursor
description: >-
  Generate paste-ready Cursor Automation configs (Dev, QA, Fix, /ask, /refine,
  product intake) from workflow-design.json using starter-kit templates. Use when
  the team runs agents with Cursor Automations.
---

# Workflow setup — Cursor Automations

## Inputs

`workflow-design.json`, `repo-profile.json`, templates in `starter-kit/automations/`.

## Steps

1. For each stage that runs an agent, pick the template:

   | Stage | Template |
   | --- | --- |
   | Dev (`/approve`) | `starter-kit/automations/dev.md` |
   | QA | `starter-kit/automations/qa.md` |
   | Fix | `starter-kit/automations/fix.md` |
   | `/ask`, `/clarify`, `/refine` | `starter-kit/automations/ask-refine.md` |
   | Product intake | `starter-kit/automations/product-intake.md` |

2. Fill each `{{PLACEHOLDER}}` from the design and profile: repo, default branch,
   gate commands, qa-skip file patterns, risk paths, bot login, human login.
   Leave unknowns as `{{TODO: …}}` and list them for the human.
3. Write the filled files to `<data_dir>/automations/` (ask first). Each file has
   a **Triggers** table and an **Instructions** block to paste into
   [cursor.com/automations](https://cursor.com/automations).
4. If the design uses label routing, propose `starter-kit/workflows/label-router.yml`
   filled for this repo, destined for `workflows_dir`. Install only on approval.
5. Walk the human through the console setup, one automation at a time:
   - Follow-up comment triggers must be **by Me**, never Anyone.
   - QA "PR opened" may be Anyone (the bot opens PRs).
   - Fix wakes on label added `qa-failed` only.
   - Attach the MCPs the instructions need (GitHub; Drive/Figma staging for
     frontend).
6. Optional: use the built-in `automate` skill to create the automations
   directly when the human prefers that over pasting.
7. Hand off to `workflow-measure-handoff`.

## Do not

- Grant agents merge rights or Anyone-triggered follow-ups.
- Drop the 3-iteration Fix cap or the one-verdict-per-wake rule.
