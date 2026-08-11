# Online automations + PR review path

## What we can and cannot see

| Source | Visible offline? | How we get it |
| --- | --- | --- |
| Git repo (rules, MCP files, workflows, hooks) | Yes | `python -m framework inspect` |
| Cursor Automations definitions (triggers, prompts) | **No** (no list API today) | User intake from console |
| Cloud Agent run launch/status | Partial via Cloud Agents API | Optional later; not required for diagnose |
| Pull requests + QA/fix comments | Via GitHub or paste | User intake / `gh pr` paste |

So: **offline inspect + user-provided automation/PR details**. AI diagnoses; CLI merges facts.

## Flow

```bash
# optional offline facts
python -m framework init --repo .
python -m framework inspect --repo .

# fill questionnaire → JSON (start from example)
cp framework/templates/intake/user-intake.example.json data/user-intake.json
# edit automations + 1–3 PRs

python -m framework intake --repo . --intake data/user-intake.json \
  --out data/evidence-pack.json

# AI skill validity-diagnose on the pack
# human approves → validity-improve / PR template adoption
```

Or use Cursor skill **`validity-intake`** to interview the user, write the JSON, merge, and diagnose.

## What to tell us (short)

**Setup:** automation names/roles, triggers, stop rules, repair cap, MCP/tools, human-review-always.  
**Each PR:** URL, AC checklist, labels, CI, QA/fix summary, iterations, diff size, what surprised the reviewer, optional Hc/O/Cb/σspec notes.

Templates:

- `framework/templates/intake/SETUP-QUESTIONNAIRE.md`
- `framework/templates/intake/pr-body-formula.md`
- `framework/templates/intake/user-intake.example.json`

## How teams get better with AI + formula metrics

1. **Before merge:** AI fills the formula PR template; blocks “done” without AC+tests+QA evidence.
2. **At review:** Use suggested depth only as a hint; humans keep nonzero review.
3. **After review:** AI maps comments/failures → R vs D gaps → one catalog intervention.
4. **Retest:** Same stratum task; update intake PR fields; re-run `intake` + diagnose.

Mechanical V_obs lanes from CLI are hints. **AI diagnosis** owns layer + policy judgment.
