"""Tests for init-kit and check-kit."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from framework.kit import install_kit, kit_root
from framework.kitcheck import check_files, collect_files, has_critical_failure

ROOT = Path(__file__).resolve().parents[1]

GOOD = {
    "dev.md": "| GitHub → Comment on issues | matches `/approve` | Me |\n"
    "Never merge or enable auto-merge; humans merge.\n"
    "Routing: qa-full\nQA-rerun: add\n",
    "qa.md": "| GitHub → Label added | `qa-full` | n/a |\n"
    "## QA PASSED\n## QA FAILED\nNever merge; humans merge.\n",
    "fix.md": "Max iterations reached (3 attempts). Requesting human review.\n"
    "needs-human\nRemove qa-rerun, then add it again.\nFix applied: done\n",
}


def write(tmp: Path, files: dict[str, str]) -> list[Path]:
    for name, body in files.items():
        (tmp / name).write_text(body, encoding="utf-8")
    return collect_files(tmp)


def failed_ids(findings) -> set[str]:
    return {f.rule_id for f in findings if not f.passed and f.critical}


class CheckKitTests(unittest.TestCase):
    def check(self, **overrides: str) -> list:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            files = dict(GOOD)
            for name, body in overrides.items():
                files[name.replace("_", ".")] = body
            return check_files(write(tmp, files))

    def test_clean_files_pass(self) -> None:
        findings = self.check()
        self.assertFalse(has_critical_failure(findings))

    def test_anyone_comment_trigger_fails(self) -> None:
        findings = self.check(dev_md=GOOD["dev.md"] + "| GitHub → Comment on PRs | `/ask` | Anyone |\n")
        self.assertIn("safe.no_anyone", failed_ids(findings))

    def test_negated_anyone_is_allowed(self) -> None:
        findings = self.check(dev_md=GOOD["dev.md"] + "| GitHub → Comment on PRs | `/ask` | Me, never Anyone |\n")
        self.assertNotIn("safe.no_anyone", failed_ids(findings))

    def test_agent_merge_fails(self) -> None:
        findings = self.check(fix_md=GOOD["fix.md"] + "Then run gh pr merge --squash\n")
        self.assertIn("safe.no_agent_merge", failed_ids(findings))

    def test_negated_merge_line_is_allowed(self) -> None:
        findings = self.check(fix_md=GOOD["fix.md"] + "Never run gh pr merge.\n")
        self.assertNotIn("safe.no_agent_merge", failed_ids(findings))

    def test_qa_on_pr_opened_fails(self) -> None:
        findings = self.check(qa_md=GOOD["qa.md"] + "| GitHub → PR opened | any | n/a |\n")
        self.assertIn("sig.qa_label_only", failed_ids(findings))

    def test_missing_cap_fails(self) -> None:
        findings = self.check(fix_md="Fix applied: done\nNever merge; humans merge.\n")
        self.assertIn("sig.fix_cap", failed_ids(findings))

    def test_missing_human_merge_line_fails(self) -> None:
        bodies = {k: v.replace("Never merge or enable auto-merge; humans merge.", "").replace("Never merge; humans merge.", "") for k, v in GOOD.items()}
        findings = self.check(dev_md=bodies["dev.md"], qa_md=bodies["qa.md"])
        self.assertIn("safe.human_merges", failed_ids(findings))

    def test_missing_needs_human_label_is_only_a_warning(self) -> None:
        findings = self.check(fix_md=GOOD["fix.md"].replace("needs-human", ""))
        self.assertFalse(has_critical_failure(findings))
        warn = [f for f in findings if f.rule_id == "sig.needs_human"][0]
        self.assertFalse(warn.passed)
        self.assertFalse(warn.critical)


class InstallKitTests(unittest.TestCase):
    def test_bundled_kit_exists_with_builder_skill(self) -> None:
        self.assertTrue((kit_root() / "skills" / "workflow-builder" / "SKILL.md").is_file())
        self.assertTrue((kit_root() / "skills" / "validity-score" / "SKILL.md").is_file())

    def test_install_copies_then_skips_existing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            first = install_kit(repo)
            self.assertTrue(all(a.status == "copied" for a in first))
            self.assertTrue((repo / ".cursor/skills/workflow-builder/SKILL.md").is_file())
            self.assertTrue((repo / "starter-kit/automations/dev.md").is_file())
            marker = repo / ".cursor/rules/workflow-generic.mdc"
            marker.write_text("local edit", encoding="utf-8")
            second = install_kit(repo)
            self.assertTrue(all(a.status == "skipped" for a in second))
            self.assertEqual(marker.read_text(encoding="utf-8"), "local edit")
            install_kit(repo, force=True)
            self.assertNotEqual(marker.read_text(encoding="utf-8"), "local edit")

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            actions = install_kit(repo, dry_run=True)
            self.assertTrue(actions)
            self.assertEqual(list(repo.iterdir()), [])


class KitSyncTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / "starter-kit").is_dir(), "source tree not available")
    def test_bundled_kit_matches_sources(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sync_kit.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
