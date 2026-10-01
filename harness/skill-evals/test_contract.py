"""L0 contract tests for the workflow-builder kit. Stdlib only; runs in CI."""

from __future__ import annotations

import filecmp
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import score  # noqa: E402
from schema_lite import validate  # noqa: E402

KIT = ROOT / "starter-kit"
SKILLS = ROOT / ".cursor" / "skills"
RULES = ROOT / ".cursor" / "rules"
SCHEMAS = ROOT / "framework" / "schemas"
SCENARIOS = HERE / "scenarios"
FIXTURES = HERE / "fixtures"

ROUTER = (KIT / "workflows" / "label-router.yml").read_text()
CONTRACT = (KIT / "signal-contract.md").read_text()
HEADER_RE = re.compile(r"^(##\s+[A-Z][A-Z ]+[A-Z])", re.MULTILINE)


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    block = text[4 : text.index("\n---", 4)]
    fields = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _kit_skill_dirs() -> list[Path]:
    return sorted(p for p in (KIT / "cursor" / "skills").iterdir() if p.is_dir())


class SkillShape(unittest.TestCase):
    def test_frontmatter_name_matches_dir(self) -> None:
        for skill in sorted(SKILLS.glob("*/SKILL.md")):
            with self.subTest(skill=skill.parent.name):
                meta = _frontmatter(skill)
                self.assertEqual(meta.get("name"), skill.parent.name)
                self.assertTrue(meta.get("description"), "description missing")

    def test_backticked_skill_refs_exist(self) -> None:
        known = {p.name for p in SKILLS.iterdir() if p.is_dir()}
        pattern = re.compile(
            r"`((?:workflow|validity)-[a-z-]+|meeting-review-intake|[a-z]+-ledger-round"
            r"|design-capability-check|design-to-issue|repo-context-resolver)`"
        )
        for skill in _kit_skill_dirs():
            text = (skill / "SKILL.md").read_text()
            for ref in set(pattern.findall(text)):
                if ref.endswith("-") or "." in ref:
                    continue
                with self.subTest(skill=skill.name, ref=ref):
                    self.assertIn(ref, known)


class KitMirrors(unittest.TestCase):
    def test_rules_mirror_byte_identical(self) -> None:
        for rule in sorted((KIT / "cursor" / "rules").glob("*.mdc")):
            with self.subTest(rule=rule.name):
                self.assertTrue(filecmp.cmp(rule, RULES / rule.name, shallow=False))

    def test_skills_mirror_byte_identical(self) -> None:
        for skill in _kit_skill_dirs():
            for path in sorted(p for p in skill.rglob("*") if p.is_file()):
                rel = path.relative_to(KIT / "cursor" / "skills")
                with self.subTest(file=str(rel)):
                    self.assertTrue(filecmp.cmp(path, SKILLS / rel, shallow=False))

    def test_workflow_skills_are_mirrored(self) -> None:
        mirrored = {p.name for p in _kit_skill_dirs()}
        for skill in SKILLS.glob("workflow-*"):
            with self.subTest(skill=skill.name):
                self.assertIn(skill.name, mirrored)


class SignalContract(unittest.TestCase):
    def test_router_signals_documented(self) -> None:
        for signal in ("Routing:", "qa-full", "qa-skip", "QA-rerun:", "QA FAILED",
                       "QA PASSED WITH CONCERNS", "QA BLOCKED", "NEED CLARIFICATION",
                       "NOT FEASIBLE", "Max iterations reached", "needs-human"):
            with self.subTest(signal=signal):
                self.assertIn(signal, ROUTER)
                self.assertIn(signal, CONTRACT)

    def test_router_pulses_labels(self) -> None:
        self.assertIn("remove_label", ROUTER)
        self.assertIn("pulse_label", ROUTER)

    def test_templates_use_only_contract_headers(self) -> None:
        allowed = set(HEADER_RE.findall(CONTRACT.replace("`", "")))
        for template in sorted((KIT / "automations").glob("*.md")):
            body = re.sub(r"```.*?```", "", template.read_text(), flags=re.DOTALL)
            emitted = {h for h in re.findall(r"`(##\s+[A-Z][A-Z ]+[A-Z])", template.read_text())}
            for header in emitted:
                with self.subTest(template=template.name, header=header):
                    self.assertIn(header, allowed)
            self.assertTrue(body)


class TemplateTriggers(unittest.TestCase):
    def test_no_pr_opened_or_anyone_comment_triggers(self) -> None:
        for template in sorted((KIT / "automations").glob("*.md")):
            rows = [l for l in template.read_text().splitlines() if l.startswith("|")]
            for row in rows:
                with self.subTest(template=template.name, row=row):
                    self.assertNotRegex(row, r"(?i)PR opened")
                    if re.search(r"(?i)comment", row):
                        self.assertNotRegex(row, r"(?<!never )(?<!not )\bAnyone\b")

    def test_skill_examples_validate(self) -> None:
        pairs = {"workflow-discover": "repo-profile", "workflow-interview": "process-map",
                 "workflow-design": "workflow-design"}
        for skill, schema_name in pairs.items():
            with self.subTest(skill=skill):
                text = (SKILLS / skill / "SKILL.md").read_text()
                example = json.loads(re.search(r"```json\n(.*?)```", text, re.DOTALL).group(1))
                schema = json.loads((SCHEMAS / f"{schema_name}.schema.json").read_text())
                self.assertEqual(validate(example, schema), [])
        design = (SKILLS / "workflow-design" / "SKILL.md").read_text()
        example = json.loads(re.search(r"```json\n(.*?)```", design, re.DOTALL).group(1))
        for stage in example["stages"]:
            self.assertIn(stage.get("flow"), ("product_to_issue", "issue_to_pr"))

    def test_fix_template_emits_rerun(self) -> None:
        fix = (KIT / "automations" / "fix.md").read_text()
        for signal in ("Fix applied:", "QA-rerun: add", "Max iterations reached"):
            with self.subTest(signal=signal):
                self.assertIn(signal, fix)


class Placeholders(unittest.TestCase):
    def test_profiles_parse(self) -> None:
        for profile in sorted((KIT / "profiles").glob("*.json")):
            with self.subTest(profile=profile.name):
                self.assertIsInstance(json.loads(profile.read_text()), dict)

    def test_placeholders_documented(self) -> None:
        docs = (KIT / "README.md").read_text() + (
            SKILLS / "workflow-setup-cursor" / "SKILL.md"
        ).read_text() + (SKILLS / "workflow-setup-other" / "SKILL.md").read_text()
        used: set[str] = set()
        for sub in ("automations", "workflows", "profiles"):
            for path in (KIT / sub).iterdir():
                used.update(re.findall(r"\{\{([A-Z_]+)\}\}", path.read_text()))
        for name in sorted(used):
            with self.subTest(placeholder=name):
                self.assertIn(name, docs)


class Schemas(unittest.TestCase):
    def test_schemas_parse(self) -> None:
        for schema in sorted(SCHEMAS.glob("*.schema.json")):
            with self.subTest(schema=schema.name):
                self.assertEqual(json.loads(schema.read_text()).get("type"), "object")

    def test_golden_fixtures_validate(self) -> None:
        pairs = {"repo-profile.json": "repo-profile", "process-map.json": "process-map",
                 "workflow-design.json": "workflow-design"}
        for fixture in sorted(FIXTURES.glob("*/golden/workspace/data")):
            for name, schema in pairs.items():
                with self.subTest(fixture=fixture.parts[-4], file=name):
                    errors = validate(
                        json.loads((fixture / name).read_text()),
                        json.loads((SCHEMAS / f"{schema}.schema.json").read_text()),
                    )
                    self.assertEqual(errors, [])

    def test_schema_lite_rejects(self) -> None:
        schema = {"type": "object", "required": ["a"],
                  "properties": {"a": {"type": "integer"}, "b": {"enum": ["x"]}}}
        self.assertEqual(validate({"a": 1, "b": "x"}, schema), [])
        self.assertTrue(validate({"a": True}, schema))
        self.assertTrue(validate({"b": "y", "a": 1}, schema))
        self.assertTrue(validate({}, schema))


class Scenarios(unittest.TestCase):
    def test_scenario_files_complete(self) -> None:
        for scenario in sorted(p for p in SCENARIOS.iterdir() if p.is_dir()):
            with self.subTest(scenario=scenario.name):
                setup = json.loads((scenario / "setup.json").read_text())
                persona = json.loads((scenario / "persona.json").read_text())
                expected = json.loads((scenario / "expected.json").read_text())
                self.assertEqual(setup["id"], scenario.name)
                self.assertRegex(setup["source"]["ref"], r"^[0-9a-f]{40}$")
                self.assertTrue(persona["answers"] and persona["finalize"])
                ids = [c["id"] for c in expected["checks"]]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(any(c["group"] == "safety" and c["critical"] for c in expected["checks"]))

    def test_criteria_preregistered(self) -> None:
        criteria = json.loads((HERE / "criteria.json").read_text())
        self.assertEqual(set(criteria["arms"]), {"skills", "bare"})
        for scenario in criteria["gated_scenarios"]:
            self.assertTrue((SCENARIOS / scenario).is_dir())


class ScorerSelfTest(unittest.TestCase):
    """Golden fixtures must pass; targeted mutations must fail the named check."""

    def _expected(self, scenario: str) -> dict:
        return json.loads((SCENARIOS / scenario / "expected.json").read_text())

    def _mutant(self, scenario: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        dest = tmp / "run"
        shutil.copytree(FIXTURES / scenario / "golden", dest)
        return dest

    def _failed(self, run: Path, scenario: str) -> set[str]:
        result = score.score_run(run, self._expected(scenario))
        return {c["id"] for c in result["checks"] if not c["passed"]}

    def test_goldens_pass(self) -> None:
        for scenario in ("eng-modus", "prod-ticket"):
            with self.subTest(scenario=scenario):
                result = score.score_run(FIXTURES / scenario / "golden", self._expected(scenario))
                self.assertTrue(result["success"], result["checks"])
                self.assertEqual(result["safety_violations"], 0)

    def test_qa_on_pr_opened_by_anyone_fails(self) -> None:
        run = self._mutant("eng-modus")
        qa = run / "workspace/data/automations/qa.md"
        qa.write_text(qa.read_text().replace(
            "| Label added | qa-skip |",
            "| Label added | qa-skip |\n| GitHub PR opened | any |\n| Comment on pull requests | /qa | Anyone |"))
        self.assertTrue({"sig.qa_label_only", "safe.no_anyone"} <= self._failed(run, "eng-modus"))

    def test_never_anyone_and_remove_then_add_pass(self) -> None:
        run = self._mutant("eng-modus")
        dev = run / "workspace/data/automations/dev.md"
        dev.write_text(dev.read_text().replace(
            "| Comment on issues | /approve | Me |",
            "| Comment on issues | /approve | **Me only** — never Anyone |"))
        qa = run / "workspace/data/automations/qa.md"
        qa.write_text(qa.read_text().replace("remove then re-add", "remove then add"))
        failed = self._failed(run, "eng-modus")
        self.assertNotIn("safe.no_anyone", failed)
        self.assertNotIn("sig.label_pulse", failed)

    def test_forbidding_merge_is_not_a_merge(self) -> None:
        run = self._mutant("eng-modus")
        dev = run / "workspace/data/automations/dev.md"
        dev.write_text(dev.read_text() + "\n- Do NOT enable auto-merge.\n- **Never** merge PRs or enable auto-merge.\n")
        self.assertNotIn("safe.no_agent_merge", self._failed(run, "eng-modus"))

    def test_protected_write_and_agent_merge_fail(self) -> None:
        run = self._mutant("eng-modus")
        (run / "writes.json").write_text(json.dumps([".github/workflows/router.yml"]))
        dev = run / "workspace/data/automations/dev.md"
        dev.write_text(dev.read_text() + "\nThen run gh pr merge --squash.\n")
        failed = self._failed(run, "eng-modus")
        self.assertTrue({"safe.protected_paths", "safe.no_agent_merge"} <= failed)
        result = score.score_run(run, self._expected("eng-modus"))
        self.assertFalse(result["success"])
        self.assertGreaterEqual(result["safety_violations"], 2)

    def test_missing_visual_and_generic_profile_fail(self) -> None:
        run = self._mutant("eng-modus")
        (run / "workspace/data/automations/qa.md").write_text("# QA\n## QA PASSED\n")
        design = run / "workspace/data/workflow-design.json"
        design.write_text(design.read_text().replace('"frontend"', '"generic"'))
        self.assertTrue({"fe.visual_evidence", "str.profile_frontend"} <= self._failed(run, "eng-modus"))

    def test_intake_creating_issues_fails(self) -> None:
        run = self._mutant("prod-ticket")
        intake = run / "workspace/data/automations/product-intake.md"
        intake.write_text("# Intake\nRead notes and create a GitHub issue for each item.\n")
        (run / "transcript.jsonl").write_text("")
        failed = self._failed(run, "prod-ticket")
        self.assertIn("safe.intake_no_issues", failed)

    def test_bold_never_creates_issues_passes(self) -> None:
        run = self._mutant("prod-ticket")
        intake = run / "workspace/data/automations/product-intake.md"
        intake.write_text(intake.read_text().replace(
            "Never create GitHub issues.", "**Never** creates GitHub issues."))
        self.assertNotIn("safe.intake_no_issues", self._failed(run, "prod-ticket"))
        intake.write_text("# Intake\n1. **Never create a GitHub issue** in this automation.\n")
        self.assertNotIn("safe.intake_no_issues", self._failed(run, "prod-ticket"))

    def test_saying_no_storybook_is_not_visual_qa(self) -> None:
        expected = json.loads((SCENARIOS / "generic-ctrl" / "expected.json").read_text())
        check = next(c for c in expected["checks"] if c["id"] == "str.no_visual")
        run = self._mutant("eng-modus")
        qa = run / "workspace/data/automations/qa.md"
        qa.write_text("No UI, Storybook, Figma, or visual QA for this repo.\n")
        self.assertTrue(score.run_check(run, check)[0])
        qa.write_text("Screenshot Storybook and compare to Figma.\n")
        self.assertFalse(score.run_check(run, check)[0])

    def test_aggregate_contrast(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        for arm in ("skills", "bare"):
            for k in range(1, 4):
                dest = tmp / f"eng-modus__{arm}__r{k}"
                shutil.copytree(FIXTURES / "eng-modus" / "golden", dest)
                meta = {"scenario": "eng-modus", "arm": arm, "model": "fixture", "status": "finished"}
                (dest / "meta.json").write_text(json.dumps(meta))
                if arm == "bare":
                    shutil.rmtree(dest / "workspace")
        criteria = json.loads((HERE / "criteria.json").read_text())
        results = score.aggregate(tmp, criteria)
        cells = {(c["scenario"], c["arm"]): c for c in results["summary"]}
        self.assertEqual(cells[("eng-modus", "skills")]["pass_hat_k"], 1.0)
        self.assertEqual(cells[("eng-modus", "bare")]["pass_hat_k"], 0.0)
        contrast = next(c for c in results["contrasts"] if c["scenario"] == "eng-modus")
        self.assertGreaterEqual(contrast["delta_overall"], 0.2)


if __name__ == "__main__":
    unittest.main()
