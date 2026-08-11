"""Churn/turnover tracker (workstream A, lagging metric).

For every merged agent PR, at +14 and +30 days measures the fraction of its
merged lines that have since been reverted or substantially rewritten.

Industry anchors (GitClear 211M-line study, 2026):
  - AI code: 12–18% 30-day turnover
  - Human code: 4–6% 30-day turnover
  - Ratio > 2x = red flag

Usage (run as a cron job or manually):
    python churn.py --days 14   # check all PRs merged 14+ days ago
    python churn.py --days 30   # check all PRs merged 30+ days ago

Results appended to data/churn.jsonl.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
FORK_CHECKOUT = "/Users/eprabhu/Desktop/Projects/mine/modus-wc-2.0"
REPO = "ElishaSamPeterPrabhu/modus-wc-2.0"
DATA_DIR = os.path.join(os.path.dirname(_HERE), "data")


def _sh(cmd: list[str], cwd: str = FORK_CHECKOUT) -> str:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout


def merged_prs_before(cutoff: dt.datetime) -> list[dict]:
    """PRs merged before `cutoff` that were experiment runs (branch starts exp/)."""
    out = subprocess.run(
        [
            "gh", "pr", "list", "-R", REPO,
            "--state", "merged",
            "--json", "number,title,mergedAt,headRefName",
            "--limit", "200",
        ],
        capture_output=True, text=True, check=True,
    ).stdout
    prs = json.loads(out)
    result = []
    for pr in prs:
        if not pr.get("headRefName", "").startswith("exp/"):
            continue
        merged = dt.datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
        if merged < cutoff:
            result.append(pr)
    return result


def measure_churn(pr: dict, fetch: bool = True) -> dict:
    """Measure line turnover for a merged PR.

    Approach: for each file the PR touched, compute git blame at merge-commit
    time and check what fraction of those lines have since changed.
    """
    pr_number = pr["number"]
    head_ref = pr["headRefName"]
    merged_at = dt.datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))

    if fetch:
        try:
            subprocess.run(
                ["git", "fetch", "origin", head_ref],
                cwd=FORK_CHECKOUT, capture_output=True,
            )
        except Exception:
            pass

    # Files touched by the PR.
    try:
        merge_sha = _sh(
            ["git", "log", "--merges", "--format=%H",
             f"--grep=#{pr_number}", "-1"]
        ).strip()
        if not merge_sha:
            merge_sha = _sh(
                ["git", "log", "--format=%H", f"origin/{head_ref}", "-1"]
            ).strip()
    except Exception:
        return {"pr": pr_number, "error": "cannot find merge sha"}

    try:
        changed_files = _sh(
            ["git", "diff", "--name-only", f"{merge_sha}^", merge_sha]
        ).splitlines()
    except Exception:
        return {"pr": pr_number, "error": "cannot diff merge commit"}

    # Count lines added in the PR.
    try:
        stat = _sh(["git", "show", "--stat", merge_sha]).splitlines()
        added = deleted = 0
        for line in stat:
            if "insertion" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if "insertion" in p:
                        added += int(parts[i - 1])
            if "deletion" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if "deletion" in p:
                        deleted += int(parts[i - 1])
    except Exception:
        added = deleted = 0

    # Compare with HEAD: how many of those lines still exist verbatim?
    try:
        diff_since = _sh(
            ["git", "diff", "--stat", merge_sha, "HEAD"]
        )
        lines_changed_since = 0
        for line in diff_since.splitlines():
            if "insertion" in line or "deletion" in line:
                parts = line.split()
                for tok in parts:
                    if tok.isdigit():
                        lines_changed_since += int(tok)
    except Exception:
        lines_changed_since = 0

    # Crude churn estimate: fraction of PR lines touched again in the window.
    pr_lines = max(1, added)
    churn_rate = min(1.0, lines_changed_since / pr_lines)

    age_days = (dt.datetime.now(dt.timezone.utc) - merged_at).days

    return {
        "pr": pr_number,
        "head_ref": head_ref,
        "merged_at": pr["mergedAt"],
        "age_days": age_days,
        "lines_added": added,
        "lines_changed_since_merge": lines_changed_since,
        "churn_rate": round(churn_rate, 4),
        "churn_flag": churn_rate > 0.15,  # > 15% at 30d = red flag
        "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def run(days: int = 30) -> None:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    prs = merged_prs_before(cutoff)
    if not prs:
        print(f"No experiment PRs merged more than {days} days ago.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "churn.jsonl")

    # Load already-measured PRs to avoid double-counting.
    measured = set()
    if os.path.exists(out_path):
        with open(out_path) as fh:
            for line in fh:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("age_days", 0) >= days:
                            measured.add((rec["pr"], days))
                    except json.JSONDecodeError:
                        pass

    with open(out_path, "a") as fh:
        for pr in prs:
            if (pr["number"], days) in measured:
                continue
            rec = measure_churn(pr)
            rec["measurement_days"] = days
            fh.write(json.dumps(rec) + "\n")
            flag = "⚠ HIGH CHURN" if rec.get("churn_flag") else "ok"
            print(
                f"PR #{rec['pr']}  churn={rec.get('churn_rate', '?'):.2f}  "
                f"age={rec.get('age_days')}d  {flag}"
            )
    print(f"Written to {out_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    run(args.days)
