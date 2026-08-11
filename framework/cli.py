"""CLI for the AI-Native PDLC Validity Framework research preview.

Commands:
  init      — write validity.layout.json + always-apply layout rule
  inspect   — Level 0 observe: build setup-manifest from a repo checkout
  evidence  — evidence pack for AI diagnosis (facts only; no layer verdict)
  intake    — merge user automation/PR intake into evidence pack (online path)
  delta     — compare two rounds (good → failed) for AI improve-from-delta
  score     — CLI-owned R/D/V* from run records or intake (placeholder weights)
  collect   — wrap existing harness collectors (path helper)
  calibrate — remind / launch Level 2 fit path when real metrics exist
  diagnose  — pointer to AI skill; optional --heuristic smoke hint
  report    — setup-validity profile aggregates by task class
  registry  — export portable factor registry JSON
  validate  — run local validation suite against baselines
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _repo(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "repo", ".")).resolve()


def _layout_for(args: argparse.Namespace):
    from framework.layout import load_layout

    layout_path = getattr(args, "layout", None) or None
    return load_layout(_repo(args), layout_path)


def _path_from_layout(args: argparse.Namespace, key: str, cli_value: str | None) -> Path:
    """Prefer explicit CLI path; otherwise resolve from layout relative to --repo."""
    if cli_value:
        p = Path(cli_value)
        return p if p.is_absolute() else (_repo(args) / p)
    layout = _layout_for(args)
    resolved = layout.resolve(_repo(args), key)
    if resolved is None:
        raise SystemExit(f"layout key {key!r} is unset; pass an explicit path or run init")
    return resolved


def cmd_init(args: argparse.Namespace) -> int:
    from framework.layout import init_repo_layout

    result = init_repo_layout(args.repo, force=args.force, layout_rel=args.layout_out)
    print(json.dumps({k: result[k] for k in ("layout_file", "rule_file", "created_layout")}, indent=2))
    print("Edit validity.layout.json if this repo uses different folders, then re-run init --force")
    print("or update .cursor/rules/validity-layout.mdc after changing paths.")
    notes = result["layout"].get("notes") or []
    if notes:
        print("discovery notes:")
        for n in notes[:8]:
            print(f"  - {n}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    from framework.adapters.inspect_repo import inspect_repository, write_manifest
    from framework.layout import load_layout

    layout = load_layout(args.repo, args.layout or None)
    manifest = inspect_repository(
        args.repo,
        owner=args.owner,
        name=args.name,
        layout=layout,
    )
    out = Path(args.out) if args.out else _path_from_layout(args, "setup_manifest_path", None)
    if not out.is_absolute():
        out = _repo(args) / out
    write_manifest(manifest, out)
    print(f"wrote setup-manifest → {out}")
    print(f"layout source={layout.source} file={layout.layout_file or '(none)'}")
    print(f"measurement_gaps ({len(manifest['measurement_gaps'])}):")
    for gap in manifest["measurement_gaps"][:12]:
        print(f"  - {gap}")
    return 0


def cmd_registry(args: argparse.Namespace) -> int:
    from theory import formula as F

    from framework.factor_catalog import export_registry

    payload = export_registry(F)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote factor registry → {out} (formula {F.FORMULA_VERSION})")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from framework.report import build_validity_report, load_metrics_jsonl, write_report

    metrics_path = _path_from_layout(args, "metrics_path", args.metrics or None)
    if not metrics_path.exists():
        print(f"metrics not found: {metrics_path}", file=sys.stderr)
        return 1

    records = load_metrics_jsonl(metrics_path, exclude_synthetic=not args.include_synthetic)
    manifest = None
    try:
        manifest_path = _path_from_layout(args, "setup_manifest_path", args.manifest or None)
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except SystemExit:
        if args.manifest:
            raise
    report = build_validity_report(
        records,
        repo=args.repo_label,
        manifest=manifest,
    )
    out = _path_from_layout(args, "validity_report_path", args.out or None)
    write_report(report, out)
    print(f"wrote validity-report → {out}")
    print(f"n_runs={report['n_runs']} evidence_status={report['evidence_status']}")
    print(
        "layer_diagnosis deferred_to_ai — run: python -m framework evidence "
        "then Cursor skill validity-diagnose"
    )
    for stratum, row in report["by_stratum"].items():
        print(
            f"  {stratum}: n={row['n']} mean_v={row['mean_v_obs']} "
            f"mechanical_lane={row['review_lane']}"
        )
    return 0


def cmd_delta(args: argparse.Namespace) -> int:
    from framework.delta import compare_intake_rounds, compare_reports, write_delta

    before_path = Path(args.before)
    after_path = Path(args.after)
    if not before_path.is_absolute():
        before_path = _repo(args) / before_path
    if not after_path.is_absolute():
        after_path = _repo(args) / after_path
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))

    # Heuristic: intake docs have "prs"; reports have "by_stratum"
    if "prs" in before or "prs" in after:
        pack = compare_intake_rounds(
            before,
            after,
            before_label=args.before_label,
            after_label=args.after_label,
        )
    else:
        pack = compare_reports(
            before,
            after,
            before_label=args.before_label,
            after_label=args.after_label,
        )

    out = Path(args.out) if args.out else _repo(args) / "data" / "delta-pack.json"
    if not out.is_absolute():
        out = _repo(args) / out
    write_delta(out, pack)
    print(f"wrote delta pack → {out}")
    scoring = pack.get("scoring") or {}
    if scoring.get("scoring_method"):
        print(f"scoring_method={scoring['scoring_method']} formula_used={scoring.get('formula_used')}")
    print(f"dominant_worsened_metric={pack.get('dominant_worsened_metric')}")
    for w in pack.get("worsened") or []:
        print(
            f"  {w.get('metric')}: {w.get('before')} → {w.get('after')} (Δ {w.get('delta')})"
        )
    print("Next: Cursor skill validity-improve-from-delta (AI explains + one fix).")
    print("Playbooks: framework/catalog/metric-playbooks.json")
    return 0


def cmd_intake(args: argparse.Namespace) -> int:
    from framework.intake import load_intake, merge_intake_into_evidence, write_json
    from framework.layout import load_layout

    intake_path = Path(args.intake)
    if not intake_path.is_absolute():
        intake_path = _repo(args) / intake_path
    if not intake_path.exists():
        print(f"intake file not found: {intake_path}", file=sys.stderr)
        print(
            "Copy framework/templates/intake/user-intake.example.json "
            "or use skill validity-intake",
            file=sys.stderr,
        )
        return 1

    intake = load_intake(intake_path)
    pack = merge_intake_into_evidence(
        args.repo,
        intake,
        include_offline_inspect=not args.intake_only,
        include_synthetic=args.include_synthetic,
    )
    layout = load_layout(args.repo, args.layout or None)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = _repo(args) / out
    else:
        out = _repo(args) / layout.data_dir / "evidence-pack.json"
    write_json(out, pack)
    print(f"wrote intake evidence pack → {out}")
    print(f"automations={len(intake.get('automations') or [])} prs={len(intake.get('prs') or [])}")
    print(f"gaps={len(pack.get('measurement_gaps') or [])}")
    print("Teach PR template: framework/templates/intake/pr-body-formula.md")
    print("Next: Cursor skill validity-diagnose (AI owns diagnosis).")
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    from framework.evidence import build_evidence_pack, write_evidence_pack
    from framework.layout import load_layout

    layout = load_layout(args.repo, args.layout or None)
    pack = build_evidence_pack(
        args.repo,
        layout=layout,
        include_synthetic=args.include_synthetic,
        include_heuristic_hint=args.heuristic_hint,
    )
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = _repo(args) / out
    else:
        out = _repo(args) / layout.data_dir / "evidence-pack.json"
    write_evidence_pack(pack, out)
    print(f"wrote evidence pack → {out}")
    print("Next: run Cursor skill validity-diagnose on this pack (AI owns diagnosis).")
    print(f"gaps={len(pack.get('measurement_gaps', []))} runs={pack['run_summary']['n_records']}")
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    """AI owns diagnosis. Default path builds an evidence pack; --heuristic is optional."""
    if not args.heuristic:
        print(
            "Diagnosis is AI-owned. Building an evidence pack for validity-diagnose…\n",
            file=sys.stderr,
        )
        # Normalize namespace for cmd_evidence
        args.heuristic_hint = False
        if not getattr(args, "out", None):
            args.out = ""
        return cmd_evidence(args)

    from framework.report import diagnose_layers, load_metrics_jsonl

    print(
        "WARNING: --heuristic is a non-authoritative keyword smoke test. "
        "Prefer `python -m framework evidence` + validity-diagnose skill.\n",
        file=sys.stderr,
    )
    manifest = None
    try:
        manifest_path = _path_from_layout(args, "setup_manifest_path", args.manifest or None)
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except SystemExit:
        if args.manifest:
            raise
    records = []
    try:
        metrics_path = _path_from_layout(args, "metrics_path", args.metrics or None)
        if metrics_path.exists():
            records = load_metrics_jsonl(
                metrics_path, exclude_synthetic=not args.include_synthetic
            )
    except SystemExit:
        if args.metrics:
            raise
    result = {
        "status": "non-authoritative-heuristic",
        "result": diagnose_layers(records, manifest),
    }
    print(json.dumps(result, indent=2))
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    layout = _layout_for(args)
    harness = layout.harness_dir or "harness"
    metrics = layout.metrics_path or "data/metrics.jsonl"
    print("Use Level 1 collectors with paths from validity.layout.json:")
    print(f"  python {harness}/collectors.py <run_dir>")
    print(f"  python {harness}/collect_run1.py")
    print(f"Run records should land in {metrics} (never mix unmarked synthetic).")
    print(f"Suggested runs path: {args.path or (layout.data_dir + '/runs')}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    from framework.score import build_score_pack, load_input, write_score_pack

    if args.metrics:
        in_path = Path(args.metrics)
        if not in_path.is_absolute():
            in_path = _repo(args) / in_path
    elif args.input:
        in_path = Path(args.input)
        if not in_path.is_absolute():
            in_path = _repo(args) / in_path
    else:
        in_path = _path_from_layout(args, "metrics_path", None)

    records: list[dict] = []
    intake_prs: list[dict] = []
    repo = args.repo_label or ""

    if in_path.exists():
        if in_path.suffix == ".jsonl":
            from framework.report import load_metrics_jsonl

            records = load_metrics_jsonl(
                in_path, exclude_synthetic=not args.include_synthetic
            )
        else:
            records, intake_prs, repo = load_input(in_path)
    else:
        print(f"input not found: {in_path}", file=sys.stderr)
        return 1

    pack = build_score_pack(records=records, intake_prs=intake_prs, repo=repo)
    out = Path(args.out) if args.out else _repo(args) / "data" / "score-pack.json"
    if not out.is_absolute():
        out = _repo(args) / out
    write_score_pack(out, pack)
    print(f"wrote score pack → {out}")
    agg = pack.get("aggregate", {}).get("V_star", {})
    v_star = agg.get("value") if isinstance(agg, dict) else agg
    print(f"aggregate_V_star={v_star} weight_source=placeholder")
    print("WARNING: placeholder weights — not repo-fitted. AI owns metric judgments.")
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    from framework.pilot_gates import check_pilot_exit, load_metrics_records

    metrics = _path_from_layout(args, "metrics_path", args.metrics or None)
    if not metrics.exists():
        print(f"missing metrics: {metrics}", file=sys.stderr)
        return 1

    records = load_metrics_records(metrics)
    gate = check_pilot_exit(records)
    real = gate["n_real"]
    print(
        f"metrics lines={gate['n_total']} non-synthetic={real} "
        f"terminal={gate['n_terminal']}"
    )
    if not gate["ok"]:
        print("Level 2 calibrate blocked:")
        for reason in gate["blocked_reasons"]:
            print(f"  - {reason}")
        print("See harness/PILOT-STATUS.md and framework/VALIDATION.md")
        return 2
    layout = _layout_for(args)
    analysis = layout.resolve(_repo(args), "analysis_dir")
    fit_py = (analysis / "fit.py") if analysis else (_ROOT / "analysis" / "fit.py")
    if not fit_py.exists():
        fit_py = _ROOT / "analysis" / "fit.py"
    print(f"Launching {fit_py} on real metrics…")
    import subprocess

    return subprocess.call([sys.executable, str(fit_py)])


def cmd_validate(args: argparse.Namespace) -> int:
    from framework.validate_local import run_validation

    out = Path(args.out)
    if not out.is_absolute():
        out = _repo(args) / out
    result = run_validation(out_dir=out)
    print(json.dumps(result["summary"], indent=2))
    print(f"full results → {out / 'validation_results.json'}")
    return 0 if result["summary"]["ok"] else 1


def _add_repo_layout_flags(s: argparse.ArgumentParser) -> None:
    s.add_argument("--repo", default=".", help="path to repository checkout")
    s.add_argument(
        "--layout",
        default="",
        help="path to validity.layout.json (default: discover under --repo)",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validity-framework",
        description="AI-Native PDLC Validity Framework (research preview)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Write validity.layout.json + layout Cursor rule")
    _add_repo_layout_flags(s)
    s.add_argument("--layout-out", default="validity.layout.json")
    s.add_argument("--force", action="store_true", help="rewrite layout from discovery")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("inspect", help="Inspect repo → setup-manifest")
    _add_repo_layout_flags(s)
    s.add_argument("--owner", default="")
    s.add_argument("--name", default="")
    s.add_argument(
        "--out",
        default="",
        help="default: layout.setup_manifest_path",
    )
    s.set_defaults(func=cmd_inspect)

    s = sub.add_parser("registry", help="Export portable factor registry")
    s.add_argument("--out", default="framework/schemas/factor-registry.instance.json")
    s.set_defaults(func=cmd_registry)

    s = sub.add_parser("report", help="Build setup-validity profile report")
    _add_repo_layout_flags(s)
    s.add_argument("--metrics", default="", help="default: layout.metrics_path")
    s.add_argument("--manifest", default="", help="default: layout.setup_manifest_path")
    s.add_argument("--repo-label", default="")
    s.add_argument("--out", default="", help="default: layout.validity_report_path")
    s.add_argument(
        "--include-synthetic",
        action="store_true",
        help="include synthetic records (demo only; not for claims)",
    )
    s.set_defaults(func=cmd_report)

    s = sub.add_parser(
        "delta",
        help="Compare two rounds for improve-from-delta (good → failed)",
    )
    _add_repo_layout_flags(s)
    s.add_argument("--before", required=True, help="prior intake or validity-report JSON")
    s.add_argument("--after", required=True, help="failed/later intake or validity-report JSON")
    s.add_argument("--before-label", default="round_good")
    s.add_argument("--after-label", default="round_failed")
    s.add_argument("--out", default="data/delta-pack.json")
    s.set_defaults(func=cmd_delta)

    s = sub.add_parser(
        "score",
        help="CLI-owned R/D/V* from run records or intake (placeholder weights)",
    )
    _add_repo_layout_flags(s)
    s.add_argument("--input", default="", help="run-record JSON or user-intake JSON")
    s.add_argument("--metrics", default="", help="metrics.jsonl or JSON input path")
    s.add_argument("--repo-label", default="")
    s.add_argument("--out", default="data/score-pack.json")
    s.add_argument(
        "--include-synthetic",
        action="store_true",
        help="include synthetic records from metrics.jsonl",
    )
    s.set_defaults(func=cmd_score)

    s = sub.add_parser(
        "intake",
        help="Merge user automation/PR intake into evidence pack",
    )
    _add_repo_layout_flags(s)
    s.add_argument(
        "--intake",
        required=True,
        help="path to user-intake.json (see templates/intake/)",
    )
    s.add_argument("--out", default="", help="default: <data_dir>/evidence-pack.json")
    s.add_argument(
        "--intake-only",
        action="store_true",
        help="skip offline git inspect; use intake only",
    )
    s.add_argument("--include-synthetic", action="store_true")
    s.set_defaults(func=cmd_intake)

    s = sub.add_parser(
        "evidence",
        help="Build evidence pack for AI diagnosis (facts only)",
    )
    _add_repo_layout_flags(s)
    s.add_argument("--out", default="", help="default: <data_dir>/evidence-pack.json")
    s.add_argument("--include-synthetic", action="store_true")
    s.add_argument(
        "--heuristic-hint",
        action="store_true",
        help="attach non-authoritative keyword hint for smoke tests",
    )
    s.set_defaults(func=cmd_evidence)

    s = sub.add_parser(
        "diagnose",
        help="Build evidence pack for AI skill (use --heuristic for smoke hint only)",
    )
    _add_repo_layout_flags(s)
    s.add_argument("--metrics", default="")
    s.add_argument("--manifest", default="")
    s.add_argument("--out", default="")
    s.add_argument("--include-synthetic", action="store_true")
    s.add_argument(
        "--heuristic",
        action="store_true",
        help="print non-authoritative keyword heuristic instead of evidence pack",
    )
    s.set_defaults(func=cmd_diagnose)

    s = sub.add_parser("collect", help="Show Level 1 collect guidance")
    _add_repo_layout_flags(s)
    s.add_argument("--path", default="")
    s.set_defaults(func=cmd_collect)

    s = sub.add_parser("calibrate", help="Level 2 fit when real data exists")
    _add_repo_layout_flags(s)
    s.add_argument("--metrics", default="")
    s.set_defaults(func=cmd_calibrate)

    s = sub.add_parser("validate", help="Local validation vs simpler baselines")
    _add_repo_layout_flags(s)
    s.add_argument("--out", default="data/validation")
    s.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
