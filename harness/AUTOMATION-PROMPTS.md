# Official-repo automation instructions (trimble-oss/modus-wc-2.0)

Paste these into [cursor.com/automations](https://cursor.com/t/trimble/automations) exactly as shown.
Target repository is **trimble-oss/modus-wc-2.0** (not the experiment fork).

## Commands (what you type)

### On a pull request (PR conversation)

These **must** have their own Dev Agent triggers of type **GitHub → Comment on PRs** (not “Comment on issues”). **By Me** only.

| You type | What happens |
|----------|----------------|
| `/ask` | Answer your recent **PR** questions **on the PR**. Do not reply only on the issue. |
| `/clarify` | Same as `/ask`. |
| `/refine` | Apply recent PR + QA comments on the same branch; re-signal QA. |

If you already asked in prose (like [PR #1417](https://github.com/trimble-oss/modus-wc-2.0/pull/1417)), add `/ask` on that PR so the trigger fires.

### On an issue (no PR yet, or start work)

Triggers of type **GitHub → Comment on issues**. **By Me** only.

| You type | What happens |
|----------|----------------|
| `/approve` | Start implementation (only if clear and feasible). |
| `/ask` | Answer questions on the **issue**. |
| `/clarify` | Same as `/ask`. |

**Reply where they wrote:** PR comment → reply on the PR. Issue comment and no PR yet → reply on the issue.

**Exception (not a slash command):** QA Agent **PR opened** may be **by Anyone** so Dev (Cursor bot) can start QA.

If the console defaults a new comment trigger to Anyone, change it to **Me** before Save.

See [`CONSOLE-TRIGGERS.md`](CONSOLE-TRIGGERS.md) — you need **two** `/ask` rows: one Issue comment, one **PR comment**.

---

## Dev Agent — official-repo block

Add at the **end** of existing Agent Instructions (keep PRE-OPEN PR GATE if already present):

```
---

OFFICIAL REPO (trimble-oss/modus-wc-2.0):

GATE BEFORE IMPLEMENTING:
Read the issue AC, Technical notes, Figma/MCP context, and permissions.
Ask: is this clear AND feasible in this PR (scope, API/design, access, would it break the library)?

REPLY SURFACE (always):
- If an open PR already exists for this work, OR this run was triggered from a PR comment: comment on the PR. Do NOT post the answer/fix only on the linked issue.
- If there is no PR yet: comment on the issue.

If UNCLEAR:
  Comment on the correct surface (PR if it exists, else issue):
    ## NEED CLARIFICATION
    - [one question per line]
  Add label needs-human
  Do NOT open a PR if none exists. STOP until the human replies, /ask, or /approve.

If NOT FEASIBLE:
  Comment on the correct surface (PR if it exists, else issue):
    ## NOT FEASIBLE
    Why: [constraint]
    Tried/blocked: [facts]
    Options: [narrow AC | split issue | wontfix]
  Add label needs-human
  Do NOT invent a workaround. Do NOT open a PR if none exists. STOP.

BRANCHING:
- Feature branch: exp/<issue-number>-<short-slug>
- Base on `main` of trimble-oss/modus-wc-2.0

COMMIT CADENCE:
- Commit after each logical sub-task / AC.
- feat(component): … or fix(component): …

CHANGE CLASSIFICATION (after Open PR):
- qa-skip if ALL changes are .scss, .tailwind.ts, .stories.ts, docs, or .md only
- qa-full otherwise

SPEC AWARENESS:
- Check off Acceptance Criteria in the PR body when satisfied.
- Read Technical notes before planning.

PRE-OPEN PR GATE (if not already in instructions):
- Run QA STEP 1 locally (or equivalent documented commands) before Open PR.
- PR body must include: Stop-boundary check: yes|no plus a command table.
```

### Dev Agent — `/ask` / `/clarify` (same automation, extra triggers)

Triggers (both **by Me**, never Anyone):
- GitHub → Issue comment matching `/ask` or `/clarify` on **trimble-oss/modus-wc-2.0** **by Me**
- GitHub → **PR comment** matching `/ask` or `/clarify` on **trimble-oss/modus-wc-2.0** **by Me**

If the human asked questions on the PR without `/ask`, they should follow with `/ask` on that PR so this trigger fires. Then treat the **recent PR comments** (since last `/ask`, or last 20) as the questions.

```
You were invoked by /ask or /clarify from the human (by Me only).

REPLY SURFACE:
- If this is a PR comment (or an open PR exists): comment on the PR.
  Do NOT post the answer only on the linked GitHub issue.
- If there is no PR: comment on the issue.

Read: issue body, PR body/diff if a PR exists, and the last 20 comments on THAT surface
(including the human's questions, ## NEED CLARIFICATION, ## NOT FEASIBLE).
Answer what you can on the same thread. If still blocked, ask ONE tighter question there.

Remove needs-human only when AC is actionable AND feasible.
Do NOT open a PR from /ask unless the human also commented /approve.
Do NOT silently implement a "fix" on the issue while the conversation is on the PR.
```

### Dev Agent — `/refine` (same automation, extra trigger)

Trigger: GitHub → PR comment matching `/refine` on **trimble-oss/modus-wc-2.0** **by Me**.

```
You were invoked by /refine from the human (by Me only).

1. Collect RECENT comments since the last /refine (or last 20):
   - PR conversation, review threads, QA reviews (## QA FAILED / PASSED / SKIPPED)

2. Route (do not run both Fix and a Dev patch on the same /refine):
   - If latest QA is ## QA FAILED and not yet repaired:
     Add qa-failed (or remove then ADD qa-rerun if Fix already ran).
     Comment: "Routed to Fix Agent for the latest QA FAILED."
     STOP.
   - Else: implement the requested refine on the SAME branch (minimal change).
     Push. Comment on the PR what changed (not only on the issue).
     Remove qa-rerun if present, then ADD qa-rerun (GitHub fires on label-added).
     Do NOT claim QA passed.

If the requested refine is not feasible:
  Comment ## NOT FEASIBLE on the PR, add needs-human, STOP.
```

---

## QA Agent — instruction additions

Replace STEP 0 with:

```
STEP 0: Decide if QA is needed.
Read the linked GitHub issue from the PR description.
Read the PR diff to understand what changed.
Check the PR labels.

LABEL ROUTING:
If the PR already has the `qa-skip` label:
  - Read the diff to VERIFY the skip is legitimate.
  - Legitimate skip = changes are ONLY in: .scss, .tailwind.ts, .stories.ts, docs, .md files
  - If CONFIRMED legitimate:
    Comment on the PR: "## QA SKIPPED\nThis PR contains only style/copy/doc changes verified by QA Agent. No functional QA required."
    STOP.
  - If NOT confirmed (the agent mislabeled it — logic or behavior changed):
    Remove the `qa-skip` label.
    Add the `qa-full` label.
    Continue to STEP 1 below.

If the PR has the `qa-full` label OR no routing label: continue to STEP 1.

STEP 1: Run functional QA.
Run these commands in order and capture output:
  npm run tailwind:build
  npm run embed:css
  npm run embed:component-css
  npm test
  npm run lint

If ALL pass:
  Comment: "## QA PASSED\nAll checks passed:\n- tailwind:build ✓\n- embed:css ✓\n- embed:component-css ✓\n- npm test ✓\n- lint ✓"
  STOP.

If ANY fail:
  Comment: "## QA FAILED\n[paste the failing output here]"
  Add the `qa-failed` label to the PR.
  STOP.
```

### QA Agent — official-repo trigger

- Type: GitHub → PR opened
- Repository: **trimble-oss/modus-wc-2.0**
- By: **Anyone** (Dev Agent opens PRs as Cursor bot — this is the only Anyone exception)
- Also: Label added matching `qa-full` and `qa-rerun` on PRs in trimble-oss/modus-wc-2.0

Do **not** add a QA trigger on PR comments from Anyone.

---

## Fix Agent — instruction additions

Keep the 3-iteration cap. **Add** this block (not-feasible / ask human):

```
If the QA failure is not repairable within the AC or would require a library-breaking change:
  Comment on the PR (not the issue): "## NOT FEASIBLE\nWhy: …\nOptions: narrow AC | split issue | human fix"
  Add label needs-human
  Do NOT loop. STOP.

If this is iteration 3+:
  Comment on the PR: "Max iterations reached (3 attempts). Requesting human review."
  Add label needs-human
  STOP.

PUSH AND SIGNAL (after a real fix):
- Push to the same branch
- Remove qa-failed
- Remove qa-rerun if present, then ADD qa-rerun
- Comment on the PR: "Fix applied: [one sentence]"
- Do NOT claim QA passed
- Do NOT post the fix summary only on the linked issue
```

### Fix Agent — official-repo trigger

- Type: GitHub → Label added
- Label: `qa-failed`
- On: PRs
- Repository: **trimble-oss/modus-wc-2.0**

No comment trigger. Do not set Fix to wake on Anyone comments.

---

## GitHub MCP tool fix (Failing tools)

For each automation with a failing GitHub MCP tool:
1. Click "Disconnect" next to the github tool
2. Click "Add Tool or MCP"
3. Search for and re-add "GitHub"
4. Re-authenticate
