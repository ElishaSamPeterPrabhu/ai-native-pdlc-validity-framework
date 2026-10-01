# Gemini meeting-notes intake rubric

This rubric is the shared classifier for the n8n Gemini-notes workflow and any
future Cursor implementation. It is versioned because note wording changes
over time. It is designed to be convenient without turning meeting mechanics
into noisy GitHub issues.

**Version:** 1.0  
**Allowed ceremonies:** Modus `Sprint Planning` and Modus `Sprint Estimating`
only  
**Default action:** classify and show a review card; do not create automatically

## Intake gates

Apply gates in order. A failed gate exits without posting a review card or
creating an issue.

### 1. Gmail filter

The trigger query is a cheap first pass:

```text
from:gemini-notes@google.com subject:"Notes:"
```

The subject must match:

```regex
^Notes:\s*[“"]?(Sprint Planning|Sprint Estimating)[”"]?\b
```

The title check is not sufficient to identify the Modus team.

### 2. Calendar identity

Extract the meeting date and title from the Gemini subject or linked Doc. Query
Google Calendar for the occurrence and verify:

- its `recurringEventId` or stable `iCalUID` is in the configured two-entry
  Modus allowlist;
- the organizer/attendee fallback matches the configured Modus roster when
  Calendar cannot return the series ID.

The allowlist is configuration, not an LLM decision:

```json
{
  "sprintPlanningSeriesId": "<capture once from Modus calendar>",
  "sprintEstimatingSeriesId": "<capture once from Modus calendar>",
  "modusRoster": ["<configured team addresses>"]
}
```

Do not accept a same-named meeting from another Trimble team.

### 3. Doc completeness and idempotency

The “Open meeting notes” Google Doc is the completeness source. Fetch it when
the email body is truncated. Extract the Doc ID and use it as the idempotency
key:

```text
gemini-notes:<google-doc-id>
```

If the Doc ID has already been processed, exit silently with an idempotent
success. Store processed IDs and status in n8n global static data. A failed
classification may be retried with the same Doc ID only when the stored status
is `failed`, never when it is `reviewed` or `created`.

## Extraction contract

The classifier must preserve every actionable-looking item. It may not silently
drop a suggestion because it appears weak. Each extracted item has:

```json
{
  "itemId": "<docId>:ReviewItems:<N>",
  "rawText": "Implement status component",
  "sourceExcerpt": "Suggested next step ...",
  "owner": "James",
  "componentHints": ["status"],
  "links": [],
  "classification": "repo-work",
  "reason": "A repository change is explicitly requested.",
  "duplicateCandidates": [],
  "createEligible": true
}
```

Use both “Suggested next steps” and Quick Notes/decisions. A decision that
changes an existing issue is retained as `decision-record`, not promoted to a
new issue.

## Five-bucket classification

Every extracted item must be assigned exactly one bucket.

### `repo-work`

Use when the item describes a concrete change to the repository, such as:

- implement a component or behavior;
- add or change a supported prop/state;
- fix a reproducible component defect;
- add tests, documentation, or a release-critical implementation artifact.

Create eligibility: yes, after duplicate search and human review.

Required evidence before the review card:

- likely component/file or an explicit repository-wide reason;
- user outcome;
- initial acceptance-criteria sketch;
- related issue candidates.

### `design-work`

Use when the primary deliverable is design or a design decision needed before
implementation:

- create/update a Figma component or state;
- define tokens, variants, responsive behavior, or state coverage;
- research whether an existing Modus component can express the request.

Create eligibility: yes, with the `design-research` label and a design-needed
flag. The issue still goes through Issue Scaffolding and may stop with
clarification.

### `process/meta`

Never create an issue for meeting mechanics, including:

- “Prioritize tickets”
- “Assign tickets”
- “Adjust estimates”
- “Create tickets”
- “Create sub-issues”
- “Move rows into the sprint sheet”
- “Review the backlog”
- generic follow-up or ceremony scheduling

Create eligibility: no. Show it in the review card under a human checklist so
it is not lost.

### `decision-record`

Use when the meeting records a decision or deferral about existing work:

- defer a stacked alert;
- move an image-format release;
- accept/reject a design direction;
- change priority or scope on an existing issue.

Create eligibility: no new issue. Link or comment on the affected existing
issue after human confirmation. If no issue can be identified, show a
clarification item rather than creating a meta-ticket.

### `already-tracked`

Use when duplicate search finds an open or recently closed issue that already
represents the work. Phrases such as “implement the autocomplete
functionality tickets” are a signal to search, not a reason to create a new
issue.

Create eligibility: no. Include the matching issue links and explain whether
the meeting adds a decision, scope change, or no new information.

## Classification decision rules

Apply these rules in order:

1. If the item is a process/meta instruction, classify `process/meta` even if
   it mentions tickets or GitHub.
2. If it changes a known issue's scope or priority, classify `decision-record`.
3. Search GitHub and the backlog before deciding that a repository request is
   new.
4. If an open issue is a clear match, classify `already-tracked`.
5. If the primary output is Figma or a design decision, classify `design-work`.
6. If a repository change is explicit, classify `repo-work`.
7. If intent is ambiguous, retain the raw item and classify it as
   `repo-work` only when a human can make the choice on the review card;
   otherwise mark `needs_clarification` in the reason and do not make it
   create-eligible.

The model must include its reason and evidence for every bucket. It must not
use owner, priority, estimate, or sentence position as a proxy for work type.

## Review card contract

The review card groups all items:

1. Repository work — selected by default only when duplicate search and
   required fields pass.
2. Design work — selected by default only with `design-research`.
3. Process/meta — never selected; shown as checklist.
4. Decision records — shown with existing issue links and a comment/decision
   action.
5. Already tracked — shown with duplicate links.
6. Clarification required — shown with the missing field/questions.

The card footer states:

```text
Completeness check: <N> extracted items, <N> classified items, <N> displayed items.
No item was silently dropped.
Capacity context: read-only values from Team tab, if this was Sprint Planning
or Sprint Estimating. The bot does not assign or reorder work.
```

Only checked repo-work/design-work items call the shared issue service. Each
payload carries:

- the meeting Doc URL and Doc ID;
- the raw source excerpt and Quick Note;
- owner as proposed context, not an assignment command;
- the selected classification and reason;
- relevant component and duplicate-search evidence;
- `autoApprove: false`.

## Accuracy checks

Before enabling creation, run the classifier against a held-out notes document
containing:

- at least one implementation request;
- one Figma/design request;
- “Prioritize Tickets” and “Assign Tickets”;
- a decision that belongs on an existing issue;
- a sentence that already has a GitHub issue;
- an ambiguous item requiring clarification.

Pass criteria:

- every extracted item appears exactly once in the review card;
- no process/meta item becomes an issue;
- duplicate candidates are linked rather than recreated;
- design work receives `design-research`;
- missing information produces questions rather than invented acceptance
  criteria;
- the same Doc ID cannot create a second set of issues.

## Document-led review ledger

The Cursor Docs Review Workflow uses a Google Doc instead of a Chat card for
the human review surface. The classifier writes one row per item to the
`ReviewItems` table:

```text
itemId | round | sourceExcerpt | classification | rationale |
duplicateCandidates | title | summary | owner | designNeeded |
acceptanceCriteria | status | reviewerComment | command |
issueStatus | issueNumber | issueUrl | lastError | updatedAt
```

Allowed statuses are:

```text
needs-review | changes-requested | approved | rejected | duplicate |
clarification | creating | created | failed
```

`approved` requires an explicit reviewer command. `approve-all` is a
whole-document command and must never be inferred from an empty comment or a
default value. The same document contains an `Issues` table with:

```text
itemId | idempotencyKey | status | issueNumber | issueUrl |
createdAt | lastError | reviewComment
```

The stable issue key is `gemini:<meetingDocId>:<itemId>`. Apps Script claims
review rounds under `LockService`; Cursor reuses the same key for retries.
Reviewer comments are stored in `reviewerComment` because the standard
`DocumentApp` surface is not a reliable machine-readable Google Docs comment
thread API. A `@cursor-review`, `review`, or explicit approval command in the
`command` cell is the trigger for the next round.
