"""Install the bundled workflow-builder kit into a repository.

The kit is the same content as ``starter-kit/`` plus the ``validity-*`` skills,
copied into ``framework/kit`` by ``scripts/sync_kit.py`` before a release.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from framework.packaging_paths import bundled_path

# bundled folder -> destination relative to the target repo
DESTINATIONS: tuple[tuple[str, str], ...] = (
    ("rules", ".cursor/rules"),
    ("skills", ".cursor/skills"),
    ("automations", "starter-kit/automations"),
    ("profiles", "starter-kit/profiles"),
    ("workflows", "starter-kit/workflows"),
)
SINGLE_FILES: tuple[tuple[str, str], ...] = (
    ("signal-contract.md", "starter-kit/signal-contract.md"),
    ("README.md", "starter-kit/README.md"),
)


@dataclass(frozen=True)
class KitAction:
    destination: Path
    status: str  # "copied" | "skipped" | "would-copy"


def kit_root() -> Path:
    return bundled_path("kit")


def _iter_sources(root: Path):
    for src_name, dest_rel in DESTINATIONS:
        base = root / src_name
        if not base.is_dir():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            yield path, Path(dest_rel) / path.relative_to(base)
    for src_name, dest_rel in SINGLE_FILES:
        path = root / src_name
        if path.is_file():
            yield path, Path(dest_rel)


def install_kit(repo: Path, force: bool = False, dry_run: bool = False) -> list[KitAction]:
    root = kit_root()
    if not root.is_dir():
        raise FileNotFoundError(f"bundled kit not found at {root}")
    actions: list[KitAction] = []
    for src, dest_rel in _iter_sources(root):
        dest = repo / dest_rel
        if dest.exists() and not force:
            actions.append(KitAction(dest_rel, "skipped"))
            continue
        if dry_run:
            actions.append(KitAction(dest_rel, "would-copy"))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        actions.append(KitAction(dest_rel, "copied"))
    return actions
