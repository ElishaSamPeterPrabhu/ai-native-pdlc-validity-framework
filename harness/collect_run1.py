"""One-shot collector for the 5-issue live run (round 1).

Run this after all 5 issues reach a terminal state (merged / needs-human / closed).
It snapshots GitHub timelines, grading, and telemetry, then writes
analysis/live-run-1.md with the formula vs observed comparison.

Usage:
    python harness/collect_run1.py --wait   # poll until all 5 are terminal
    python harness/collect_run1.py          # snapshot whatever is terminal now
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "theory"))
import formula as F  # noqa: E402

REPO = "ElishaSamPeterPrabhu/modus-wc-2.0"
FORK_CHECKOUT = "/Users/eprabhu/Desktop/Projects/mine/modus-wc-2.0"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RUNS_DIR = os.path.join(DATA_DIR, "live-run-1")

# The 5 experiment issues
ISSUES = {
    26: {"task": "high-select-event",   "stratum": "high",   "qa_route": "qa-full",  "upstream": 677},
    27: {"task": "low-button-xs",        "stratum": "low",    "qa_route": "qa-skip",  "upstream": 800},
    28: {"task": "med-checkbox-switch",  "stratum": "medium", "qa_route": "qa-full",  "upstream": 861},
    29: {"task": "low-sidenav-style",    "stratum": "low",    "qa_route": "qa-skip",  "upstream": 987},
    30: {"task": "med-menu-end-icon",    "stratum": "medium", "qa_route": "qa-full",  "upstream": 1128},
}

# Factor activity for round 1 (current setup, all on except review bot + human_alignment)
FACTOR_STATE_ROUND1 = {
    "spec_refinement": False,  # issues were pre-written, scaffolding not used
    "agentic_qa": True,
    "fix_loop": True,
    "ci_gate": True,
    "mcp_context": True,   # mcp/ is in the repo
    "rules_context": True,  # .cursor/rules/ is in the repo
    "checkpointing": True,  # instruction added to Dev Agent
    "review_bot": False,
    "human_alignment": False,
}


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout.strip()


def terminal_state(issue_number: int) -> str:
    prs = json.loads(gh(
        "pr", "list", "-R", REPO, "--state", "all",
        "--search", f"in:title [#{issue_number}]",
        "--json", "number,state,mergedAt,headRefName,labels",
        "--limit", "5",
    ))
    # Also try searching by issue number in body
    if not prs:
        prs = json.loads(gh(
            "pr", "list", "-R", REPO, "--state", "all",
            "--search", f"exp/{issue_number}-",
            "--json", "number,state,mergedAt,headRefName,labels",
            "--limit", "5",
        ))
    for pr in prs:
        if pr.get("mergedAt"):
            return "merged"
        labels = {l["name"] for l in pr.get("labels", [])}
        if "needs-human" in labels:
            return "needs-human"
        if pr["state"] == "CLOSED":
            return "closed"
        return "running"
    return "no-pr"


def snapshot_issue(issue_number: int, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)

    # Issue timeline
    timeline_raw = gh("api", f"repos/{REPO}/issues/{issue_number}/timeline", "--paginate")
    timeline = json.loads(timeline_raw)
    with open(os.path.join(out_dir, "issue-timeline.json"), "w") as fh:
        json.dump(timeline, fh, indent=2)

    # Find the PR for this issue
    prs = json.loads(gh(
        "pr", "list", "-R", REPO, "--state", "all",
        "--search", f"exp/{issue_number}-",
        "--json", "number,state,mergedAt,headRefName,labels,createdAt,body",
        "--limit", "3",
    ))
    if not prs:
        return {"issue": issue_number, "pr": None, "error": "no PR found"}

    pr = prs[0]
    with open(os.path.join(out_dir, "pr.json"), "w") as fh:
        json.dump(pr, fh, indent=2)

    pr_number = pr["number"]
    # PR timeline (labels, comments)
    pr_timeline = json.loads(gh("api", f"repos/{REPO}/issues/{pr_number}/timeline", "--paginate"))
    with open(os.path.join(out_dir, "pr-timeline.json"), "w") as fh:
        json.dump(pr_timeline, fh, indent=2)

    # PR commits
    pr_commits = json.loads(gh("api", f"repos/{REPO}/pulls/{pr_number}/commits", "--paginate"))
    with open(os.path.join(out_dir, "pr-commits.json"), "w") as fh:
        json.dump(pr_commits, fh, indent=2)

    return {
        "issue": issue_number,
        "pr_number": pr_number,
        "pr_state": pr["state"],
        "merged_at": pr.get("mergedAt"),
        "head_ref": pr.get("headRefName"),
        "labels": [l["name"] for l in pr.get("labels", [])],
        "n_commits": len(pr_commits),
    }


def extract_telemetry(snapshot: dict, pr_timeline: list, pr_commits: list) -> dict:
    """Extract pipeline telemetry from the GitHub event timelines."""
    events: dict[str, str] = {}
    for ev in pr_timeline:
        if ev.get("event") == "labeled":
            name = ev["label"]["name"]
            if name in ("qa-skip", "qa-full", "qa-failed", "needs-human"):
                events.setdefault(name + "_at", ev["created_at"])
        if ev.get("event") == "commented":
            body = (ev.get("body") or "")
            for key, phrase in [
                ("qa_passed_at", "QA PASSED"),
                ("qa_skipped_at", "QA SKIPPED"),
                ("qa_failed_at", "QA FAILED"),
                ("fix_started_at", "fixing"),
            ]:
                if phrase.upper() in body.upper():
                    events.setdefault(key, ev["created_at"])

    # Fix iterations: count qa-failed labels added to PR
    fix_iterations = sum(
        1 for ev in pr_timeline
        if ev.get("event") == "labeled" and ev["label"]["name"] == "qa-failed"
    )

    # Diff stats from commits
    n_commits = len(pr_commits)
    head_ref = snapshot.get("head_ref", "")

    delta_loc = 0
    files_touched = 0
    if head_ref and pr_commits:
        try:
            diff_stat = subprocess.run(
                ["git", "diff", "--shortstat", f"origin/main", f"origin/{head_ref}"],
                cwd=FORK_CHECKOUT, capture_output=True, text=True,
            ).stdout
            for part in diff_stat.split(","):
                p = part.strip()
                if "insertion" in p or "deletion" in p:
                    delta_loc += int(p.split()[0])
                elif "file" in p:
                    files_touched = int(p.split()[0])
        except Exception:
            pass

    return {
        "events": events,
        "fix_iterations": fix_iterations,
        "n_commits": n_commits,
        "delta_loc": delta_loc,
        "files_touched": files_touched,
        "terminal_state": snapshot.get("pr_state", "unknown"),
        "merged": bool(snapshot.get("merged_at")),
        "labels_on_pr": snapshot.get("labels", []),
    }


def predicted_equilibrium(telemetry: dict, qa_route: str) -> dict:
    """Compute formula v0 predicted V* for this run."""
    # Build activities
    acts = dict(FACTOR_STATE_ROUND1)
    # spec_refinement was off (raw issues seeded directly)
    if qa_route == "qa-skip":
        # If the PR actually got qa-skipped, agentic_qa ran but stopped early
        pass  # still True — the QA agent ran and made a decision

    recovery = F.recovery_rate(acts)

    # Decay proxy inputs
    n_files = max(1, telemetry.get("files_touched", 1))
    delta_loc = max(0, telemetry.get("delta_loc", 0))
    # Blast radius heuristic: files/60 (60 components in repo)
    blast = F.blast_radius_proxy(n_files, 60)
    # Spec ambiguity: raw spec (no scaffolding) = high ambiguity
    spec_ambiguity = 0.55 if not FACTOR_STATE_ROUND1["spec_refinement"] else 0.20
    opacity = F.opacity_proxy(delta_loc, 0, n_files)
    entropy = 0.15  # baseline — no real token data yet

    inputs = F.DecayInputs(entropy=entropy, opacity=opacity,
                           blast_radius=blast, spec_ambiguity=spec_ambiguity)
    decay = F.decay_rate(inputs, form=F.DecayForm.HYBRID)
    v_star = F.equilibrium_validity(recovery, decay)

    return {
        "recovery_R": round(recovery, 4),
        "decay_D": round(decay, 4),
        "predicted_V_star": round(v_star, 4),
        "opacity": round(opacity, 4),
        "blast_radius": round(blast, 4),
        "spec_ambiguity": round(spec_ambiguity, 4),
    }


def write_report(all_data: list[dict]) -> str:
    """Write analysis/live-run-1.md."""
    lines = [
        "# Live Run 1: Formula vs Observed — 5 Issues (Round 1 Baseline)",
        "",
        f"Collected: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "Setup: baseline pipeline (current Cursor automations, no Tier-1 QA hardening)",
        f"Formula version: {F.FORMULA_VERSION} "
        f"(placeholder weights; decay form = {F.DEFAULT_DECAY_FORM_NAME}; "
        f"evidence = {F.EVIDENCE_STATUS})",
        "",
        "## Summary table",
        "",
        "| Issue | Stratum | Expected QA | Actual terminal | Fix iters | Commits | "
        "Predicted V* | Passed? | Formula correct? |",
        "|-------|---------|-------------|-----------------|-----------|---------|"
        "-------------|---------|-----------------|",
    ]

    for d in all_data:
        issue_meta = ISSUES.get(d["issue_number"], {})
        pred = d.get("predicted", {})
        tel = d.get("telemetry", {})
        merged = tel.get("merged", False)
        actual = tel.get("terminal_state", "?")
        fix_it = tel.get("fix_iterations", 0)
        commits = tel.get("n_commits", 0)
        v_star = pred.get("predicted_V_star", "?")
        qa_expected = issue_meta.get("qa_route", "?")
        labels = tel.get("labels_on_pr", [])
        actual_qa = ("qa-skip" if "qa-skip" in labels else
                     "qa-full" if "qa-full" in labels else "?")
        formula_correct = "✓" if merged == (float(v_star) > 0.5 if v_star != "?" else False) else "✗"

        lines.append(
            f"| #{d['issue_number']} | {issue_meta.get('stratum','?')} "
            f"| {qa_expected} | {actual}/{actual_qa} | {fix_it} | {commits} "
            f"| {v_star} | {'✓' if merged else '✗'} | {formula_correct} |"
        )

    lines += [
        "",
        "## Per-run details",
        "",
    ]

    for d in all_data:
        issue_meta = ISSUES.get(d["issue_number"], {})
        pred = d.get("predicted", {})
        tel = d.get("telemetry", {})
        lines += [
            f"### Issue #{d['issue_number']}: {issue_meta.get('task','?')} [{issue_meta.get('stratum','?')}]",
            "",
            f"- PR: #{d.get('pr_number', 'none')}",
            f"- Terminal state: {tel.get('terminal_state','?')} | merged: {tel.get('merged',False)}",
            f"- Fix iterations: {tel.get('fix_iterations', 0)} | Commits: {tel.get('n_commits', 0)}",
            f"- diff: +/-{tel.get('delta_loc',0)} LOC across {tel.get('files_touched',0)} files",
            f"- Labels on PR: {tel.get('labels_on_pr', [])}",
            f"- Pipeline events: {json.dumps(tel.get('events', {}), indent=4)}",
            "",
            "**Formula prediction (v0):**",
            f"- Recovery R = {pred.get('recovery_R','?')} (all factors on except spec_refinement, review_bot)",
            f"- Decay D = {pred.get('decay_D','?')} (opacity={pred.get('opacity','?')}, blast={pred.get('blast_radius','?')}, σ={pred.get('spec_ambiguity','?')})",
            f"- Predicted V* = {pred.get('predicted_V_star','?')}",
            f"- Trust gate verdict: {F.trust_verdict(pred.get('predicted_V_star', 0)).value}",
            "",
            "---",
            "",
        ]

    lines += [
        "## Formula ordering predictions vs observed",
        "",
        "The v0 formula predicted (from Phase-B simulation):",
        "1. High-stratum runs (complex, high blast radius) → more fix iterations",
        "2. qa-skip runs → faster terminal state, fewer iterations",
        "3. Mislabeled qa-skip (if any) → QA reversal, increases fix iterations",
        "",
        "These are checked above. Violations (formula_correct = ✗) reveal where",
        "v0 weights need adjustment — the primary signal for v1 calibration.",
        "",
        "## Next steps",
        "",
        "1. Trigger round 2 after Tier-1 QA hardening (Playwright + blocking a11y + visual regression)",
        "2. Compare fix iteration counts and merge rates between round 1 and round 2",
        "3. The ΔV* (round2 − round1) at equilibrium = measured value of Tier-1 QA stage",
        "4. Run `python harness/churn.py --days 14` in 2 weeks to check turnover",
    ]

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "live-run-1.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    return path


def main(wait: bool = False) -> None:
    os.makedirs(RUNS_DIR, exist_ok=True)
    all_data = []

    if wait:
        print("Polling until all 5 issues reach terminal state (Ctrl-C to stop)...")

    for issue_number, meta in sorted(ISSUES.items()):
        print(f"\nIssue #{issue_number} ({meta['task']})...")
        state = terminal_state(issue_number)
        if wait and state == "running":
            print(f"  still running, polling...")
            deadline = time.time() + 90 * 60  # max 90 min wait
            while state in ("running", "no-pr") and time.time() < deadline:
                time.sleep(60)
                state = terminal_state(issue_number)
        print(f"  state: {state}")

        out_dir = os.path.join(RUNS_DIR, f"issue-{issue_number}")
        snap = snapshot_issue(issue_number, out_dir)

        pr_timeline = []
        pr_commits = []
        pt_path = os.path.join(out_dir, "pr-timeline.json")
        pc_path = os.path.join(out_dir, "pr-commits.json")
        if os.path.exists(pt_path):
            pr_timeline = json.load(open(pt_path))
        if os.path.exists(pc_path):
            pr_commits = json.load(open(pc_path))

        tel = extract_telemetry(snap, pr_timeline, pr_commits)
        pred = predicted_equilibrium(tel, meta["qa_route"])

        record = {
            "issue_number": issue_number,
            "pr_number": snap.get("pr_number"),
            "telemetry": tel,
            "predicted": pred,
            "factor_state": FACTOR_STATE_ROUND1,
        }
        with open(os.path.join(out_dir, "analysis.json"), "w") as fh:
            json.dump(record, fh, indent=2)
        all_data.append(record)

        # Update metrics.jsonl for the dashboard
        metrics_record = {
            "run_tag": f"round1/{meta['task']}/r1",
            "arm": "round1-baseline",
            "task": meta["task"],
            "stratum": meta["stratum"],
            "repeat": 1,
            "factor_state": FACTOR_STATE_ROUND1,
            "model": "composer-2.5",
            "terminal_state": tel["terminal_state"],
            "final_v_obs": 1.0 if tel.get("merged") else 0.0,
            "final_pass": tel.get("merged", False),
            "fix_iterations": tel.get("fix_iterations", 0),
            "fix_budget_remaining": 1.0 - tel.get("fix_iterations", 0) / 3.0,
            "stage_transitions": tel.get("events", {}),
            "checkpoints": [{
                "sha": "run1",
                "t_hours": 1.0,
                "v_obs": 1.0 if tel.get("merged") else 0.0,
                "delta_loc": tel.get("delta_loc", 0),
                "files_touched": tel.get("files_touched", 0),
                "opacity": pred.get("opacity", 0.0),
                "blast_radius": pred.get("blast_radius", 0.0),
            }],
        }
        metrics_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metrics.jsonl"
        )
        with open(metrics_path, "a") as fh:
            fh.write(json.dumps(metrics_record) + "\n")

    path = write_report(all_data)
    print(f"\nReport written: {path}")
    print(f"Dashboard: python dashboard/server.py --port 8600")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    main(wait=args.wait)
