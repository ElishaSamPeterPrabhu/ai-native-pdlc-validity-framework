---
name: validity-intake
description: >-
  Collect user-provided Cursor Automation setup and PR evidence when console
  automations are not API-readable. Teach what to share, merge into an evidence
  pack, and hand off to validity-diagnose. Use for online automation review,
  remote teams, or when offline git inspect is not enough.
---

# Validity Intake (online automations + PR evidence)

## Reality check

- Offline `inspect` sees git/rules/CI/hooks only.
- Cursor Automations definitions are **not** listable via a management API today.
- Therefore: interview the user (or load their JSON), teach the PR template, merge
  into an evidence pack, then **validity-diagnose** reasons.

## Steps

1. Explain the split in plain language (offline vs console vs PR paste).
2. If no intake file exists, copy and fill:
   - `framework/templates/intake/user-intake.example.json` → layout `data_dir`/user-intake.json
   - Or walk `framework/templates/intake/SETUP-QUESTIONNAIRE.md` conversationally
3. For PRs, teach `framework/templates/intake/pr-body-formula.md`:
   - what fields humans/AI must fill
   - how to ask AI to fill the PR body from the issue
   - how to map review failures back to Hc/O/Cb/σspec and recovery gaps
4. Merge:
   ```bash
   python -m framework intake --repo . --intake data/user-intake.json
   ```
5. Hand off to **validity-diagnose** on the resulting evidence pack.
6. After diagnosis acceptance, either:
   - **validity-improve** for setup controls, and/or
   - help the team adopt the formula PR template + “done” evidence checklist

## Interview prompts (ask the user)

1. Which Dev/QA/Fix automations exist, and what triggers them?
2. When is the agent allowed to say “done”?
3. Cap on repair rounds?
4. Always human PR review?
5. Paste 1–3 recent AI PRs: AC, QA/fix trail, what surprised the reviewer.
6. What do you want: safer review depth, fewer false completions, or both?

## Hard rules

- Do not pretend we scraped the Automations console.
- Do not invent automation instructions the user did not provide.
- Human review never removed.
- Prefer teaching the PR template over one-off advice.
