"""Validity dashboard server (stdlib only — runs anywhere, no dependencies).

Serves:
    /                    the dashboard SPA (index.html)
    /api/summary         fleet view: runs, arms, pass^k per task, formula version
    /api/run/<run_tag>   one run: V(t) points (observed + formula-predicted),
                         decay/recovery term breakdown, trust-gate verdict

All model math comes from theory/formula.py — changing the formula version changes
what this dashboard shows, with no code changes here.

Usage:  python dashboard/server.py [--port 8600]
Then open http://<host>:8600 from any browser (iPad Safari included).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "theory"))

import formula as F  # noqa: E402

DATA_DIR = os.path.join(_ROOT, "data")
RUNS_DIR = os.path.join(DATA_DIR, "runs")


def load_metrics() -> list[dict]:
    records = []
    path = os.path.join(DATA_DIR, "metrics.jsonl")
    if os.path.exists(path):
        with open(path) as fh:
            for line in fh:
                if line.strip():
                    records.append(json.loads(line))
    # also pick up per-run metrics.json not yet in the jsonl
    if os.path.isdir(RUNS_DIR):
        seen = {r.get("run_tag") for r in records}
        for d in os.listdir(RUNS_DIR):
            p = os.path.join(RUNS_DIR, d, "metrics.json")
            if os.path.exists(p):
                with open(p) as fh:
                    rec = json.load(fh)
                if rec.get("run_tag") not in seen:
                    records.append(rec)
    return records


def run_view(record: dict) -> dict:
    """Observed V(t) + formula prediction + term breakdown for one run."""
    checkpoints = record.get("checkpoints", [])
    fix_budget = record.get("fix_budget_remaining", 1.0)
    activities = {
        name: (1.0 if enabled is True else 0.0)
        for name, enabled in record.get("factor_state", {}).items()
        if name in F.REGISTRY_BY_NAME
    }
    if isinstance(record.get("factor_state", {}).get("fix_loop"), dict):
        activities["fix_loop"] = fix_budget

    points, terms = [], []
    v = checkpoints[0]["v_obs"] if checkpoints and checkpoints[0].get("v_obs") is not None else 1.0
    prev_t = 0.0
    for cp in checkpoints:
        inputs = F.DecayInputs(
            entropy=cp.get("entropy", 0.0) or 0.0,
            opacity=cp.get("opacity", 0.0),
            blast_radius=cp.get("blast_radius", 0.0),
            spec_ambiguity=0.2 if activities.get("spec_refinement") else 0.6,
        )
        decay = F.decay_rate(inputs, form=F.DecayForm.HYBRID)
        recovery = F.recovery_rate(activities)
        dt = max(1e-3, cp["t_hours"] - prev_t)
        v_star = F.equilibrium_validity(recovery, decay)
        import math

        v = v_star + (v - v_star) * math.exp(-(recovery + decay) * dt)
        prev_t = cp["t_hours"]
        points.append(
            {
                "t": cp["t_hours"],
                "v_obs": cp.get("v_obs"),
                "v_model": round(v, 4),
            }
        )
        terms.append(
            {
                "t": cp["t_hours"],
                "recovery": round(recovery, 4),
                "decay": round(decay, 4),
                "decay_parts": {
                    "entropy": round(inputs.entropy, 3),
                    "opacity": round(inputs.opacity, 3),
                    "blast_radius": round(inputs.blast_radius, 3),
                    "spec_ambiguity": round(inputs.spec_ambiguity, 3),
                },
            }
        )

    v_end = record.get("final_v_obs")
    if v_end is None:
        v_end = points[-1]["v_model"] if points else 0.0
    consistency = 1.0 if record.get("final_pass") else 0.5  # per-run placeholder
    v_delivered = F.delivered_validity(v_end, consistency, 0.5, 2.0)
    return {
        "run_tag": record.get("run_tag"),
        "arm": record.get("arm"),
        "task": record.get("task"),
        "terminal_state": record.get("terminal_state"),
        "formula_version": F.FORMULA_VERSION,
        "evidence_status": getattr(F, "EVIDENCE_STATUS", "unknown"),
        "points": points,
        "terms": terms,
        "v_end": v_end,
        "v_delivered": round(v_delivered, 4),
        "verdict": F.trust_verdict(v_delivered).value,
        "stage_transitions": record.get("stage_transitions", {}),
        "fix_iterations": record.get("fix_iterations", 0),
    }


def summary() -> dict:
    records = load_metrics()
    by_task: dict[str, list] = {}
    for r in records:
        by_task.setdefault(r.get("task", "?"), []).append(r)
    tasks = []
    for task, recs in sorted(by_task.items()):
        n = len(recs)
        c = sum(1 for r in recs if r.get("final_pass"))
        tasks.append(
            {
                "task": task,
                "runs": n,
                "pass_rate": round(c / n, 3) if n else None,
                "pass_hat_k": round(F.pass_hat_k(c, n), 3) if n else None,
            }
        )
    return {
        "formula_version": F.FORMULA_VERSION,
        "evidence_status": getattr(F, "EVIDENCE_STATUS", "unknown"),
        "total_runs": len(records),
        "runs": [
            {
                "run_tag": r.get("run_tag"),
                "arm": r.get("arm"),
                "task": r.get("task"),
                "terminal_state": r.get("terminal_state"),
                "final_v_obs": r.get("final_v_obs"),
            }
            for r in records
        ],
        "tasks": tasks,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=_HERE, **kwargs)

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/summary"):
            self._json(summary())
            return
        if self.path.startswith("/api/run/"):
            tag = unquote(self.path[len("/api/run/"):])
            for r in load_metrics():
                if r.get("run_tag") == tag:
                    self._json(run_view(r))
                    return
            self._json({"error": f"run {tag!r} not found"}, 404)
            return
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8600)
    args = parser.parse_args()
    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"dashboard: http://localhost:{args.port}  (formula {F.FORMULA_VERSION})")
    server.serve_forever()


if __name__ == "__main__":
    main()
