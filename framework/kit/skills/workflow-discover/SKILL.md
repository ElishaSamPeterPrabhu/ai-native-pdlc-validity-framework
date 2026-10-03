---
name: workflow-discover
description: >-
  Read an existing repository and produce repo-profile.json: stack, build/test/lint
  commands, CI, existing Cursor rules/hooks/MCP, ownership, component graph, and
  design sources. Read-only. Use before designing automations for an unfamiliar repo.
---

# Workflow discover (read-only)

## Steps

1. **Layout.** Read `validity.layout.json` (or run `python -m framework init --repo .`
   and confirm paths with the human).
2. **Facts from the CLI.** Run `python -m framework inspect --repo .` and read the
   setup manifest at `setup_manifest_path`. Do not re-derive what it already reports.
3. **Read, don't run.** Collect:
   - Stack and package manager (`package.json`, `pyproject.toml`, `go.mod`, …).
   - Commands: build, test, lint, typecheck, storybook/preview, e2e. Quote them
     exactly from scripts; mark guesses as `unverified`.
   - CI: workflow files under `workflows_dir`, required checks, label automations.
   - Agent surface: files under `rules_dir`, `hooks_path`, `mcp_config_path`,
     `.cursor/skills`, `AGENTS.md`, Copilot instructions.
   - Ownership: `CODEOWNERS`, top contributors (`git shortlog -sn --since=6.months`).
   - Graph: component/module dependency map if present; otherwise note the gap.
   - Design sources (UI repos): Figma links in issues, design docs, design-system repo.
   - Tracker: GitHub issues/labels in use (`gh label list`, `gh issue list --limit 20`).
4. **Write `repo-profile.json`** under `data_dir` (ask before writing):

```json
{
  "repo": "owner/name",
  "profile": "frontend",
  "stack": ["typescript", "storybook"],
  "commands": {"build": "npm run build", "test": "npm test", "lint": "npm run lint", "preview": ""},
  "ci": {"workflows": [".github/workflows/ci.yml"], "required_checks": []},
  "agent_surface": {"rules": [".cursor/rules/code.mdc"], "hooks": false, "mcp": [], "skills": []},
  "ownership": {"codeowners": false, "maintainers": []},
  "graph": {"present": true, "path": "docs/component-graph/component-graph.json"},
  "design_sources": [],
  "tracker": {"kind": "github", "labels": []},
  "gaps": ["no hooks"]
}
```

   Shape rules (validated by `framework/schemas/repo-profile.schema.json`):
   - `profile` is exactly `generic` or `frontend`.
   - `hooks` and `graph.present` are JSON booleans (`true`/`false`), never strings.
   - `stack`, `ci.workflows`, `agent_surface.rules`/`mcp`/`skills`, `gaps` are
     arrays of strings. `commands.*` are single command strings.

5. **Summarize** in 5–8 sentences: what exists, which gaps block automation, and
   which profile (generic or frontend) fits. Then hand off to `workflow-interview`.

## Do not

- Run installs, builds, or tests unless the human asks.
- Invent folders the repo does not have; missing optional paths are gaps.
