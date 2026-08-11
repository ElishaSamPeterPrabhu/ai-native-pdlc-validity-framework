# Exact automation instruction updates for the 5-issue live run

Paste these into cursor.com/automations exactly as shown. Changes vs the
current instructions are marked with [ADDED] / [CHANGED]. Keep all existing
text unless overridden.

---

## Dev Agent — instruction additions

Add the following block at the **end** of the existing Agent Instructions,
after all current content:

```
---

EXPERIMENT INSTRUCTIONS (modus-wc-2.0 fork):
When working on the ElishaSamPeterPrabhu/modus-wc-2.0 repository:

BRANCHING:
- Create the feature branch as: exp/<issue-number>-<short-slug>
  Example: exp/28-checkbox-switch-value
- Base all work on the `main` branch of the fork.

COMMIT CADENCE (checkpointing factor):
- Commit frequently — after each logical sub-task, not just at the end.
- Minimum: one commit after each acceptance criterion is addressed.
- Commit message format: "feat(component): <description>" or "fix(component): <description>"

CHANGE CLASSIFICATION (QA routing):
After opening the PR, examine your own diff and add ONE label:
- `qa-skip` if ALL changes are: .scss files, .tailwind.ts files, .stories.ts files, docs, or .md files only
- `qa-full` for everything else (logic changes, new slots, event handling, test files)

SPEC AWARENESS:
- The issue body contains "Acceptance Criteria" checkboxes. Check each one off
  in the PR body or a comment when it is satisfied.
- The issue body may contain "Technical notes" — read them before planning.
```

---

## QA Agent — instruction additions

Replace the existing STEP 0 block with this expanded version:

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

---

## Fix Agent — instruction changes (none needed)

The existing Fix Agent instructions are correct. The 3-iteration memory cap,
qa-failed label trigger, and needs-human escalation path are all right.
No changes required.

---

## QA Agent — also add the modus-wc-2.0 fork trigger

In the Triggers section, add a new trigger:
- Type: GitHub → PR opened
- Repository: ElishaSamPeterPrabhu/modus-wc-2.0
- By: Anyone (PRs opened by the Dev Agent cloud user, not by you)

---

## Fix Agent — also add the modus-wc-2.0 fork trigger

In the Triggers section, add a new trigger:
- Type: GitHub → Label change (label added)
- Label: qa-failed
- Repository: ElishaSamPeterPrabhu/modus-wc-2.0

---

## GitHub MCP tool fix (applies to all automations showing "Failing")

For each automation with a failing GitHub MCP tool:
1. Click "Disconnect" next to the github tool
2. Click "Add Tool or MCP"
3. Search for and re-add "GitHub"
4. Re-authenticate
