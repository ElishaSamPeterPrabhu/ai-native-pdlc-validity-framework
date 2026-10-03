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
   - Copy signal-contract strings **verbatim** (`Routing: qa-full`,
     `QA-rerun: add`, `## QA FAILED`, `Fix applied:`, `Max iterations reached`).
     The label router matches exact text; `QA-rerun:` alone does not fire.
   - Keep every `Never …` / `Do not …` line from the template in the filled file,
     including "Never merge … humans merge". Rewording is fine; dropping is not.
   - If the team has no Fix agent, merge `fix.md` into Dev's `qa-failed` section
     whole: repair only what `## QA FAILED` lists, end with `Fix applied: …` and
     `QA-rerun: add`, and keep the 3-iteration cap.
3. Write the filled files to `<data_dir>/automations/` (ask first). Each file has
   a **Triggers** table and an **Instructions** block to paste into
   [cursor.com/automations](https://cursor.com/automations).
4. If the design uses label routing, propose `starter-kit/workflows/label-router.yml`
   filled for this repo, destined for `workflows_dir`. Install only on approval.
5. Walk the human through the console setup, one automation at a time:
   - Every comment trigger on every agent must be **by Me**, never Anyone. That
     includes QA/Fix handoff comments; route those through the label router.
   - QA wakes on label added (`qa-full`, `qa-skip`, `qa-rerun`) only, never on
     PR opened.
   - Fix (or Dev, if the team has no Fix agent) wakes on label added `qa-failed`
     only.
   - Attach the MCPs the instructions need (GitHub; Drive/Figma staging for
     frontend).
6. Optional: use the built-in `automate` skill to create the automations
   directly when the human prefers that over pasting.
7. Hand off to `workflow-measure-handoff`.

## Do not

- Grant agents merge rights or put Anyone on any comment trigger.
- Drop the 3-iteration Fix cap or the one-verdict-per-wake rule.
