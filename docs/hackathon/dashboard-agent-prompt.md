# Dashboard agent prompt — Timeline Monitor

Paste everything below the line into the agent that builds the dashboard.

---

Build **Timeline Monitor**: a LOCAL hackathon dashboard (no deploy) that shows every
AI delivery automation in one place, inspired by the TVA monitors in Loki (amber CRT
glow, "sacred timeline" flows, "nexus event" alerts). Do not use Marvel names, logos,
or assets in the UI; use the metaphor only.

## Repo

`Autonomous-Agent(Research)`. Read `validity.layout.json` first and use only its paths.
Keep `dashboard/server.py` and its existing `/api/summary` and `/api/run/<tag>` working.

## Stack

- **Frontend:** `dashboard/monitor/` (React 19 + Vite + TypeScript), Modus Web Components
  via `@trimble-oss/moduswebcomponents-react` (lock versions; import
  `@trimble-oss/moduswebcomponents/modus-wc-styles.css` once; call
  `defineCustomElements()` at startup). Use the Modus MCP (`user-modus-wc-2.0`) for
  component props, events, and setup. Use Modus for buttons, badges, chips, tables,
  tabs, toasts, panels, navbar, switches.
- **Theme:** a custom dark "amber terminal" theme built only from Modus tokens / CSS
  variables, plus scanline and glow effects on a custom SVG or canvas timeline (Modus
  has no timeline primitive).
- **Backend:** extend `dashboard/server.py` (stdlib only) with `/api/monitor/*`
  endpoints and serve the built monitor at `/monitor`. One command runs the demo.

## Data (hybrid: live first, replay fallback)

1. **GitHub live adapter** via the `gh` CLI (user's existing auth, READ-ONLY, never
   write): issues, PRs, labels, label events, comments, check runs for repos listed in
   `dashboard/monitor/monitor.config.json` (default `trimble-oss/modus-wc-2.0`). Poll
   every 20s using `since` / ETag to respect rate limits.
2. **Product→Issue adapter** (pluggable): a Google Sheet CSV export URL or a local
   `data/ledger.json` (rows: source meeting, classification, cursor comment, approval,
   linked issue). Optional; when absent show "not connected" as a measurement gap, not
   an error.
3. **Local framework artifacts:** `data/metrics.jsonl`, `data/score-pack.json`,
   `data/evidence-pack.json`, `data/validity-report.json`.
4. **Replay mode:** `python dashboard/server.py --record` snapshots live responses into
   `dashboard/monitor/fixtures/<date>/`; `--replay <dir>` serves them with a time
   cursor (play / pause / scrub) so the demo never breaks offline. The UI shows a
   LIVE / REPLAY badge at all times.

## Stage model

Derive stages from the signal contract in `harness/AUTOMATION-PROMPTS.md` and
`starter-kit/signal-contract.md`. Put the signal→stage map in `monitor.config.json`
so other repos can change it without code changes.

- **Product→Issue:** meeting/notes → ledger row → review round → approved → issue created.
- **Issue→PR:** issue opened → `/approve` → Dev (branch `exp/<n>-<slug>`) → PR opened →
  routing (`qa-full` | `qa-skip`) → `## QA PASSED` | `## QA FAILED` | `## QA SKIPPED` →
  Fix (`Fix applied:`, cap 3) → `qa-rerun` → `needs-human` / human review → merged | closed.
- **Nexus events** (branch off the sacred timeline): repeated QA FAILED,
  `## NEED CLARIFICATION`, `## NOT FEASIBLE`, `Max iterations reached`, stale > 24h in
  one stage, label/comment mismatch (for example `qa-skip` on a logic diff).
- **Pruned:** closed without merge.

## Views

1. **Monitor wall:** grid of workflow "screens", one per issue/PR lifeline, colored by state.
2. **Lifeline detail:** horizontal timeline with a node per stage, timestamps, actor
   (human vs `cursor[bot]`), comment excerpts, and links to GitHub.
3. **Validity panel:** R, D, V* exactly as returned by `python -m framework score`
   (shell out, pass the pack through unchanged). Show per-field provenance badges
   (observed / heuristic / imputed / missing), `weight_source`, and `record_kind`.
   If inputs are missing, show: "The framework does not have the necessary data to
   compute this; the gap is <fields>." NEVER compute or estimate R/D/V* in the frontend
   or in the monitor endpoints.
4. **Event ticker:** newest signals across all workflows.
5. **Throughput strip:** counts per stage, QA pass rate, fix iterations, human touches.

## Acceptance

- `python dashboard/server.py --port 8600` serves `/monitor` and the old dashboard at `/`.
- Live mode shows real issues/PRs from the configured repo within 30s.
- Replaying a recorded fixture plays a full issue→PR loop including one nexus event.
- No secrets committed; `gh` auth only; read-only toward GitHub.
- Switch statements over stage/state unions use an exhaustive `never` default.
- Imports at the top of every file.
- A short `dashboard/monitor/README.md` with run, record, and replay commands.
