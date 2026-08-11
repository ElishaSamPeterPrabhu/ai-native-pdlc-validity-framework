"""Round 2 setup: merge Tier-1 hardening and re-seed the 5 issues.

Run this after round 1 is complete and the Tier-1 PR (#32) is reviewed.

Steps:
1. Merge tier1-qa-hardening PR into main on the fork
2. Re-create the 5 issues on the fork (new issue numbers) with [Round 2] prefix
3. The same /approve trigger + pipeline runs on the hardened setup
4. collect_round2.py then diffs round-1 vs round-2 outcomes

Usage:
    python harness/setup_round2.py --dry-run   # see what would happen
    python harness/setup_round2.py             # execute
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

REPO = "ElishaSamPeterPrabhu/modus-wc-2.0"
UPSTREAM = "trimble-oss/modus-wc-2.0"
TIER1_PR = 32  # the PR number for Tier-1 hardening

# Same 5 issues, same round-1 fork numbers
ROUND1_ISSUES = {27: "low", 29: "low", 30: "medium", 28: "medium", 26: "high"}


def gh(*args: str, dry_run: bool = False) -> str:
    if dry_run:
        print(f"  [dry-run] gh {' '.join(args)}")
        return ""
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout.strip()


def main(dry_run: bool = False) -> None:
    print("=== Round 2 Setup ===")
    print()

    # 1. Check Tier-1 PR status
    pr_info = json.loads(
        subprocess.run(
            ["gh", "pr", "view", str(TIER1_PR), "-R", REPO,
             "--json", "state,mergedAt,title"],
            capture_output=True, text=True,
        ).stdout
    )
    if pr_info.get("mergedAt"):
        print(f"Tier-1 PR #{TIER1_PR} is already merged.")
    else:
        print(f"Tier-1 PR #{TIER1_PR} state: {pr_info.get('state')} — merging now...")
        gh("pr", "merge", str(TIER1_PR), "-R", REPO,
           "--squash", "--admin", dry_run=dry_run)
        print("  merged.")
    print()

    # 2. Re-seed the 5 issues for round 2
    print("Re-seeding 5 issues for round 2:")
    round2_issues = {}
    for fork_num, stratum in sorted(ROUND1_ISSUES.items()):
        # Get the round-1 issue body to re-use
        issue_data = json.loads(
            subprocess.run(
                ["gh", "issue", "view", str(fork_num), "-R", REPO,
                 "--json", "title,body"],
                capture_output=True, text=True,
            ).stdout
        )
        title = issue_data["title"].replace("[Experiment Issue]", "").strip()
        body = issue_data["body"] or ""
        # Add round-2 marker
        new_body = (
            f"**[Round 2 — Hardened Setup]** Replay of fork #{fork_num}.\n"
            f"Tier-1 QA (Playwright, visual regression, blocking a11y) is now active.\n\n"
            + body
        )
        new_title = f"[Round 2] {title}"
        labels = [f"task:{stratum}", "experiment-run"]
        url = gh(
            "issue", "create", "-R", REPO,
            "--title", new_title,
            "--body", new_body,
            "--label", ",".join(labels),
            dry_run=dry_run,
        )
        if not dry_run:
            new_num = int(url.rstrip("/").rsplit("/", 1)[-1])
            round2_issues[fork_num] = new_num
            print(f"  #{fork_num} → round-2 #{new_num}  [{stratum}]  {url}")
        else:
            print(f"  would re-seed #{fork_num} [{stratum}]")
    print()

    if not dry_run and round2_issues:
        print("Round 2 issue URLs (comment /approve on each to start):")
        for r1, r2 in round2_issues.items():
            print(f"  https://github.com/{REPO}/issues/{r2}  (was #{r1})")
        # Save mapping for collect_round2
        mapping_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "round2-issue-mapping.json",
        )
        os.makedirs(os.path.dirname(mapping_path), exist_ok=True)
        with open(mapping_path, "w") as fh:
            json.dump({"round1_to_round2": round2_issues}, fh, indent=2)
        print(f"\nMapping saved: {mapping_path}")

    print()
    print("After running /approve on each round-2 issue, use:")
    print("  python harness/collect_run1.py  # (with ROUND=2 env var or adapt)")
    print("to collect telemetry and generate analysis/live-run-2.md.")
    print()
    print("The before/after delta is:")
    print("  ΔV* = round2_merge_rate - round1_merge_rate")
    print("  Δpass@k = round2_pass^k - round1_pass^k")
    print("  This is the measured value of the Tier-1 QA stage hardening.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
