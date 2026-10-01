# Product intake agent (product → issue)

Turns meeting notes, sprint-planning output, or product requests into reviewed,
approved issues. Humans approve every issue before it is created.

## Existing repo implementation

This repository includes a fuller product-to-issue implementation under
`docs/chat-bots/`:

- `meeting-intake-automation-prompt.md` and `meeting-intake-rubric.md` define
  classification and clarification behavior.
- `workflows/meeting-intake*.json` and `apps-script/` contain the coordinator,
  review, and write-back templates.
- `.cursor/skills/meeting-review-intake`,
  `.cursor/skills/review-ledger-round`, and
  `.cursor/skills/approve-ledger-round` keep intake, review, and approval as
  separate human-controlled stages.

Use those adapters when adopting this repository's Google Docs/Sheets flow. For
another repository, keep the generic ledger contract below and replace the
source-specific templates.

## Ledger

A sheet or `data/ledger.json` with one row per candidate item:

| Column | Meaning |
| --- | --- |
| `id` | Stable row id |
| `source` | Meeting / doc / request link |
| `summary` | One-line item |
| `classification` | `dev` \| `design` \| `bug` \| `question` \| `drop` |
| `acceptance_criteria` | Draft AC |
| `agent_comment` | Agent's review notes or questions |
| `status` | `draft` → `in_review` → `approved` \| `rejected` → `issue_created` |
| `approved_by` | Human login |
| `issue_url` | Filled when the issue is created |

## Triggers

| Type | Filter | By |
| --- | --- | --- |
| Schedule or webhook | New meeting notes in `{{INTAKE_SOURCE}}` | — |
| Ledger change | Row `status` set to `approved` | Me |

## Instructions

```
You are the Product Intake Agent for {{REPO}}. Follow workflow-generic.mdc.

ON NEW NOTES: extract candidate work items. For each, add a ledger row with
status=draft, classification, a one-line summary, and draft acceptance criteria.
Unclear items: put "## NEED CLARIFICATION" questions in agent_comment.
Set status=in_review. Never create issues from draft or in_review rows.

ON APPROVED ROW: create one issue in {{REPO}} using {{ISSUE_TEMPLATE}} with the
summary, acceptance criteria, source link, and design source (QA-source line for UI
work). Label {{INTAKE_LABEL}}. Write issue_url back and set status=issue_created.
Do not comment /approve on the issue; implementation start stays human.
Never merge or approve PRs; humans merge.
```
