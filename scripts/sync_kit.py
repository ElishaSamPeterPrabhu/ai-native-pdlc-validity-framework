"""Copy the starter kit and validity skills into framework/kit for packaging.

Sources:
  starter-kit/cursor/rules/*          -> framework/kit/rules
  starter-kit/cursor/skills/*         -> framework/kit/skills
  .cursor/skills/validity-*           -> framework/kit/skills
  starter-kit/{automations,profiles,workflows,signal-contract.md,README.md}

Run before building a release. `--check` exits 1 if framework/kit is out of date.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "framework" / "kit"
SK = ROOT / "starter-kit"


def sources() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []

    def add_tree(src: Path, dest: Path) -> None:
        for p in sorted(x for x in src.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
            pairs.append((p, dest / p.relative_to(src)))

    add_tree(SK / "cursor" / "rules", KIT / "rules")
    add_tree(SK / "cursor" / "skills", KIT / "skills")
    for skill in sorted((ROOT / ".cursor" / "skills").glob("validity-*")):
        add_tree(skill, KIT / "skills" / skill.name)
    for name in ("automations", "profiles", "workflows"):
        add_tree(SK / name, KIT / name)
    for name in ("signal-contract.md", "README.md"):
        pairs.append((SK / name, KIT / name))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    pairs = sources()
    expected = {dest for _, dest in pairs}
    stale = [p for p in KIT.rglob("*") if p.is_file() and p not in expected] if KIT.is_dir() else []
    drift = [d for s, d in pairs if not d.is_file() or not filecmp.cmp(s, d, shallow=False)]
    if args.check:
        for p in drift + stale:
            print(f"out of date: {p.relative_to(ROOT)}")
        return 1 if (drift or stale) else 0
    if KIT.is_dir():
        shutil.rmtree(KIT)
    for src, dest in pairs:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    print(f"synced {len(pairs)} files into {KIT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
