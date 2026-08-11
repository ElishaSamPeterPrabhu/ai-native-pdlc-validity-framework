"""Quality vector collector (workstream A).

For each merged agent PR, computes a quality vector Q containing leading
metrics: cognitive complexity, duplicated-block density, and code-smell count.
Q feeds the trust gate: a PR can pass its verifier but be downgraded to
'review-carefully' based on sustained quality regression.

Two approaches, selected automatically:
  1. SonarCloud (preferred): reads the scan already configured in the repo's
     sonar-project.properties; requires SONAR_TOKEN env var.
  2. Local fallback (lizard + jscpd): no account needed, runs locally.

Usage:
    python quality.py --pr 5 --repo ElishaSamPeterPrabhu/modus-wc-2.0 --base main
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
FORK_CHECKOUT = "/Users/eprabhu/Desktop/Projects/mine/modus-wc-2.0"

sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "theory"))
import formula as F  # noqa: E402


@dataclass
class QualityVector:
    """Leading quality metrics for one PR."""

    pr_number: int
    # Cognitive complexity delta (PR branch vs base); > 0 = added complexity.
    delta_cognitive_complexity: float
    # Duplicated-block density delta (fraction of new lines that are duplicates).
    delta_dup_density: float
    # Code smells introduced (positive = new smells).
    delta_code_smells: int
    # Method: "sonarcloud" or "local"
    method: str

    def as_opacity_addon(self) -> float:
        """Map quality deltas to an additional opacity penalty in [0, 0.25].

        This caps at 0.25 so quality alone cannot exceed the main opacity proxy.
        """
        cc_penalty = min(1.0, max(0.0, self.delta_cognitive_complexity / 50.0))
        dup_penalty = min(1.0, max(0.0, self.delta_dup_density / 0.30))
        smells_penalty = min(1.0, max(0.0, self.delta_code_smells / 20.0))
        raw = (cc_penalty + dup_penalty + smells_penalty) / 3.0
        return round(raw * 0.25, 4)


def _sh(cmd: list[str], cwd: str = FORK_CHECKOUT) -> tuple[str, int]:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return res.stdout + res.stderr, res.returncode


def _fetch_sonarcloud(pr_number: int, repo: str) -> QualityVector | None:
    """Try to fetch the SonarCloud analysis for this PR."""
    token = os.environ.get("SONAR_TOKEN")
    if not token:
        return None
    # Derive the SonarCloud project key from sonar-project.properties.
    props_path = os.path.join(FORK_CHECKOUT, "sonar-project.properties")
    if not os.path.exists(props_path):
        return None
    key = None
    with open(props_path) as fh:
        for line in fh:
            if line.startswith("sonar.projectKey"):
                key = line.split("=", 1)[1].strip()
    if not key:
        return None
    import urllib.request
    # Pull the measures for the PR branch
    url = (
        f"https://sonarcloud.io/api/measures/component"
        f"?component={key}"
        f"&pullRequest={pr_number}"
        f"&metricKeys=cognitive_complexity,duplicated_lines_density,code_smells"
    )
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception:
        return None
    measures = {m["metric"]: float(m["value"]) for m in data["component"]["measures"]}
    return QualityVector(
        pr_number=pr_number,
        delta_cognitive_complexity=measures.get("cognitive_complexity", 0.0),
        delta_dup_density=measures.get("duplicated_lines_density", 0.0) / 100.0,
        delta_code_smells=int(measures.get("code_smells", 0)),
        method="sonarcloud",
    )


def _local_quality(pr_number: int, base_branch: str, head_ref: str) -> QualityVector:
    """Compute quality metrics locally using lizard (CC) and jscpd (duplication)."""
    # Fetch the PR branch.
    _sh(["git", "fetch", "origin", head_ref, base_branch])

    changed_ts = _sh(
        ["git", "diff", "--name-only", f"origin/{base_branch}", f"origin/{head_ref}"],
    )[0].splitlines()
    changed_ts = [f for f in changed_ts if f.endswith((".ts", ".tsx"))]

    cc_delta = 0.0
    if changed_ts:
        out, _ = _sh(
            ["python3", "-m", "lizard", "--CCN", "1", "--json", *changed_ts]
        )
        try:
            data = json.loads(out)
            for fn in data.get("function_list", []):
                cc_delta += fn.get("cyclomatic_complexity", 0)
        except (json.JSONDecodeError, KeyError):
            pass

    dup_density = 0.0
    jscpd_out, _ = _sh(
        [
            "npx", "--yes", "jscpd",
            "--min-lines", "5", "--reporters", "json",
            "--output", "/tmp/jscpd-out",
            *changed_ts,
        ]
    )
    jscpd_json = "/tmp/jscpd-out/jscpd-report.json"
    if os.path.exists(jscpd_json):
        try:
            with open(jscpd_json) as fh:
                jd = json.load(fh)
            pct = jd.get("statistics", {}).get("total", {}).get("percentage", 0)
            dup_density = float(pct) / 100.0
        except (json.JSONDecodeError, KeyError):
            pass

    return QualityVector(
        pr_number=pr_number,
        delta_cognitive_complexity=cc_delta,
        delta_dup_density=dup_density,
        delta_code_smells=0,  # not available locally without Sonar
        method="local",
    )


def collect(pr_number: int, repo: str, base_branch: str = "main") -> QualityVector:
    """Compute quality vector for a PR, trying SonarCloud then local fallback."""
    # Determine the PR's head ref from the GitHub API.
    out = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "-R", repo, "--json", "headRefName"],
        capture_output=True, text=True,
    )
    head_ref = json.loads(out.stdout).get("headRefName", "")

    q = _fetch_sonarcloud(pr_number, repo)
    if q is None:
        q = _local_quality(pr_number, base_branch, head_ref)
    return q


def verdict_with_quality(
    v_delivered: float,
    q: QualityVector,
) -> F.TrustVerdict:
    """Apply the quality penalty to V_delivered before calling the trust gate."""
    adjusted = v_delivered * (1.0 - q.as_opacity_addon())
    return F.trust_verdict(adjusted)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--repo", default="ElishaSamPeterPrabhu/modus-wc-2.0")
    parser.add_argument("--base", default="main")
    args = parser.parse_args()

    q = collect(args.pr, args.repo, args.base)
    print(json.dumps({
        "pr": q.pr_number,
        "method": q.method,
        "delta_cognitive_complexity": q.delta_cognitive_complexity,
        "delta_dup_density": q.delta_dup_density,
        "delta_code_smells": q.delta_code_smells,
        "opacity_addon": q.as_opacity_addon(),
    }, indent=2))


if __name__ == "__main__":
    main()
