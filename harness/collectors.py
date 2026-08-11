"""Telemetry collectors: turn a run's artifacts into the formula's inputs.

Input: the artifacts directory written by driver.py (issue/PR timelines, commits)
plus a local checkout of the fork for diff/graph analysis and verifier grading.

Output: one metrics record per run (data/metrics.jsonl) with
- per-commit checkpoints: t, V_obs, entropy/opacity/blast-radius proxies, activities
- run-level: stage transition times, fix iterations, pass/fail, diff stats

The proxy math lives in theory/formula.py; this module only extracts raw telemetry
and calls those functions.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "theory"))
sys.path.insert(0, _HERE)

import formula as F  # noqa: E402
from factors.registry import FACTORS  # noqa: E402

FORK_CHECKOUT = "/Users/eprabhu/Desktop/Projects/mine/modus-wc-2.0"
TASKS_DIR = os.path.join(_HERE, "tasks")
CONTEXT_WINDOW_TOKENS = 200_000  # Composer 2.5 default window; recorded, not assumed


def sh(cmd: list[str], cwd: str = FORK_CHECKOUT) -> str:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout


@dataclass
class CommitPoint:
    sha: str
    t_hours: float
    v_obs: float | None  # None until graded
    delta_loc: int
    files_touched: int
    opacity: float
    blast_radius: float


def load_artifacts(run_dir: str) -> dict:
    out = {}
    for name in ("run", "pr", "pr-commits", "issue-timeline", "pr-timeline"):
        path = os.path.join(run_dir, f"{name}.json")
        if os.path.exists(path):
            with open(path) as fh:
                out[name.replace("-", "_")] = json.load(fh)
    return out


# ---------------------------------------------------------------------------
# Stage transitions from GitHub event timelines (the label-handoff bus)
# ---------------------------------------------------------------------------

def stage_transitions(artifacts: dict) -> dict[str, str]:
    """Timestamped pipeline handoffs from label/comment events."""
    events: dict[str, str] = {}
    for ev in artifacts.get("issue_timeline", []):
        if ev.get("event") == "labeled" and ev["label"]["name"] == "approved":
            events.setdefault("approved_at", ev["created_at"])
        if (
            ev.get("event") == "commented"
            and "/approve" in (ev.get("body") or "")
        ):
            events.setdefault("dev_triggered_at", ev["created_at"])
    for ev in artifacts.get("pr_timeline", []):
        if ev.get("event") == "labeled" and ev["label"]["name"] == "qa-failed":
            events.setdefault("first_qa_failed_at", ev["created_at"])
            events["last_qa_failed_at"] = ev["created_at"]
        if ev.get("event") == "labeled" and ev["label"]["name"] == "needs-human":
            events["needs_human_at"] = ev["created_at"]
    if artifacts.get("pr"):
        events["pr_opened_at"] = artifacts["pr"].get("createdAt")
        if artifacts["pr"].get("mergedAt"):
            events["merged_at"] = artifacts["pr"]["mergedAt"]
    return events


def fix_iterations(artifacts: dict) -> int:
    return sum(
        1
        for ev in artifacts.get("pr_timeline", [])
        if ev.get("event") == "labeled" and ev["label"]["name"] == "qa-failed"
    )


# ---------------------------------------------------------------------------
# Per-commit structural telemetry (diff stats, dependency reach)
# ---------------------------------------------------------------------------

def dependency_reach(changed_files: list[str]) -> float:
    """Blast radius via reverse dependencies (madge over src/).

    Cached per collector invocation; falls back to a component-count heuristic if
    madge is unavailable.
    """
    try:
        graph = json.loads(
            sh(["npx", "--yes", "madge", "--extensions", "ts,tsx", "--json", "src"])
        )
    except Exception:
        comps = {f.split("/")[2] for f in changed_files if f.startswith("src/components/")}
        return min(1.0, len(comps) / 20.0)
    # reverse edges: file -> dependents
    dependents: dict[str, set] = {}
    for src_file, deps in graph.items():
        for d in deps:
            dependents.setdefault(d, set()).add(src_file)

    def reach(node: str, seen: set) -> None:
        for parent in dependents.get(node, ()):  # transitive closure upward
            if parent not in seen:
                seen.add(parent)
                reach(parent, seen)

    affected: set = set()
    for f in changed_files:
        rel = os.path.relpath(f, "src") if f.startswith("src/") else f
        reach(rel, affected)
        affected.add(rel)
    return F.blast_radius_proxy(len(affected), max(1, len(graph)))


def commit_points(artifacts: dict, base_branch: str) -> list[CommitPoint]:
    """Structural telemetry at each PR commit (fetches the PR branch)."""
    commits = artifacts.get("pr_commits", [])
    if not commits:
        return []
    head_ref = artifacts["pr"]["headRefName"]
    sh(["git", "fetch", "origin", head_ref, base_branch])
    t0 = None
    points: list[CommitPoint] = []
    for c in commits:
        sha = c["sha"]
        ts = c["commit"]["committer"]["date"]
        import datetime as dt

        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        t0 = t0 or t
        stat = sh(["git", "diff", "--shortstat", f"origin/{base_branch}", sha])
        files = sh(
            ["git", "diff", "--name-only", f"origin/{base_branch}", sha]
        ).splitlines()
        ins = del_ = nf = 0
        for part in stat.split(","):
            part = part.strip()
            if "insertion" in part:
                ins = int(part.split()[0])
            elif "deletion" in part:
                del_ = int(part.split()[0])
            elif "file" in part:
                nf = int(part.split()[0])
        delta_loc = ins + del_
        points.append(
            CommitPoint(
                sha=sha,
                t_hours=(t - t0).total_seconds() / 3600.0,
                v_obs=None,
                delta_loc=delta_loc,
                files_touched=nf,
                opacity=F.opacity_proxy(delta_loc, 0.0, nf),
                blast_radius=dependency_reach(files),
            )
        )
    return points


# ---------------------------------------------------------------------------
# Verifier grading: V_obs at every commit
# ---------------------------------------------------------------------------

def grade_commits(task_id: str, points: list[CommitPoint]) -> None:
    """Copy the task verifier into the checkout at each commit and run it."""
    with open(os.path.join(TASKS_DIR, f"{task_id}.json")) as fh:
        task = json.load(fh)
    vdir = os.path.join(TASKS_DIR, task["verifier"]["dir"])
    spec_files = [f for f in os.listdir(vdir) if f.endswith(".spec.ts")]
    if not spec_files:
        return
    comp = task["components"][0]
    target_dir = os.path.join(FORK_CHECKOUT, "src", "components", comp, "__verifier__")

    for point in points:
        sh(["git", "checkout", "-q", point.sha])
        os.makedirs(target_dir, exist_ok=True)
        for f in spec_files:
            sh(["cp", os.path.join(vdir, f), target_dir], cwd="/")
        # regenerate build artifacts the specs need
        for script in ("tailwind:build", "embed:css", "embed:component-css"):
            subprocess.run(["npm", "run", "-s", script], cwd=FORK_CHECKOUT,
                           capture_output=True)
        result = subprocess.run(
            ["npx", "stencil", "test", "--spec", "--json",
             "--outputFile", "/tmp/verifier-grade.json"],
            cwd=FORK_CHECKOUT, capture_output=True, text=True,
        )
        passed = total = 0
        try:
            with open("/tmp/verifier-grade.json") as fh:
                data = json.load(fh)
            for tr in data["testResults"]:
                if "__verifier__" in tr["name"]:
                    for a in tr["assertionResults"]:
                        total += 1
                        passed += a["status"] == "passed"
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
        point.v_obs = (passed / total) if total else None
        sh(["rm", "-rf", target_dir], cwd="/")
    sh(["git", "checkout", "-q", "experiment-base"])


# ---------------------------------------------------------------------------
# Entry point: one run directory -> one metrics record
# ---------------------------------------------------------------------------

def collect(run_dir: str, grade: bool = True) -> dict:
    artifacts = load_artifacts(run_dir)
    run = artifacts["run"]
    points = commit_points(artifacts, run["base_branch"])
    if grade and points:
        grade_commits(run["task"], points)

    transitions = stage_transitions(artifacts)
    iterations = fix_iterations(artifacts)
    cap = FACTORS["fix_loop"].options.get("cap", 3)

    record = {
        **{k: run[k] for k in ("run_tag", "arm", "task", "stratum", "repeat",
                                "factor_state", "model", "terminal_state")},
        "stage_transitions": transitions,
        "fix_iterations": iterations,
        "fix_budget_remaining": max(0.0, 1.0 - iterations / cap),
        "checkpoints": [asdict(p) for p in points],
        "final_v_obs": points[-1].v_obs if points else None,
        "final_pass": bool(points and points[-1].v_obs == 1.0),
    }
    out = os.path.join(run_dir, "metrics.json")
    with open(out, "w") as fh:
        json.dump(record, fh, indent=2)
    return record


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs="+")
    parser.add_argument("--no-grade", action="store_true")
    args = parser.parse_args()
    data_dir = os.path.join(os.path.dirname(_HERE), "data")
    metrics_path = os.path.join(data_dir, "metrics.jsonl")
    for run_dir in args.run_dirs:
        record = collect(run_dir, grade=not args.no_grade)
        with open(metrics_path, "a") as fh:
            fh.write(json.dumps(record) + "\n")
        print(record["run_tag"], "final V_obs:", record["final_v_obs"])
