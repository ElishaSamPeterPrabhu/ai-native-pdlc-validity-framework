"""Deterministic scorer for workflow-builder skill evaluation runs.

A run directory (written by run_eval.py) contains:
    meta.json          scenario, arm, repeat, model, ids, status
    transcript.jsonl   {"turn", "role", "text"} per message
    writes.json        repo-relative paths the run created or modified
    workspace/         copies of those files

Each scenario's expected.json lists checks; no LLM is involved in scoring.

Usage:
    python harness/skill-evals/score.py --runs data/skill-evals/runs --out data/skill-evals
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_ROOT / "theory"))
sys.path.insert(0, str(_HERE))

import formula as F  # noqa: E402
from schema_lite import validate  # noqa: E402

SCENARIOS_DIR = _HERE / "scenarios"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yml", ".yaml", ".mdc"}


def load_expected(scenario: str) -> dict:
    return json.loads((SCENARIOS_DIR / scenario / "expected.json").read_text())


def _workspace_files(run_dir: Path) -> list[Path]:
    ws = run_dir / "workspace"
    if not ws.is_dir():
        return []
    return [p for p in ws.rglob("*") if p.is_file()]


def _match(run_dir: Path, pattern: str) -> list[Path]:
    ws = run_dir / "workspace"
    hits = []
    for p in _workspace_files(run_dir):
        rel = p.relative_to(ws).as_posix()
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(p.name, pattern):
            hits.append(p)
    return sorted(hits)


def _read_text(paths: list[Path]) -> str:
    return "\n".join(
        p.read_text(errors="replace") for p in paths if p.suffix in TEXT_SUFFIXES
    )


def _transcript(run_dir: Path, role: str | None) -> str:
    path = run_dir / "transcript.jsonl"
    if not path.exists():
        return ""
    lines = []
    for raw in path.read_text().splitlines():
        if raw.strip():
            msg = json.loads(raw)
            if role is None or msg.get("role") == role:
                lines.append(msg.get("text", ""))
    return "\n".join(lines)


def _collect(node: object, pointer: list[str]) -> list[str]:
    """Collect string leaves at a dotted pointer; `key[*]` walks a list."""
    if not pointer:
        if isinstance(node, list):
            return [str(x) for x in node]
        return [] if node is None else [str(node)]
    head, rest = pointer[0], pointer[1:]
    if head.endswith("[*]"):
        key = head[:-3]
        items = node.get(key, []) if isinstance(node, dict) else []
        out: list[str] = []
        for item in items if isinstance(items, list) else []:
            out.extend(_collect(item, rest))
        return out
    if isinstance(node, dict) and head in node:
        return _collect(node[head], rest)
    return []


def _regex_hits(text: str, patterns: list[str]) -> list[bool]:
    return [re.search(p, text, re.MULTILINE) is not None for p in patterns]


def run_check(run_dir: Path, check: dict) -> tuple[bool, str]:
    kind = check["type"]
    if kind == "artifact_exists":
        hits = _match(run_dir, check["name"])
        return bool(hits), f"{len(hits)} match(es) for {check['name']}"

    if kind == "schema_valid":
        hits = _match(run_dir, check["name"])
        if not hits:
            return False, f"no {check['name']}"
        schema = json.loads((_ROOT / check["schema"]).read_text())
        try:
            instance = json.loads(hits[0].read_text())
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON: {exc}"
        errors = validate(instance, schema)
        return not errors, "; ".join(errors[:3]) or "valid"

    if kind == "json_includes":
        hits = _match(run_dir, check["name"])
        if not hits:
            return False, f"no {check['name']}"
        try:
            data = json.loads(hits[0].read_text())
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON: {exc}"
        found = " ".join(_collect(data, check["pointer"].split("."))).lower()
        results = [v.lower() in found for v in check["values"]]
        ok = all(results) if check.get("mode", "all") == "all" else any(results)
        missing = [v for v, r in zip(check["values"], results) if not r]
        return ok, f"missing {missing}" if missing else "all present"

    if kind in ("text_includes", "text_excludes"):
        paths: list[Path] = []
        for glob in check["globs"]:
            paths.extend(_match(run_dir, glob))
        text = _read_text(paths)
        if check.get("include_transcript"):
            text += "\n" + _transcript(run_dir, "assistant")
        if kind == "text_includes" and not text.strip():
            return False, f"no files for {check['globs']}"
        hits = _regex_hits(text, check["patterns"])
        if kind == "text_excludes":
            bad = [p for p, h in zip(check["patterns"], hits) if h]
            return not bad, f"forbidden {bad}" if bad else "clean"
        ok = all(hits) if check.get("mode", "all") == "all" else any(hits)
        missing = [p for p, h in zip(check["patterns"], hits) if not h]
        return ok, f"missing {missing}" if missing else "all present"

    if kind == "transcript_includes":
        text = _transcript(run_dir, check.get("role", "assistant"))
        hits = _regex_hits(text, check["patterns"])
        ok = all(hits) if check.get("mode", "all") == "all" else any(hits)
        missing = [p for p, h in zip(check["patterns"], hits) if not h]
        return ok, f"missing {missing}" if missing else "all present"

    if kind == "no_protected_writes":
        writes_path = run_dir / "writes.json"
        writes = json.loads(writes_path.read_text()) if writes_path.exists() else []
        bad = [w for w in writes if any(fnmatch.fnmatch(w, g) for g in check["globs"])]
        return not bad, f"protected writes {bad}" if bad else "none"

    raise ValueError(f"unknown check type {kind!r}")


def score_run(run_dir: Path, expected: dict) -> dict:
    checks = []
    for check in expected["checks"]:
        ok, detail = run_check(run_dir, check)
        checks.append(
            {
                "id": check["id"],
                "group": check["group"],
                "critical": check.get("critical", False),
                "passed": ok,
                "detail": detail,
            }
        )
    critical = [c for c in checks if c["critical"]]
    safety = [c for c in checks if c["group"] == "safety"]
    groups: dict[str, list[bool]] = {}
    for c in checks:
        groups.setdefault(c["group"], []).append(c["passed"])
    return {
        "overall": round(sum(c["passed"] for c in checks) / len(checks), 4),
        "critical_rate": round(sum(c["passed"] for c in critical) / len(critical), 4)
        if critical
        else 1.0,
        "success": all(c["passed"] for c in critical),
        "safety_violations": sum(not c["passed"] for c in safety),
        "groups": {g: round(sum(v) / len(v), 4) for g, v in groups.items()},
        "checks": checks,
    }


def aggregate(runs_dir: Path, criteria: dict) -> dict:
    cells: dict[tuple[str, str, str], list[dict]] = {}
    per_run = []
    for run_dir in sorted(p for p in runs_dir.iterdir() if (p / "meta.json").exists()):
        meta = json.loads((run_dir / "meta.json").read_text())
        result = score_run(run_dir, load_expected(meta["scenario"]))
        result.update(
            {
                "run": run_dir.name,
                "scenario": meta["scenario"],
                "arm": meta["arm"],
                "model": meta.get("model"),
                "status": meta.get("status"),
            }
        )
        per_run.append(result)
        cells.setdefault((meta.get("model") or "unknown", meta["scenario"], meta["arm"]), []).append(result)

    summary = []
    for (model, scenario, arm), results in sorted(cells.items()):
        n = len(results)
        c = sum(r["success"] for r in results)
        summary.append(
            {
                "model": model,
                "scenario": scenario,
                "arm": arm,
                "n": n,
                "pass_at_1": round(c / n, 4),
                "pass_hat_k": round(F.pass_hat_k(c, n), 4),
                "mean_overall": round(sum(r["overall"] for r in results) / n, 4),
                "mean_critical_rate": round(
                    sum(r["critical_rate"] for r in results) / n, 4
                ),
                "safety_violations": sum(r["safety_violations"] for r in results),
            }
        )

    contrasts = []
    for model, scenario in sorted({(s["model"], s["scenario"]) for s in summary}):
        by_arm = {s["arm"]: s for s in summary if (s["model"], s["scenario"]) == (model, scenario)}
        if "skills" in by_arm and "bare" in by_arm:
            contrasts.append(
                {
                    "model": model,
                    "scenario": scenario,
                    "delta_overall": round(
                        by_arm["skills"]["mean_overall"] - by_arm["bare"]["mean_overall"], 4
                    ),
                }
            )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": sorted({r["model"] for r in per_run if r["model"]}),
        "summary": summary,
        "contrasts": contrasts,
        "criteria": evaluate_criteria(summary, contrasts, criteria),
        "runs": per_run,
    }


def evaluate_criteria(summary: list[dict], contrasts: list[dict], criteria: dict) -> dict:
    """Verdict per model, per gated scenario: {model: {scenario: verdict}}."""
    out: dict[str, dict] = {}
    for model in sorted({s["model"] for s in summary}) or ["none"]:
        out[model] = {
            scenario: _verdict(
                next((s for s in summary if (s["model"], s["scenario"], s["arm"]) == (model, scenario, "skills")), None),
                next((c for c in contrasts if (c["model"], c["scenario"]) == (model, scenario)), None),
                criteria,
            )
            for scenario in criteria["gated_scenarios"]
        }
    return out


def _verdict(cell: dict | None, contrast: dict | None, criteria: dict) -> dict:
    if cell is None:
        return {"status": "not_run"}
    checks = {
        "critical_rate": cell["mean_critical_rate"] >= criteria["min_critical_rate"],
        "pass_hat_k": cell["pass_hat_k"] >= criteria["min_pass_hat_k"],
        "no_safety_violations": cell["safety_violations"] == 0,
        "beats_bare": contrast is not None
        and contrast["delta_overall"] >= criteria["min_delta_vs_bare"],
    }
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks}


def write_report(results: dict, out_dir: Path) -> None:
    lines = [
        "# Workflow-builder skill evaluation",
        "",
        f"Generated {results['generated_at']} · models: {', '.join(results['models']) or 'n/a'}",
        "",
        "| Model | Scenario | Arm | n | pass@1 | pass^k | overall | critical | safety violations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in results["summary"]:
        lines.append(
            f"| {s['model']} | {s['scenario']} | {s['arm']} | {s['n']} | {s['pass_at_1']} | "
            f"{s['pass_hat_k']} | {s['mean_overall']} | {s['mean_critical_rate']} | "
            f"{s['safety_violations']} |"
        )
    lines += ["", "## Pre-registered criteria", ""]
    for model, verdicts in results["criteria"].items():
        for scenario, verdict in verdicts.items():
            lines.append(f"- **{model} / {scenario}:** {verdict['status']} {verdict.get('checks', '')}")
    failed = sorted(
        {c["id"] for r in results["runs"] if r["arm"] == "skills" for c in r["checks"] if not c["passed"]}
    )
    lines += ["", "## Failed checks in the skills arm", ""]
    lines += [f"- `{c}`" for c in failed] or ["- none"]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default=str(_ROOT / "data/skill-evals/runs"))
    parser.add_argument("--out", default=str(_ROOT / "data/skill-evals"))
    args = parser.parse_args()
    criteria = json.loads((_HERE / "criteria.json").read_text())
    out_dir = Path(args.out)
    os.makedirs(out_dir, exist_ok=True)
    if not Path(args.runs).is_dir():
        sys.exit(f"no runs at {args.runs}; run run_eval.py first")
    results = aggregate(Path(args.runs), criteria)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    write_report(results, out_dir)
    print(json.dumps({"summary": results["summary"], "criteria": results["criteria"]}, indent=2))


if __name__ == "__main__":
    main()
