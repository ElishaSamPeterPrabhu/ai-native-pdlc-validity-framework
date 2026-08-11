# PR body template (formula-useful signals)

Paste into AI-authored PRs (or ask an agent to fill this from the issue).
Humans and the Validity Framework both need these fields.

```markdown
## Summary
<!-- 2–4 sentences: what changed and why -->

## Linked issue
Fixes #

## Complexity stratum
<!-- low | medium | high — human-time estimate style -->
- Guess: 
- Why: 

## Acceptance criteria
<!-- copy from development-ready issue; check only with evidence -->
- [ ] …
- [ ] …

## Evidence (required before "done")
- Tests run: `…` (pass/fail)
- QA automation: link or "QA PASS/FAIL comment …"
- Screenshots / Storybook / a11y: …
- Stop-boundary check: AC + tests + QA evidence present? yes/no

## Formula signals (help review depth)
| Signal | Notes |
| --- | --- |
| Hc (context / failed tool loops) | <!-- quiet \| noisy debug loop --> |
| O (diff opacity) | <!-- files/lines; hard-to-review areas --> |
| Cb (blast radius) | <!-- shared component? API? migration? --> |
| σspec (spec ambiguity) | <!-- AC pinned or still vague? --> |
| Recovery used | <!-- ci / qa / fix rounds / review bot --> |

## Repair history
- Fix iterations: 
- What failed first: 
- What changed after QA:

## Human review ask
<!-- deep | high-level | minimal — suggestion only; human decides -->
- Suggested depth: 
- Please focus on: 
```

## How to have AI fill this

Prompt example:

> Using the linked issue acceptance criteria and the current diff, fill the PR
> body from `framework/templates/intake/pr-body-formula.md`. Do not check an
> AC box unless tests or QA evidence support it. Estimate stratum and blast
> radius honestly. List recovery controls that already ran.

## How to improve the next PR from metrics

After review, ask:

> Map the human review comments and QA failures to decay pressures (Hc, O, Cb,
> σspec) or missing recovery (R). Propose one intervention from the catalog and
> the PR template fields we should tighten next time.
