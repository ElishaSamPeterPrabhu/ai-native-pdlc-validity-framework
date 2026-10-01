"""L1 golden-retrodiction runner for the workflow-builder skills.

Each run: scratch checkout of the target repo at a pinned SHA with the real
automation config held out, starter kit installed only for the `skills` arm,
a scripted persona answering the agent, then writes are recorded for score.py.

    python harness/skill-evals/run_eval.py --smoke
    python harness/skill-evals/run_eval.py --k 3
    python harness/skill-evals/score.py

Exit codes: 0 ok, 1 prerequisites or startup failed, 2 one or more runs failed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from cursor_sdk import (
        Agent,
        Cursor,
        CursorAgentError,
        LocalAgentOptions,
        ModelParameterValue,
        ModelSelection,
    )
except ImportError:  # optional: score.py and the L0 tests must run without it
    Agent = Cursor = LocalAgentOptions = ModelParameterValue = ModelSelection = None
    CursorAgentError = RuntimeError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCENARIOS = HERE / "scenarios"
KIT = ROOT / "starter-kit"
DEFAULT_RUNS = ROOT / "data" / "skill-evals" / "runs"
DEFAULT_MODEL = "composer-2.5"
MAX_TURNS = 6
MAX_COPY_BYTES = 1_000_000

OPENING = {
    "skills": (
        "Use the workflow-builder skill. I want AI delivery automations for this "
        "repository. Understand the repo first, then ask me about our process before "
        "designing anything."
    ),
    "bare": (
        "I want AI delivery automations for this repository. Understand the repo "
        "first, then ask me about our process before designing anything."
    ),
}


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _source_path(setup: dict) -> Path:
    src = setup["source"]
    raw = os.environ.get(src["path_env"]) or src["default_path"]
    path = Path(raw)
    return path if path.is_absolute() else (ROOT / path).resolve()


def _prerequisites(scenarios: list[str]) -> list[str]:
    problems = []
    if not os.environ.get("CURSOR_API_KEY"):
        problems.append("CURSOR_API_KEY is not set (Cursor dashboard -> Integrations -> API keys)")
    if Agent is None:
        problems.append("cursor-sdk is not installed: pip install 'cursor-sdk==1.0.35'")
    for name in scenarios:
        setup = json.loads((SCENARIOS / name / "setup.json").read_text())
        src = _source_path(setup)
        ref = setup["source"]["ref"]
        if not (src / ".git").exists():
            problems.append(f"{name}: source repo not found at {src} (set {setup['source']['path_env']})")
            continue
        probe = subprocess.run(["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=src, capture_output=True)
        if probe.returncode != 0:
            problems.append(f"{name}: commit {ref[:12]} missing in {src}; git fetch the fork/upstream")
    return problems


def _remove_held_out(scratch: Path, patterns: list[str]) -> list[str]:
    removed = []
    for pattern in patterns:
        for path in sorted(scratch.glob(pattern)):
            removed.append(str(path.relative_to(scratch)))
            shutil.rmtree(path) if path.is_dir() else path.unlink()
    return removed


def prepare_scratch(scenario: str, arm: str, scratch: Path) -> dict:
    setup = json.loads((SCENARIOS / scenario / "setup.json").read_text())
    src = _source_path(setup)
    archive = subprocess.run(
        ["git", "archive", "--format=tar", setup["source"]["ref"]],
        cwd=src, check=True, capture_output=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(scratch)], input=archive, check=True)
    removed = _remove_held_out(scratch, setup["held_out"])
    if arm == "skills":
        for sub in ("rules", "skills"):
            shutil.copytree(KIT / "cursor" / sub, scratch / ".cursor" / sub, dirs_exist_ok=True)
    _git(scratch, "init", "-q")
    _git(scratch, "add", "-A")
    _git(scratch, "-c", "user.name=eval", "-c", "user.email=eval@local",
         "commit", "-q", "-m", "baseline", "--no-verify")
    return {"source": str(src), "ref": setup["source"]["ref"], "held_out_removed": removed}


def collect_writes(scratch: Path, run_dir: Path) -> list[str]:
    out = _git(scratch, "status", "--porcelain", "--untracked-files=all")
    writes = sorted({line[3:].strip().strip('"') for line in out.splitlines() if line.strip()})
    workspace = run_dir / "workspace"
    for rel in writes:
        src = scratch / rel
        if "node_modules" in rel or not src.is_file() or src.stat().st_size > MAX_COPY_BYTES:
            continue
        dest = workspace / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return writes


def _is_fast(*labels: str) -> bool:
    return any("fast" in label.lower() for label in labels if label)


def _param_is_fast(param_id: str, value: str) -> bool:
    if _is_fast(value):
        return True
    return _is_fast(param_id) and value.lower() in ("true", "1", "on", "yes")


def describe_model(model) -> str:
    lines = [f"{model.id}  ({model.display_name})"]
    for param in model.parameters:
        values = ", ".join(v.value for v in param.values)
        lines.append(f"  param {param.id}: {values}")
    for variant in model.variants:
        params = ", ".join(f"{p.id}={p.value}" for p in variant.params)
        default = " [default]" if variant.is_default else ""
        lines.append(f"  variant {variant.display_name or '-'}: {params}{default}")
    return "\n".join(lines)


def resolve_model(model, allow_fast: bool) -> tuple[object, str]:
    """Pin an explicit variant; a bare id lets the account default (often fast) win."""
    if allow_fast:
        return ModelSelection(id=model.id), model.id
    for variant in sorted(model.variants, key=lambda v: not v.is_default):
        fast = _is_fast(variant.display_name) or any(
            _param_is_fast(p.id, p.value) for p in variant.params
        )
        if not fast:
            pairs = ",".join(f"{p.id}={p.value}" for p in variant.params)
            label = variant.display_name or pairs or model.id
            return ModelSelection(id=model.id, params=tuple(variant.params)), label
    params = []
    for param in model.parameters:
        if not _is_fast(param.id, *(v.value for v in param.values)):
            continue
        slow = [v for v in param.values if not _param_is_fast(param.id, v.value)]
        if not slow:
            raise ValueError(f"{model.id}: no non-fast value for parameter {param.id}")
        params.append(ModelParameterValue(id=param.id, value=slow[0].value))
    if model.variants and not params:
        raise ValueError(f"{model.id}: every variant is fast")
    label = ",".join(f"{p.id}={p.value}" for p in params) or model.id
    return ModelSelection(id=model.id, params=tuple(params)), label


def _asks_question(text: str) -> bool:
    tail = text.strip()[-600:]
    return "?" in tail


def run_one(scenario: str, arm: str, rep: int, model: str, selection, variant: str,
            allow_fast: bool, runs_dir: Path) -> dict:
    persona = json.loads((SCENARIOS / scenario / "persona.json").read_text())
    run_dir = runs_dir / f"{scenario}__{arm}__r{rep}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    meta = {"scenario": scenario, "arm": arm, "rep": rep, "model": model,
            "model_variant": variant, "models_used": [],
            "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    transcript: list[dict] = []
    scratch = Path(tempfile.mkdtemp(prefix=f"skill-eval-{scenario}-{arm}-"))
    try:
        meta.update(prepare_scratch(scenario, arm, scratch))
        answers = list(persona["answers"])
        message = OPENING[arm]
        finalized = False
        with Agent.create(
            model=selection,
            api_key=os.environ["CURSOR_API_KEY"],
            name=f"skill-eval {scenario} {arm} r{rep}",
            local=LocalAgentOptions(cwd=str(scratch), setting_sources=["project"]),
        ) as agent:
            for turn in range(1, MAX_TURNS + 1):
                transcript.append({"turn": turn, "role": "user", "text": message})
                result = agent.send(message).wait()
                reply = result.result or ""
                if result.model is not None:
                    used = result.model.id + "".join(
                        f" {p.id}={p.value}" for p in result.model.params
                    )
                    if used not in meta["models_used"]:
                        meta["models_used"].append(used)
                    if not allow_fast and (
                        _is_fast(result.model.id)
                        or any(_param_is_fast(p.id, p.value) for p in result.model.params)
                    ):
                        meta["status"] = "failed"
                        meta["error"] = f"server ran {used}, not the pinned non-fast variant"
                        break
                transcript.append({"turn": turn, "role": "assistant", "text": reply,
                                   "status": str(result.status)})
                if result.status != "finished":
                    meta["status"] = "failed"
                    meta["error"] = f"run status {result.status}"
                    break
                if finalized:
                    meta["status"] = "finished"
                    break
                if answers and _asks_question(reply):
                    message = answers.pop(0)
                else:
                    message = persona["finalize"]
                    finalized = True
            else:
                meta["status"] = "finished" if finalized else "turn_cap"
    except CursorAgentError as exc:
        meta["status"] = "failed"
        meta["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        writes = collect_writes(scratch, run_dir) if (scratch / ".git").exists() else []
        meta["writes"] = len(writes)
        (run_dir / "writes.json").write_text(json.dumps(writes, indent=2) + "\n")
        (run_dir / "transcript.jsonl").write_text(
            "".join(json.dumps(m) + "\n" for m in transcript)
        )
        meta["finished_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        shutil.rmtree(scratch, ignore_errors=True)
    return meta


def main(argv: list[str] | None = None) -> int:
    criteria = json.loads((HERE / "criteria.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", action="append", help="repeatable; default all")
    parser.add_argument("--arm", action="append", choices=criteria["arms"])
    parser.add_argument("--k", type=int, default=criteria["k"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--allow-fast", action="store_true",
                        help="use the account's default variant even if it is fast")
    parser.add_argument("--list-models", action="store_true",
                        help="print models, parameters and variants, then exit")
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--smoke", action="store_true", help="eng-modus, skills arm, k=1")
    args = parser.parse_args(argv)

    all_scenarios = sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir())
    scenarios = args.scenario or all_scenarios
    arms = args.arm or criteria["arms"]
    k = args.k
    if args.smoke:
        scenarios, arms, k = ["eng-modus"], ["skills"], 1
    unknown = [s for s in scenarios if s not in all_scenarios]
    if unknown:
        print(f"unknown scenario(s): {unknown}", file=sys.stderr)
        return 1

    problems = _prerequisites(scenarios)
    if problems:
        print("Cannot start L1 runs:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    try:
        models = {m.id: m for m in Cursor.models.list(api_key=os.environ["CURSOR_API_KEY"])}
    except CursorAgentError as exc:
        print(f"Cannot start L1 runs: {exc} (keys start with crsr_)", file=sys.stderr)
        return 1
    if args.list_models:
        for model in models.values():
            print(describe_model(model))
        return 0
    if args.model not in models:
        print(f"model {args.model!r} not available; choose from {sorted(models)}", file=sys.stderr)
        return 1
    try:
        selection, variant = resolve_model(models[args.model], args.allow_fast)
    except ValueError as exc:
        print(f"Cannot start L1 runs: {exc}\n{describe_model(models[args.model])}", file=sys.stderr)
        return 1
    print(f"model {args.model} variant {variant}")

    args.runs.mkdir(parents=True, exist_ok=True)
    failed = 0
    for scenario in scenarios:
        for arm in arms:
            for rep in range(1, k + 1):
                meta = run_one(scenario, arm, rep, args.model, selection, variant,
                               args.allow_fast, args.runs)
                used = ";".join(meta["models_used"]) or "?"
                print(f"{scenario:13} {arm:6} r{rep}  {meta['status']:9} "
                      f"writes={meta['writes']}  model={used}")
                failed += meta["status"] != "finished"
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
