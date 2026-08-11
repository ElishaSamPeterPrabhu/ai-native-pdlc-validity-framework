"""Repo layout contract for the Validity Framework.

Target repositories do not share one folder tree. Every inspect/collect/report
path is resolved from ``validity.layout.json`` (or discovered and written by
``python -m framework init``). Cursor agents must read the layout rule first.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

LAYOUT_SCHEMA_VERSION = "1.0.0"
LAYOUT_FILENAMES = (
    "validity.layout.json",
    ".cursor/validity.layout.json",
    "framework/validity.layout.json",
)
LAYOUT_RULE_REL = ".cursor/rules/validity-layout.mdc"


@dataclass
class ValidityLayout:
    """Logical roles → repo-relative paths. Empty string means not configured."""

    schema_version: str = LAYOUT_SCHEMA_VERSION
    # Cursor / harness surfaces (may differ per product repo)
    rules_dir: str = ".cursor/rules"
    hooks_path: str = ".cursor/hooks.json"
    mcp_config_path: str = ".cursor/mcp.json"
    mcp_server_dir: str = "mcp"
    workflows_dir: str = ".github/workflows"
    # Framework package (vendored copy or monorepo path)
    framework_dir: str = "framework"
    # Research / experiment surfaces (optional in adopter repos)
    harness_dir: str = "harness"
    tasks_dir: str = "harness/tasks"
    theory_dir: str = "theory"
    analysis_dir: str = "analysis"
    # Outputs
    data_dir: str = "data"
    metrics_path: str = "data/metrics.jsonl"
    setup_manifest_path: str = "data/setup-manifest.json"
    validity_report_path: str = "data/validity-report.json"
    fit_results_path: str = "data/fit_results.json"
    # Discovery metadata
    source: str = "default"  # default | file | discovered | init
    layout_file: str = ""
    notes: list[str] = field(default_factory=list)

    def resolve(self, root: Path, key: str) -> Path | None:
        rel = getattr(self, key, None)
        if not rel:
            return None
        return (root / rel).resolve()

    def exists(self, root: Path, key: str) -> bool:
        path = self.resolve(root, key)
        return bool(path and path.exists())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidityLayout":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def find_layout_file(repo_root: Path) -> Path | None:
    root = repo_root.resolve()
    for rel in LAYOUT_FILENAMES:
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return None


def load_layout(repo_root: str | Path, layout_path: str | Path | None = None) -> ValidityLayout:
    """Load layout from explicit path, known filenames, or defaults + discovery."""
    root = Path(repo_root).resolve()
    if layout_path:
        path = Path(layout_path)
        if not path.is_absolute():
            path = root / path
        data = json.loads(path.read_text(encoding="utf-8"))
        layout = ValidityLayout.from_dict(data)
        layout.source = "file"
        layout.layout_file = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        return layout

    found = find_layout_file(root)
    if found:
        data = json.loads(found.read_text(encoding="utf-8"))
        layout = ValidityLayout.from_dict(data)
        layout.source = "file"
        layout.layout_file = str(found.relative_to(root))
        return layout

    return discover_layout(root)


def discover_layout(repo_root: Path) -> ValidityLayout:
    """Heuristic discovery when no layout file exists yet."""
    root = repo_root.resolve()
    layout = ValidityLayout(source="discovered", notes=[])

    # rules: prefer .cursor/rules, else .cursorrules file legacy, else AGENTS.md adjacent
    if (root / ".cursor" / "rules").is_dir():
        layout.rules_dir = ".cursor/rules"
    elif (root / ".cursorrules").is_file():
        layout.rules_dir = ""
        layout.notes.append("legacy .cursorrules present; prefer migrating to .cursor/rules/")
    else:
        # search shallow for *rules* dirs used by agents
        for candidate in (".cursor/rules", "rules", ".rules", "ai/rules"):
            if (root / candidate).exists():
                layout.rules_dir = candidate
                break
        else:
            layout.rules_dir = ".cursor/rules"  # intended default for init
            layout.notes.append("rules_dir not found; default .cursor/rules will be created by init")

    hooks_candidates = [
        ".cursor/hooks.json",
        "hooks.json",
        ".cursor/hooks/hooks.json",
    ]
    layout.hooks_path = next((p for p in hooks_candidates if (root / p).is_file()), ".cursor/hooks.json")
    if not (root / layout.hooks_path).is_file():
        layout.notes.append("hooks_path not found; default .cursor/hooks.json")

    mcp_cfg = [".cursor/mcp.json", "mcp.json", ".mcp.json"]
    layout.mcp_config_path = next((p for p in mcp_cfg if (root / p).is_file()), ".cursor/mcp.json")
    mcp_dirs = ["mcp", ".cursor/mcp", "servers/mcp"]
    layout.mcp_server_dir = next((p for p in mcp_dirs if (root / p).is_dir()), "mcp")

    wf = [".github/workflows", "workflows", "ci/workflows"]
    layout.workflows_dir = next((p for p in wf if (root / p).is_dir()), ".github/workflows")

    for key, candidates in (
        ("framework_dir", ["framework", "validity-framework", "tools/validity"]),
        ("harness_dir", ["harness", "experiment/harness", "validity/harness"]),
        ("tasks_dir", ["harness/tasks", "experiment/tasks", "validity/tasks"]),
        ("theory_dir", ["theory", "validity/theory"]),
        ("analysis_dir", ["analysis", "validity/analysis"]),
        ("data_dir", ["data", "validity/data", ".validity/data"]),
    ):
        hit = next((p for p in candidates if (root / p).exists()), candidates[0])
        setattr(layout, key, hit)
        if not (root / hit).exists():
            layout.notes.append(f"{key} not found; using intended path {hit}")

    # Keep derived output paths under data_dir
    data = layout.data_dir.rstrip("/")
    layout.metrics_path = f"{data}/metrics.jsonl"
    layout.setup_manifest_path = f"{data}/setup-manifest.json"
    layout.validity_report_path = f"{data}/validity-report.json"
    layout.fit_results_path = f"{data}/fit_results.json"
    # Prefer tasks under harness when harness exists
    if layout.harness_dir and (root / layout.harness_dir / "tasks").is_dir():
        layout.tasks_dir = f"{layout.harness_dir}/tasks"

    return layout


def write_layout(repo_root: str | Path, layout: ValidityLayout, rel_path: str = "validity.layout.json") -> Path:
    root = Path(repo_root).resolve()
    out = root / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = layout.to_dict()
    payload["source"] = "init" if layout.source in {"default", "discovered", "init"} else layout.source
    payload["layout_file"] = rel_path
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out


def layout_rule_markdown(layout: ValidityLayout) -> str:
    """Always-apply Cursor rule that forces agents to use the layout file."""
    return f"""---
description: Validity Framework layout contract — resolve all paths from validity.layout.json
alwaysApply: true
---

# Validity layout (init / main rule)

Do **not** assume this repository uses the research-repo folder names
(`framework/`, `harness/`, `data/`, `theory/`). Paths differ per product repo.

## Before inspect, collect, calibrate, diagnose, or report

1. Read **`validity.layout.json`** at the repo root (fallback:
   `.cursor/validity.layout.json`).
2. If the file is missing, run:
   ```bash
   python -m framework init --repo .
   ```
   or create it from `framework/templates/validity.layout.json`, then ask the
   human to confirm paths before writing other files.
3. Use **only** the paths in that file for:
   - rules → `rules_dir`
   - hooks → `hooks_path`
   - MCP → `mcp_config_path` / `mcp_server_dir`
   - CI workflows → `workflows_dir`
   - metrics / manifests / reports → `metrics_path`, `setup_manifest_path`,
     `validity_report_path`
   - optional research surfaces → `harness_dir`, `tasks_dir`, `theory_dir`,
     `analysis_dir`, `framework_dir`

## Current layout snapshot (update when validity.layout.json changes)

```json
{json.dumps({k: getattr(layout, k) for k in (
    "rules_dir", "hooks_path", "mcp_config_path", "mcp_server_dir",
    "workflows_dir", "framework_dir", "harness_dir", "tasks_dir",
    "data_dir", "metrics_path", "setup_manifest_path", "validity_report_path",
)}, indent=2)}
```

## Hard rules

- Never invent a folder because the research repo has it.
- Prefer adapting the layout file over forcing the adopter into our tree.
- Require human approval before creating missing directories or installing hooks/rules.
- Mark absent optional paths as measurement gaps, not errors.
"""


def write_layout_rule(repo_root: str | Path, layout: ValidityLayout) -> Path:
    root = Path(repo_root).resolve()
    out = root / LAYOUT_RULE_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(layout_rule_markdown(layout), encoding="utf-8")
    return out


def init_repo_layout(
    repo_root: str | Path,
    *,
    force: bool = False,
    layout_rel: str = "validity.layout.json",
) -> dict[str, Any]:
    """Create validity.layout.json + always-apply layout rule."""
    root = Path(repo_root).resolve()
    existing = find_layout_file(root)
    if existing and not force:
        layout = load_layout(root, existing)
        rule = write_layout_rule(root, layout)
        return {
            "layout_file": str(existing.relative_to(root)),
            "rule_file": str(rule.relative_to(root)),
            "created_layout": False,
            "layout": layout.to_dict(),
        }

    layout = discover_layout(root)
    layout.source = "init"
    layout_path = write_layout(root, layout, layout_rel)
    rule = write_layout_rule(root, layout)
    # Drop stale "not found" notes for paths we just ensured via the rule file.
    if (root / layout.rules_dir).exists():
        layout.notes = [
            n for n in layout.notes if "rules_dir not found" not in n
        ]
        write_layout(root, layout, layout_rel)
        write_layout_rule(root, layout)
    return {
        "layout_file": str(layout_path.relative_to(root)),
        "rule_file": str(rule.relative_to(root)),
        "created_layout": True,
        "layout": layout.to_dict(),
    }
