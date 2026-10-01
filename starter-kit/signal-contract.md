# Signal contract

Every automation speaks these exact signals. The label router, the Timeline
Monitor, and `python -m framework` read them verbatim, so do not paraphrase.

## Commands (human, by Me / allowlisted only)

| Command | Surface | Effect |
| --- | --- | --- |
| `/approve` | Issue | Dev starts if the issue is clear and feasible |
| `/ask`, `/clarify` | Issue or PR | Agent answers on the same surface |
| `/refine` | PR | Apply recent PR + QA comments on the same branch; re-signal QA |

## Comment headers (first line, exact)

| Header | Posted by | Router label |
| --- | --- | --- |
| `Routing: qa-full` | Dev | `qa-full` |
| `Routing: qa-skip` | Dev | `qa-skip` |
| `QA-rerun: add` | Dev / Fix | `qa-rerun` (pulse) |
| `## QA PASSED` | QA | — |
| `## QA PASSED WITH CONCERNS` | QA | `needs-human` |
| `## QA FAILED` (`— functional` / `— visual`) | QA | `qa-failed` |
| `## QA SKIPPED` | QA | — |
| `## QA BLOCKED` | QA | `needs-human` |
| `## NEED CLARIFICATION` | Any agent | `needs-human` |
| `## NOT FEASIBLE` | Any agent | `needs-human` |
| `Fix applied: <sentence>` | Fix | — |
| `Max iterations reached (3 attempts). Requesting human review.` | Fix | `needs-human` |

## Labels

| Label | Meaning | Wakes |
| --- | --- | --- |
| `qa-full` | Functional + visual QA required | QA |
| `qa-skip` | Docs/styles only, QA verifies the skip | QA |
| `qa-rerun` | Re-run QA after a fix or refine | QA |
| `qa-failed` | Latest QA failed | Fix |
| `needs-human` | Blocked on a person | nobody (human) |

The router always removes then adds a label so label-added webhooks fire again.

## Stages (for monitoring)

Product→Issue: `intake` → `review` → `approved` → `issue_created`

Issue→PR: `issue_opened` → `approved` → `dev` → `pr_opened` → `routed` → `qa` →
`fix` (≤3) → `qa_rerun` → `human_review` → `merged` | `closed`

Nexus events (deviations): repeated `## QA FAILED`, `## NEED CLARIFICATION`,
`## NOT FEASIBLE`, `Max iterations reached`, stale > 24h in a stage, label that
contradicts the diff.

Branch naming: `exp/<issue-number>-<short-slug>`.
