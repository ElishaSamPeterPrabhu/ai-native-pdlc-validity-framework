---
name: workflow-builder
description: >-
  Entry point for building an AI delivery workflow (product→issue, issue→PR) in
  any repo. Asks what the user wants, then routes to discover, interview, design,
  setup, or measurement skills. Use when someone wants to set up Cursor
  Automations or other agent automations, understand their repo's delivery
  process, or start measuring an existing workflow.
---

# Workflow builder (router)

Build → Monitor → Measure → Improve. This skill only routes; each step lives in
its own skill.

## Step 1 — Ask one question

Use `AskQuestion`:

- "What do you want to do?"
  - Understand my repo and current process (start from scratch)
  - Design a new workflow (I know my process)
  - Set up automations from an agreed design
  - Measure / improve a workflow I already run

## Step 2 — Route

| Answer | Run in order |
| --- | --- |
| Understand | `workflow-discover` → `workflow-interview` → `workflow-design` → setup → `workflow-measure-handoff` |
| Design | `workflow-interview` (short) → `workflow-design` → setup → `workflow-measure-handoff` |
| Set up | Read the existing `workflow-design.json`; `workflow-setup-cursor` or `workflow-setup-other` → `workflow-measure-handoff` |
| Measure | `workflow-measure-handoff` (it hands off to `validity-setup` / `validity-score`) |

"Setup" means `workflow-setup-cursor` when the team uses Cursor Automations, else
`workflow-setup-other`. Ask if unknown.

## Artifacts (all under `data_dir` from `validity.layout.json`)

| File | Written by |
| --- | --- |
| `repo-profile.json` | `workflow-discover` |
| `process-map.json` | `workflow-interview` |
| `workflow-design.json` | `workflow-design` |
| `automations/*.md` (paste-ready) | `workflow-setup-*` |

If `validity.layout.json` is missing, run `python -m framework init --repo .` and
confirm paths with the human first.

## Rules

- Follow `workflow-generic.mdc`; add `workflow-frontend.mdc` for UI repos.
- Never write rules, hooks, workflows, or automations without explicit approval.
- Templates come from `starter-kit/` in this repo; adapt, do not copy blindly.
