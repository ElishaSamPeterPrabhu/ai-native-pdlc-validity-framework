# Modus backlog and sprint-sheet enrichment

The Google Sheet is a planning and estimation surface. GitHub issues are the
actionable source of truth. Enrichment improves issue quality and writes the
issue number back to the row; it does not silently change priority, estimates,
assignment, readiness, or sprint order.

## Verified sheet model

Spreadsheet ID:
`1RrGZcATDM-K_YCFkhkiiR6-KfvSa6ZqAp6qzhx4Jl6g`

| Tab | Role | Resolution |
| --- | --- | --- |
| `Modus Backlog` | grooming / ready / in-refinement planning | stable tab; gid is configuration |
| `Team` | estimated, actual, and remaining capacity | stable tab; read-only context |
| `Sprint MM/DD` | rolling sprint commitment | choose the latest date-named tab dynamically |
| `Closed` | closed planning items | stable tab |
| `Sprint Template` | source for a new sprint tab | never treated as the current sprint |

The current observed sprint tab was `Sprint 09/02`. Most rows already had issue
numbers, while the broader backlog contained one-line rows and duplicates.
Examples from the current sprint demonstrate why scaffolding must research
before drafting:

- [#1459](https://github.com/trimble-oss/modus-wc-2.0/issues/1459) only says
  to add XS and XL to textarea.
- [#1462](https://github.com/trimble-oss/modus-wc-2.0/issues/1462) only says
  to design a monochromatic logo variant.
- [#1468](https://github.com/trimble-oss/modus-wc-2.0/issues/1468) asks to
  test a PR without stating scenarios or expected results.

## Row intake

Normalize columns into:

```json
{
  "rowKey": "tab:row-number",
  "title": "Add XS and XL size for text area component",
  "issueNumber": null,
  "category": "Forms",
  "type": "Feature",
  "product": "Modus",
  "priority": "High",
  "size": "3",
  "assignedTo": "James",
  "designSource": "TBD",
  "ready": "Yes",
  "blocker": "",
  "sprint": "Sprint 09/02"
}
```

The `sheet-intake` object is additional context, not an instruction to assign
work:

```json
{
  "title": "...",
  "category": "...",
  "type": "...",
  "product": "...",
  "priority": "...",
  "size": "...",
  "design_source": "...",
  "sprint": "..."
}
```

## Enrichment algorithm

For each row in `Ready` and `In Refinement`:

1. Validate the row key and preserve the original values.
2. Search GitHub by existing issue number, exact links, normalized title, and
   likely component terms.
3. Search other sheet rows for the same issue number and normalized title.
4. If an exact issue number exists, inspect whether the body contains
   Context, Proposed Change, Acceptance Criteria, Design Notes, Technical
   Notes, Test Plan, and Sources. Send incomplete issues to Issue Scaffolding
   with `issue_url`; do not create a second issue.
5. If no issue number exists and no duplicate is found, call the shared issue
   service with `sheet-intake`, component evidence, design source, and
   `autoApprove: false`. Write the returned number/link back to the exact row.
6. If a duplicate candidate is plausible but not exact, show both rows/issues
   in a review card. Do not merge or choose one automatically.
7. For Figma-product or design-source rows, add `design-research` to the
   scaffolding labels and require the capability check.

The service must preserve a stable idempotency key:

```text
sheet:<spreadsheet-id>:<tab-name>:<row-number>:<normalized-title-hash>
```

If a sheet row moves to another tab, the issue number remains the primary
link; the workflow does not create a new issue because the tab changed.

## Readiness report

The workflow posts a review card for:

- `Ready?=Yes` with `Design Source=TBD`;
- missing Priority or PM/Team Est. Size;
- duplicate issue numbers or likely duplicate titles;
- issue-numbered rows missing scaffold sections;
- upcoming sprint rows without an issue number;
- a design/development pair that lacks cross-links.

The card includes Team-tab remaining capacity as read-only context. It does not
assign work or reorder rows.

## Sprint readiness check

Resolve the current sprint dynamically:

1. list tabs;
2. select tabs matching `^Sprint \d{1,2}/\d{1,2}$`;
3. parse the date in the workspace timezone;
4. choose the latest date not in the future, or the next scheduled tab for a
   pre-planning run;
5. inspect every non-empty work row.

Never hardcode `Sprint 09/02` or its gid. The tab is cloned each sprint.

Before Sprint Planning, every committed row should have:

- a GitHub issue number;
- a complete scaffold or an explicit clarification;
- a design source or `design needed`;
- no unresolved duplicate candidate.

Rows that fail are surfaced in the review card rather than “fixed” with
guessed values.

## Paired feature handling

When two rows describe design and implementation for the same feature (for
example, a Figma row and a Web Components row), the workflow:

- sends both through duplicate search;
- preserves separate ownership and estimates;
- links the issues bidirectionally after human confirmation;
- adds a shared feature reference to Technical Notes;
- runs Design-Research before design work is marked ready.

## Safe sheet writes

Only these writes are automated:

- Issue # / issue URL in the exact source row after the shared service returns;
- an explicit enrichment status and timestamp in designated columns, if the PO
  adds them.

The workflow does not overwrite title, category, priority, size, assignee,
design source, readiness, blocker, or sprint columns. If those fields are
missing, the report asks a human.

The sanitized template is
[`workflows/backlog-enrichment.template.json`](workflows/backlog-enrichment.template.json).
