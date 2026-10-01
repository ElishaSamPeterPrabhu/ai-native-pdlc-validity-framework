# Product intake agent (product → issue)

Turns meeting notes, sprint-planning output, or product requests into reviewed,
approved issues. Humans approve every issue before it is created.

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
```
