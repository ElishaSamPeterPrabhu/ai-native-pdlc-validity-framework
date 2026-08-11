"""Phase D: fit the ODE to observed V(t) trajectories and value the factors.

Reads data/metrics.jsonl (collector output; works identically on synthetic and
real records). Produces data/fit_results.json with:

1. Arm contrasts (primary estimand per the Phase-B identifiability finding):
   ΔV_end, Δpass@1, Δpass^k per ablated factor vs baseline, with bootstrap CIs.
2. Joint ODE fit (secondary): factor weights w_f and decay weights, per decay form.
3. Model comparison: AIC/BIC across MULTIPLICATIVE / ADDITIVE / HYBRID decay forms
   and a no-covariate exponential baseline.
4. Hypothesis tests in telemetry form (opacity vs failure, etc.).

When run on real campaign data, the winning form + fitted weights constitute
formula v2 (ship into theory/formula.py and record in formula-changelog.md).
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from scipy.optimize import least_squares

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "theory"))

import formula as F  # noqa: E402

DATA = os.path.join(_ROOT, "data")

FITTED_FACTORS = list(getattr(F, "CORE_FITTED_FACTORS", (
    "spec_refinement", "agentic_qa", "fix_loop", "ci_gate",
    "mcp_context", "rules_context", "checkpointing", "review_bot",
)))
DECAY_KEYS = ["baseline", "entropy", "opacity", "blast_radius",
              "spec_ambiguity", "interaction_cs"]


def load_records() -> list[dict]:
    path = os.path.join(DATA, "metrics.jsonl")
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ---------------------------------------------------------------------------
# 1. Arm contrasts (primary)
# ---------------------------------------------------------------------------

def _boot_ci(values: list[float], n_boot: int = 2000, seed: int = 0):
    if not values:
        return (None, None)
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = [float(np.mean(rng.choice(arr, arr.size))) for _ in range(n_boot)]
    return (round(float(np.percentile(means, 2.5)), 4),
            round(float(np.percentile(means, 97.5)), 4))


def arm_contrasts(records: list[dict]) -> dict:
    by_arm: dict[str, list[dict]] = {}
    for r in records:
        by_arm.setdefault(r["arm"], []).append(r)

    def summarize(recs: list[dict]) -> dict:
        v = [r["final_v_obs"] for r in recs if r.get("final_v_obs") is not None]
        p = [1.0 if r.get("final_pass") else 0.0 for r in recs]
        # pass^k per task group
        by_task: dict[str, list] = {}
        for r in recs:
            by_task.setdefault(r["task"], []).append(bool(r.get("final_pass")))
        pk = [F.pass_hat_k(sum(g), len(g)) for g in by_task.values()]
        return {
            "n": len(recs),
            "v_end_mean": round(float(np.mean(v)), 4) if v else None,
            "v_end_ci": _boot_ci(v),
            "pass_at_1": round(float(np.mean(p)), 4) if p else None,
            "pass_hat_k": round(float(np.mean(pk)), 4) if pk else None,
        }

    base = summarize(by_arm.get("baseline", []))
    out = {"baseline": base, "contrasts": {}}
    for arm, recs in sorted(by_arm.items()):
        if arm == "baseline":
            continue
        s = summarize(recs)
        contrast = {
            "arm": s,
            "delta_v_end": (
                round(base["v_end_mean"] - s["v_end_mean"], 4)
                if base["v_end_mean"] is not None and s["v_end_mean"] is not None
                else None
            ),
            "delta_pass_at_1": (
                round(base["pass_at_1"] - s["pass_at_1"], 4)
                if base["pass_at_1"] is not None and s["pass_at_1"] is not None
                else None
            ),
            "delta_pass_hat_k": (
                round(base["pass_hat_k"] - s["pass_hat_k"], 4)
                if base["pass_hat_k"] is not None and s["pass_hat_k"] is not None
                else None
            ),
        }
        out["contrasts"][arm] = contrast
    return out


# ---------------------------------------------------------------------------
# 2 & 3. Joint ODE fit + model comparison
# ---------------------------------------------------------------------------

def _activities(record: dict) -> dict[str, float]:
    acts = {}
    for name in FITTED_FACTORS:
        val = record.get("factor_state", {}).get(name, False)
        acts[name] = 1.0 if val is True or isinstance(val, dict) else 0.0
    return acts


def _predict(record: dict, theta: np.ndarray, form: F.DecayForm) -> np.ndarray:
    nf = len(FITTED_FACTORS)
    w = dict(zip(FITTED_FACTORS, theta[:nf]))
    dw = F.DecayWeights(
        baseline=theta[nf], entropy=theta[nf + 1], opacity=theta[nf + 2],
        blast_radius=theta[nf + 3], spec_ambiguity=theta[nf + 4],
        interaction_cs=theta[nf + 5], multiplicative_rate=theta[nf],
    )
    acts = _activities(record)
    recovery = sum(w[k] * a for k, a in acts.items())
    cps = record["checkpoints"]
    sigma = 0.2 if acts.get("spec_refinement") else 0.6
    v = cps[0]["v_obs"] if cps[0].get("v_obs") is not None else 1.0
    preds = [v]
    prev_t = cps[0]["t_hours"]
    for cp in cps[1:]:
        inputs = F.DecayInputs(
            entropy=cp.get("entropy") or 0.0,
            opacity=cp.get("opacity") or 0.0,
            blast_radius=cp.get("blast_radius") or 0.0,
            spec_ambiguity=sigma,
        )
        decay = F.decay_rate(inputs, dw, form)
        dt = max(1e-3, cp["t_hours"] - prev_t)
        v_star = F.equilibrium_validity(recovery, decay)
        v = v_star + (v - v_star) * math.exp(-(recovery + decay) * dt)
        preds.append(v)
        prev_t = cp["t_hours"]
    return np.asarray(preds)


def fit_form(records: list[dict], form: F.DecayForm, seed: int = 0) -> dict:
    usable = [
        r for r in records
        if len(r.get("checkpoints", [])) >= 2
        and all(c.get("v_obs") is not None for c in r["checkpoints"])
    ]
    if not usable:
        return {"error": "no usable trajectories"}

    def residuals(theta):
        return np.concatenate([
            _predict(r, theta, form) - np.array([c["v_obs"] for c in r["checkpoints"]])
            for r in usable
        ])

    n = len(FITTED_FACTORS) + len(DECAY_KEYS)
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(4):
        sol = least_squares(residuals, rng.uniform(0.05, 1.0, n),
                            bounds=(0.0, 10.0), method="trf")
        if best is None or sol.cost < best.cost:
            best = sol
    res = best.fun
    n_obs = res.size
    rss = float(np.sum(res**2))
    sigma2 = max(rss / n_obs, 1e-12)
    loglik = -0.5 * n_obs * (math.log(2 * math.pi * sigma2) + 1)
    k = n
    return {
        "n_trajectories": len(usable),
        "n_obs": n_obs,
        "rmse": round(float(np.sqrt(np.mean(res**2))), 5),
        "aic": round(2 * k - 2 * loglik, 2),
        "bic": round(k * math.log(n_obs) - 2 * loglik, 2),
        "factor_weights": dict(zip(FITTED_FACTORS,
                                   np.round(best.x[:len(FITTED_FACTORS)], 4))),
        "decay_weights": dict(zip(DECAY_KEYS,
                                  np.round(best.x[len(FITTED_FACTORS):], 4))),
    }


def exponential_baseline(records: list[dict]) -> dict:
    """No-covariate model: V(t) = exp(-d t): one parameter."""
    ts, vs = [], []
    for r in records:
        for c in r.get("checkpoints", []):
            if c.get("v_obs") is not None:
                ts.append(c["t_hours"])
                vs.append(max(1e-6, c["v_obs"]))
    if not ts:
        return {"error": "no data"}
    ts, vs = np.asarray(ts), np.asarray(vs)
    d = max(0.0, float(-np.polyfit(ts, np.log(vs), 1)[0]))
    res = vs - np.exp(-d * ts)
    n_obs = res.size
    rss = float(np.sum(res**2))
    sigma2 = max(rss / n_obs, 1e-12)
    loglik = -0.5 * n_obs * (math.log(2 * math.pi * sigma2) + 1)
    return {
        "decay": round(d, 5),
        "rmse": round(float(np.sqrt(np.mean(res**2))), 5),
        "aic": round(2 * 1 - 2 * loglik, 2),
        "bic": round(1 * math.log(n_obs) - 2 * loglik, 2),
    }


# ---------------------------------------------------------------------------
# 4. Telemetry-form hypothesis tests
# ---------------------------------------------------------------------------

def hypotheses(records: list[dict]) -> dict:
    from scipy import stats

    out = {}
    # H(O): final opacity predicts failure (point-biserial correlation).
    op, fail = [], []
    for r in records:
        cps = r.get("checkpoints", [])
        if cps:
            op.append(cps[-1].get("opacity") or 0.0)
            fail.append(0.0 if r.get("final_pass") else 1.0)
    if len(set(fail)) > 1:
        rho, p = stats.pointbiserialr(fail, op)
        out["opacity_predicts_failure"] = {"r": round(float(rho), 3),
                                           "p": round(float(p), 4)}
    # H(C): blast radius correlates with fix iterations (Spearman).
    br = [r["checkpoints"][-1].get("blast_radius") or 0.0
          for r in records if r.get("checkpoints")]
    fi = [r.get("fix_iterations", 0) for r in records if r.get("checkpoints")]
    if len(set(fi)) > 1:
        rho, p = stats.spearmanr(br, fi)
        out["blast_radius_vs_fix_iterations"] = {"rho": round(float(rho), 3),
                                                 "p": round(float(p), 4)}
    # H(stratum): pass rate decreases with complexity (Cochran-Armitage-ish trend).
    order = {"low": 0, "medium": 1, "high": 2}
    xs = [order.get(r.get("stratum"), 1) for r in records]
    ys = [1.0 if r.get("final_pass") else 0.0 for r in records]
    if len(set(ys)) > 1:
        rho, p = stats.spearmanr(xs, ys)
        out["complexity_vs_pass"] = {"rho": round(float(rho), 3),
                                     "p": round(float(p), 4)}
    return out


def main() -> None:
    records = load_records()
    synthetic = all(r.get("synthetic") for r in records)
    results = {
        "data": "SYNTHETIC (pipeline validation only)" if synthetic else "real",
        "n_records": len(records),
        "arm_contrasts": arm_contrasts(records),
        "model_comparison": {
            "exponential_baseline": exponential_baseline(records),
            **{
                form.value: fit_form(records, form)
                for form in F.DecayForm
            },
        },
        "hypotheses": hypotheses(records),
    }
    out = os.path.join(DATA, "fit_results.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(json.dumps(results["arm_contrasts"], indent=2, default=str)[:1500])
    print("\nmodel comparison (AIC lower = better):")
    for name, m in results["model_comparison"].items():
        if "aic" in m:
            print(f"  {name:16s} AIC={m['aic']:>10}  BIC={m['bic']:>10}  RMSE={m['rmse']}")
    print("\nhypotheses:", json.dumps(results["hypotheses"], default=str))
    print("written:", out)
    if synthetic:
        print("\nNOTE: synthetic data - v2 formula shipping deferred until real "
              "campaign data exists (see PILOT-STATUS.md).")


if __name__ == "__main__":
    main()
