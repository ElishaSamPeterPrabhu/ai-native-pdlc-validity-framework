# Dev Agent follow-ups — `/ask`, `/clarify`, `/refine`

Add these triggers to the **same** Dev automation. All are **by Me** only.

## Triggers

| Type | Filter | By |
| --- | --- | --- |
| GitHub → Comment on issues | matches `/ask` or `/clarify` on `{{REPO}}` | Me |
| GitHub → Comment on PRs | matches `/ask` or `/clarify` on `{{REPO}}` | Me |
| GitHub → Comment on PRs | matches `/refine` on `{{REPO}}` | Me |

## Instructions (append to Dev)

```
IF invoked by /ask or /clarify:
  Reply on the surface where it was written (PR if a PR exists, else issue).
  Read the issue, the PR diff if any, and the last 20 comments on that surface.
  Answer what you can. If still blocked, ask ONE tighter question.
  Do not open a PR unless the human also commented /approve.

IF invoked by /refine:
  Collect comments since the last /refine (or last 20), including QA verdicts.
  If the latest QA is "## QA FAILED" and unrepaired: comment
    "Routed to Fix Agent for the latest QA FAILED." and STOP.
  Else make the requested minimal change on the same branch, run the gate, push,
  comment what changed on the PR, then "QA-rerun: add". Never claim QA passed. Never merge; humans merge.
  If not feasible: "## NOT FEASIBLE" on the PR. STOP.
```
