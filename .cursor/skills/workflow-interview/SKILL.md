---
name: workflow-interview
description: >-
  Interview the team in short rounds to map their full delivery process (product
  intake, issue, design, dev, QA, review, release), tools, risk tolerance, and
  approvers. Produces process-map.json. Use after workflow-discover or when a team
  wants automations shaped around how they actually work.
---

# Workflow interview

Ask with `AskQuestion`, **2–3 questions per round**, max 4 rounds. Prefill options
from `repo-profile.json` so the human mostly confirms. Skip anything already known.

## Rounds

1. **Intake.** Where does work start? (meetings / sprint planning, product tickets,
   design handoff, bug reports). Who turns it into an issue today? What tracker?
2. **Build.** Who picks up issues? What makes an issue "ready" (acceptance criteria,
   design link, estimate)? Which issues should agents take vs. never take?
3. **Verify.** How is work checked today (CI, manual QA, visual review, design
   review)? What evidence would make you trust an agent PR?
4. **Control.** Who approves start, who reviews, who merges? Risk areas the agent must
   not touch (auth, payments, public API)? Notification channel (GitHub, Slack, email)?
   Which automation platform interests you (Cursor Automations, GitHub Actions,
   other)?

## Output — `process-map.json` under `data_dir` (ask before writing)

```json
{
  "stages": [
    {"name": "intake", "today": "", "owner": "", "tool": "", "pain": ""}
  ],
  "ready_definition": [],
  "agent_scope": {"take": [], "never": []},
  "evidence_for_trust": [],
  "approvers": {"start": "", "review": "", "merge": ""},
  "risk_areas": [],
  "channels": [],
  "platform": "cursor-automations | github-actions | other"
}
```

Read the map back to the human in plain sentences and confirm before handing off to
`workflow-design`.
