"""Experiment driver: seeds task issues, fires the pipeline, awaits terminal state.

The existing Cursor Automations pipeline does all the real work; this driver only
talks to GitHub (via the `gh` CLI, which is already authenticated on this machine)
and records artifacts.

One run =
    1. resolve arm -> factor state (harness/factors); verify repo-side toggles
    2. create the task issue (spec_raw or spec_refined variant per arm)
    3. wait for `approved` label (scaffolding path) or self-approve (raw path)
    4. comment `/approve` -> Dev Agent picks it up
    5. poll until terminal: PR merged | needs-human | closed | timeout
    6. snapshot the issue+PR event timeline and PR branch, then clean up
       (close PR unmerged, delete exp/ branch) so the next repeat starts clean

Usage:
    python driver.py --arm baseline --task low-card-hover --repeats 3
    python driver.py --arm no_mcp --task all --repeats 3 --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from factors.registry import ARMS, BASELINE_STATE, arm_config  # noqa: E402

REPO = "ElishaSamPeterPrabhu/modus-wc-2.0"
BASE_BRANCH = "experiment-base"
TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks")
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "runs"
)
POLL_SECONDS = 60
TIMEOUT_MINUTES = 90
CAMPAIGN_MODEL = "composer-2.5"  # fixed for the whole campaign (see plan)


def gh(*args: str, capture: bool = True) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=capture, text=True, check=True
    )
    return result.stdout.strip() if capture else ""


def load_task(task_id: str) -> dict:
    with open(os.path.join(TASKS_DIR, f"{task_id}.json")) as fh:
        return json.load(fh)


def all_task_ids() -> list[str]:
    return sorted(
        f[:-5]
        for f in os.listdir(TASKS_DIR)
        if f.endswith(".json")
    )


def issue_body(task: dict, refined: bool) -> str:
    if not refined:
        return task["spec_raw"]
    spec = task["spec_refined"]
    criteria = "\n".join(f"- [ ] {c}" for c in spec["acceptance_criteria"])
    return (
        f"{spec['description']}\n\n## Acceptance Criteria\n{criteria}\n\n"
        f"## Technical Notes\n{spec.get('technical_notes', '')}\n"
    )


def base_branch_for(state: dict) -> str:
    """Repo-side toggles are encoded as arm-specific base branches."""
    if not state.get("mcp_context", True):
        return f"{BASE_BRANCH}-nomcp"
    if not state.get("rules_context", True):
        return f"{BASE_BRANCH}-norules"
    return BASE_BRANCH


def create_issue(task: dict, state: dict, run_tag: str) -> int:
    refined = bool(state.get("spec_refinement", True))
    spec_label = "spec:refined" if refined else "spec:raw"
    title = (
        task["spec_refined"]["title"] if refined else task["spec_raw"][:80]
    )
    labels = [
        f"task:{task['stratum']}", spec_label, "experiment-run", "approved",
    ]
    url = gh(
        "issue", "create", "-R", REPO,
        "--title", f"[{run_tag}] {title}",
        "--body", issue_body(task, refined)
        + f"\n\n<!-- experiment: task={task['id']} run={run_tag} base={base_branch_for(state)} -->",
        "--label", ",".join(labels),
    )
    return int(url.rstrip("/").rsplit("/", 1)[-1])


def approve(issue_number: int) -> None:
    gh("issue", "comment", str(issue_number), "-R", REPO, "--body", "/approve")


def find_pr_for_issue(issue_number: int) -> dict | None:
    prs = json.loads(
        gh(
            "pr", "list", "-R", REPO, "--state", "all",
            "--search", f"{issue_number} in:title,body",
            "--json", "number,state,mergedAt,headRefName,labels,createdAt",
        )
    )
    return prs[0] if prs else None


def run_state(issue_number: int) -> str:
    """Terminal states: merged | needs-human | closed | running."""
    pr = find_pr_for_issue(issue_number)
    if pr is None:
        return "running"
    labels = {label["name"] for label in pr.get("labels", [])}
    if pr.get("mergedAt"):
        return "merged"
    if "needs-human" in labels:
        return "needs-human"
    if pr["state"] == "CLOSED":
        return "closed"
    return "running"


def snapshot(issue_number: int, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    # GitHub's timeline API lags event creation by a few seconds; retry until
    # events appear (an experiment issue always has at least its label events).
    timeline = "[]"
    for _ in range(5):
        timeline = gh(
            "api", f"repos/{REPO}/issues/{issue_number}/timeline", "--paginate"
        )
        if json.loads(timeline):
            break
        time.sleep(5)
    with open(os.path.join(out_dir, "issue-timeline.json"), "w") as fh:
        fh.write(timeline)
    pr = find_pr_for_issue(issue_number)
    if pr:
        with open(os.path.join(out_dir, "pr.json"), "w") as fh:
            json.dump(pr, fh, indent=2)
        with open(os.path.join(out_dir, "pr-commits.json"), "w") as fh:
            fh.write(
                gh(
                    "api",
                    f"repos/{REPO}/pulls/{pr['number']}/commits",
                    "--paginate",
                )
            )
        with open(os.path.join(out_dir, "pr-timeline.json"), "w") as fh:
            fh.write(
                gh(
                    "api",
                    f"repos/{REPO}/issues/{pr['number']}/timeline",
                    "--paginate",
                )
            )


def cleanup(issue_number: int) -> None:
    pr = find_pr_for_issue(issue_number)
    if pr and pr["state"] == "OPEN" and not pr.get("mergedAt"):
        gh("pr", "close", str(pr["number"]), "-R", REPO,
           "--comment", "Experiment run complete; closing unmerged.")
    if pr and pr.get("headRefName", "").startswith("exp/"):
        try:
            gh("api", "-X", "DELETE",
               f"repos/{REPO}/git/refs/heads/{pr['headRefName']}")
        except subprocess.CalledProcessError:
            pass  # branch already deleted (e.g. on merge)
    gh("issue", "close", str(issue_number), "-R", REPO)


def one_run(task: dict, arm: str, repeat: int, dry_run: bool) -> dict:
    state = arm_config(arm)
    run_tag = f"{arm}/{task['id']}/r{repeat}"
    record: dict = {
        "run_tag": run_tag,
        "arm": arm,
        "task": task["id"],
        "stratum": task["stratum"],
        "repeat": repeat,
        "factor_state": state,
        "base_branch": base_branch_for(state),
        "model": CAMPAIGN_MODEL,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if dry_run:
        record["terminal_state"] = "dry-run"
        return record

    issue = create_issue(task, state, run_tag)
    record["issue"] = issue
    approve(issue)

    deadline = time.time() + TIMEOUT_MINUTES * 60
    terminal = "timeout"
    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        current = run_state(issue)
        if current != "running":
            terminal = current
            break
    record["terminal_state"] = terminal
    record["ended_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

    out_dir = os.path.join(DATA_DIR, run_tag.replace("/", "__"))
    snapshot(issue, out_dir)
    record["artifacts_dir"] = out_dir
    cleanup(issue)
    with open(os.path.join(out_dir, "run.json"), "w") as fh:
        json.dump(record, fh, indent=2)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=sorted(ARMS))
    parser.add_argument("--task", required=True,
                        help="task id or 'all'")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tasks = all_task_ids() if args.task == "all" else [args.task]
    os.makedirs(DATA_DIR, exist_ok=True)
    log_path = os.path.join(DATA_DIR, "runs.jsonl")
    for task_id in tasks:
        task = load_task(task_id)
        for repeat in range(1, args.repeats + 1):
            record = one_run(task, args.arm, repeat, args.dry_run)
            with open(log_path, "a") as fh:
                fh.write(json.dumps(record) + "\n")
            print(f"[{record['terminal_state']:>11}] {record['run_tag']}")


if __name__ == "__main__":
    main()
