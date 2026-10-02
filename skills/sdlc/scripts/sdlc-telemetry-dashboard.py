#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn",
#   "structlog",
# ]
# ///
"""Dashboard for the SDLC telemetry database recorded by sdlc-telemetry.py.

Serves a single page of charts over the cross-repository telemetry SQLite
database: activity over time, events by step and by repository, pipeline
progression (average hours from an issue's first event to reaching each
step), a Sankey diagram of step-to-step transitions across issues, a
weekday-by-hour activity heatmap, and the most recent events.
The database is opened read-only and is never modified.

Run:
    uv run skills/sdlc/scripts/sdlc-telemetry-dashboard.py
    uv run skills/sdlc/scripts/sdlc-telemetry-dashboard.py --port 8788
    uv run skills/sdlc/scripts/sdlc-telemetry-dashboard.py --db path/to/telemetry.db
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

PIPELINE_STEPS: tuple[str, ...] = (
    "create-issue",
    "review-issue",
    "create-requirements",
    "review-requirements",
    "create-existing-solutions",
    "review-existing-solutions",
    "create-codebase-analysis",
    "review-codebase-analysis",
    "create-feasibility",
    "review-feasibility",
    "create-specifications",
    "review-specifications",
    "create-lifecycle",
    "review-lifecycle",
    "create-mockups",
    "review-mockups",
    "create-telemetry",
    "review-telemetry",
    "create-observability",
    "review-observability",
    "create-plan",
    "review-plan",
    "publish-plan",
    "validate-assumptions",
    "create-tasks-decomposition",
    "review-tasks-decomposition",
    "create-implementation",
    "refactor-implementation",
    "review-implementation",
    "create-documentation",
    "review-documentation",
    "validate-implementation",
    "create-pr",
    "validate-pr",
    "verify-pr",
    "handle-pr-ci",
    "handle-pr-reviewer-feedback",
    "merge-pr",
    "deploy-pr",
)

_RECENT_LIMIT = 25

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SDLC Telemetry</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-chart-sankey@0.19.1/dist/chartjs-chart-sankey.min.js"></script>
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --border: #30363d;
    --text: #c9d1d9; --muted: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --purple: #bc8cff; --orange: #d29922;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px; background: var(--bg); color: var(--text);
    font: 14px/1.5 -apple-system, "Segoe UI", system-ui, sans-serif;
  }
  header { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 20px; }
  h1 { font-size: 20px; margin: 0; }
  h1 span { color: var(--muted); font-weight: 400; }
  #db { color: var(--muted); font-family: ui-monospace, monospace; font-size: 12px; }
  select, button {
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 6px 10px; font-size: 13px; cursor: pointer;
  }
  #error { color: #f85149; margin: 12px 0; display: none; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 16px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
  .card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
  .card .value { font-size: 24px; font-weight: 600; margin-top: 4px; }
  .card .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid .wide { grid-column: 1 / -1; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .panel h2 { font-size: 14px; margin: 0 0 12px; color: var(--muted); font-weight: 600; }
  .chart-box { position: relative; height: 320px; }
  .chart-box.tall { height: 380px; }
  .chart-box.sankey { height: 560px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: var(--muted); font-weight: 600; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  td { padding: 6px 8px; border-bottom: 1px solid rgba(48, 54, 61, 0.4); }
  td.mono, .mono { font-family: ui-monospace, monospace; font-size: 12px; }
  td a { color: var(--accent); text-decoration: none; }
  td a:hover { text-decoration: underline; }
  #heatmap { overflow-x: auto; }
  #heatmap table { border-collapse: separate; border-spacing: 2px; }
  #heatmap th { border: none; padding: 2px 4px; font-size: 11px; }
  #heatmap td { border: none; padding: 0; }
  #heatmap .cell { width: 22px; height: 22px; border-radius: 3px; background: #1c2128; }
  #empty { color: var(--muted); text-align: center; padding: 60px 0; display: none; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <h1>SDLC Telemetry <span>dashboard</span></h1>
  <select id="repo-select" onchange="setRepo(this.value)"><option value="">All repositories</option></select>
  <button onclick="load()">Refresh</button>
  <span id="db" class="mono"></span>
</header>
<div id="error"></div>
<div id="empty">No events recorded yet. Run SDLC skills to populate the telemetry database.</div>
<div id="content">
  <div class="cards" id="cards"></div>
  <div class="grid">
    <div class="panel wide"><h2>Events per day</h2><div class="chart-box"><canvas id="timeline"></canvas></div></div>
    <div class="panel"><h2>Events by step</h2><div class="chart-box tall"><canvas id="by-step"></canvas></div></div>
    <div class="panel"><h2>Events by repository</h2><div class="chart-box tall"><canvas id="by-repo"></canvas></div></div>
    <div class="panel wide"><h2>Pipeline progression (avg hours from an issue's first event to first reach of each step)</h2><div class="chart-box tall"><canvas id="pipeline"></canvas></div></div>
    <div class="panel wide"><h2>Pipeline flow (Sankey: consecutive step transitions within each issue)</h2><div class="chart-box sankey"><canvas id="sankey"></canvas></div></div>
    <div class="panel"><h2>Activity by weekday and hour (UTC)</h2><div id="heatmap"></div></div>
    <div class="panel"><h2>Recent events</h2><div id="recent"></div></div>
  </div>
</div>
<script>
const PALETTE = ["#58a6ff", "#3fb950", "#bc8cff", "#d29922", "#f85149", "#39c5cf", "#db61a2", "#8b949e"];
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
let charts = [];
let repo = new URLSearchParams(location.search).get("repo") || "";

Chart.defaults.color = "#8b949e";
Chart.defaults.borderColor = "rgba(48, 54, 61, 0.6)";
Chart.defaults.font.family = '-apple-system, "Segoe UI", system-ui, sans-serif';

function setRepo(value) {
  repo = value;
  const url = repo ? `/?repo=${encodeURIComponent(repo)}` : "/";
  history.replaceState(null, "", url);
  load();
}

function card(label, value, sub) {
  return `<div class="card"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub || ""}</div></div>`;
}

function renderStats(d) {
  const t = d.totals;
  const span = t.first_ts ? `${t.first_ts.slice(0, 10)} to ${t.last_ts.slice(0, 10)}` : "";
  document.getElementById("cards").innerHTML =
    card("Total events", t.events, span) +
    card("Issues", t.issues, `${t.events && t.issues ? (t.events / t.issues).toFixed(1) : 0} events per issue`) +
    card("Repositories", d.by_repo.length) +
    card("Last 7 days", t.last7, "events") +
    card("Top step", d.by_step.length ? d.by_step[0][0].replace("create-", "").replace("review-", "review ") : "-", d.by_step.length ? `${d.by_step[0][1]} events` : "") +
    card("Busiest repo", d.by_repo.length ? d.by_repo[0][0].split("/")[1] || d.by_repo[0][0] : "-", d.by_repo.length ? `${d.by_repo[0][1]} events` : "");
}

function renderRepoOptions(d) {
  const sel = document.getElementById("repo-select");
  sel.innerHTML = '<option value="">All repositories</option>' +
    d.by_repo.map(([r]) => `<option value="${r}" ${r === repo ? "selected" : ""}>${r}</option>`).join("");
}

function makeChart(id, config) {
  charts.push(new Chart(document.getElementById(id), config));
}

function renderTimeline(d) {
  makeChart("timeline", {
    type: "line",
    data: {
      labels: d.daily.map((r) => r[0]),
      datasets: [{
        label: "Events", data: d.daily.map((r) => r[1]),
        borderColor: PALETTE[0], backgroundColor: "rgba(88, 166, 255, 0.15)",
        fill: true, tension: 0.25, pointRadius: 2,
      }],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

function renderByStep(d) {
  makeChart("by-step", {
    type: "bar",
    data: {
      labels: d.by_step.map((r) => r[0]),
      datasets: [{ label: "Events", data: d.by_step.map((r) => r[1]), backgroundColor: "rgba(88, 166, 255, 0.75)", borderRadius: 3 }],
    },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

function renderByRepo(d) {
  makeChart("by-repo", {
    type: "doughnut",
    data: {
      labels: d.by_repo.map((r) => r[0]),
      datasets: [{ data: d.by_repo.map((r) => r[1]), backgroundColor: PALETTE, borderColor: "#161b22", borderWidth: 2 }],
    },
    options: { maintainAspectRatio: false, cutout: "55%",
      plugins: { legend: { position: "right", labels: { boxWidth: 12, padding: 8 } } } },
  });
}

function renderPipeline(d) {
  const rows = d.pipeline;
  makeChart("pipeline", {
    type: "bar",
    data: {
      labels: rows.map((r) => r.step),
      datasets: [
        { label: "Avg hours from issue start", data: rows.map((r) => r.avg_hours),
          backgroundColor: "rgba(188, 140, 255, 0.75)", borderRadius: 3, yAxisID: "y" },
        { label: "Issues reaching step", data: rows.map((r) => r.issues), type: "line",
          borderColor: PALETTE[1], backgroundColor: PALETTE[1], tension: 0.3, pointRadius: 3, yAxisID: "y1" },
      ],
    },
    options: { maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "hours" } },
        y1: { position: "right", beginAtZero: true, ticks: { precision: 0 }, grid: { drawOnChartArea: false } },
      } },
  });
}

function renderFlow(d) {
  const links = d.flow.links;
  const canvas = document.getElementById("sankey");
  if (!links.length) {
    canvas.parentElement.innerHTML = '<p style="color: var(--muted)">No issue-linked events recorded yet.</p>';
    return;
  }
  const order = d.pipeline_order;
  const rank = (s) => { const i = order.indexOf(s); return i === -1 ? order.length : i; };
  const color = (s) => PALETTE[rank(s) % PALETTE.length];
  const priority = {};
  links.forEach(([s, t]) => { priority[s] = rank(s); priority[t] = rank(t); });
  makeChart("sankey", {
    type: "sankey",
    data: {
      datasets: [{
        label: "Step transitions",
        data: links.map(([s, t, n]) => ({ from: s, to: t, flow: n })),
        colorFrom: (c) => color(c.raw.from),
        colorTo: (c) => color(c.raw.to),
        alpha: 0.35,
        priority,
        nodePadding: 6,
        nodeMinSize: 3,
        size: "max",
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { displayColors: false } },
    },
  });
}

function renderHeatmap(d) {
  const max = Math.max(1, ...Object.values(d.heatmap));
  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  let html = "<table><tr><th></th>" + Array.from({ length: 24 }, (_, h) => `<th>${h}</th>`).join("") + "</tr>";
  for (let wd = 0; wd < 7; wd++) {
    html += `<tr><th>${weekdays[wd]}</th>`;
    for (let h = 0; h < 24; h++) {
      const n = d.heatmap[`${wd}-${h}`] || 0;
      const alpha = n ? 0.15 + 0.85 * (n / max) : 0;
      html += `<td><div class="cell" style="background: rgba(88, 166, 255, ${alpha})" title="${weekdays[wd]} ${h}:00 UTC, ${n} event${n === 1 ? "" : "s"}"></div></td>`;
    }
    html += "</tr>";
  }
  document.getElementById("heatmap").innerHTML = html + "</table>";
}

function renderRecent(d) {
  const rows = d.recent.map((r) => {
    const issue = r.issue && r.repo
      ? `<a href="https://github.com/${r.repo}/issues/${r.issue}" target="_blank">#${r.issue}</a>`
      : r.issue ? `#${r.issue}` : "-";
    return `<tr><td class="mono">${r.timestamp.replace("T", " ")}</td><td class="mono">${r.step}</td><td class="mono">${r.repo || "-"}</td><td>${issue}</td></tr>`;
  }).join("");
  document.getElementById("recent").innerHTML =
    `<table><tr><th>Time (UTC)</th><th>Step</th><th>Repo</th><th>Issue</th></tr>${rows}</table>`;
}

async function load() {
  const errorEl = document.getElementById("error");
  errorEl.style.display = "none";
  try {
    const res = await fetch(`/api/data?repo=${encodeURIComponent(repo)}`);
    const data = await res.json();
    if (data.error) { errorEl.textContent = data.error; errorEl.style.display = "block"; return; }
    document.getElementById("db").textContent = data.db;
    const hasData = data.totals.events > 0;
    document.getElementById("empty").style.display = hasData ? "none" : "block";
    document.getElementById("content").style.display = hasData ? "block" : "none";
    if (!hasData) return;
    renderStats(data);
    renderRepoOptions(data);
    charts.forEach((c) => c.destroy());
    charts = [];
    renderTimeline(data);
    renderByStep(data);
    renderByRepo(data);
    renderPipeline(data);
    renderFlow(data);
    renderHeatmap(data);
    renderRecent(data);
  } catch (err) {
    errorEl.textContent = `Failed to load telemetry: ${err}`;
    errorEl.style.display = "block";
  }
}

load();
</script>
</body>
</html>
"""


def default_db_path() -> Path:
    override = os.environ.get("SDLC_TELEMETRY_DB")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "sdlc" / "telemetry.db"


def connect_ro(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{quote(str(db))}?mode=ro", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def pipeline_sort_key(step: str) -> tuple[int, str]:
    try:
        return (PIPELINE_STEPS.index(step), step)
    except ValueError:
        return (len(PIPELINE_STEPS), step)


def build_heatmap(timestamps: list[str]) -> dict[str, int]:
    cells: dict[str, int] = {}
    for raw in timestamps:
        try:
            ts = datetime.fromisoformat(raw)
        except ValueError:
            continue
        key = f"{ts.weekday()}-{ts.hour}"
        cells[key] = cells.get(key, 0) + 1
    return cells


def build_clause(conds: list[str], prefix: str = "", op: str = "WHERE") -> str:
    if not conds:
        return ""
    return f" {op} " + " AND ".join(prefix + c for c in conds)


def query_data(conn: sqlite3.Connection, repo: str) -> dict[str, Any]:
    conds = ["repo = ?"] if repo else []
    params: list[object] = [repo] if repo else []
    where = build_clause(conds)

    totals = conn.execute(
        f"SELECT COUNT(*) AS events, COUNT(DISTINCT issue) AS issues, "
        f"COUNT(DISTINCT repo) AS repos, MIN(timestamp) AS first_ts, "
        f"MAX(timestamp) AS last_ts FROM sdlc_events{where}",
        params,
    ).fetchone()

    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(
        timespec="seconds"
    )
    last7 = conn.execute(
        f"SELECT COUNT(*) AS n FROM sdlc_events"
        f"{build_clause(conds + ['timestamp >= ?'])}",
        params + [cutoff],
    ).fetchone()["n"]

    daily = [
        [r["day"], r["n"]]
        for r in conn.execute(
            f"SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS n "
            f"FROM sdlc_events{where} GROUP BY day ORDER BY day",
            params,
        )
    ]

    by_step = [
        [r["step"], r["n"]]
        for r in conn.execute(
            f"SELECT step, COUNT(*) AS n FROM sdlc_events{where} GROUP BY step ORDER BY n DESC",
            params,
        )
    ]

    by_repo = [
        [r["repo"], r["n"]]
        for r in conn.execute(
            f"SELECT COALESCE(repo, '(unknown)') AS repo, COUNT(*) AS n "
            f"FROM sdlc_events{where} GROUP BY repo ORDER BY n DESC",
            params,
        )
    ]

    pipeline_rows = conn.execute(
        f"""
        WITH starts AS (
            SELECT issue, MIN(timestamp) AS first_ts
            FROM sdlc_events
            WHERE issue IS NOT NULL{build_clause(conds, op="AND")}
            GROUP BY issue
        ),
        reached AS (
            SELECT e.step, e.issue, e.timestamp, s.first_ts
            FROM sdlc_events e
            JOIN starts s ON s.issue = e.issue
            WHERE e.issue IS NOT NULL{build_clause(conds, prefix="e.", op="AND")}
        ),
        first_reach AS (
            SELECT step, issue, MIN(timestamp) AS reached_at, first_ts
            FROM reached
            GROUP BY step, issue
        )
        SELECT step,
               AVG((julianday(reached_at) - julianday(first_ts)) * 24) AS avg_hours,
               COUNT(*) AS issues
        FROM first_reach
        GROUP BY step
        """,
        params + params,
    ).fetchall()
    pipeline = sorted(
        (
            {
                "step": r["step"],
                "avg_hours": round(r["avg_hours"], 1)
                if r["avg_hours"] is not None
                else 0.0,
                "issues": r["issues"],
            }
            for r in pipeline_rows
        ),
        key=lambda r: pipeline_sort_key(r["step"]),
    )

    heatmap_rows = conn.execute(
        f"SELECT timestamp FROM sdlc_events{where}", params
    ).fetchall()
    heatmap = build_heatmap([r["timestamp"] for r in heatmap_rows])

    recent = [
        {
            "timestamp": r["timestamp"],
            "step": r["step"],
            "repo": r["repo"],
            "issue": r["issue"],
        }
        for r in conn.execute(
            f"SELECT timestamp, step, repo, issue FROM sdlc_events{where} "
            "ORDER BY id DESC LIMIT ?",
            params + [_RECENT_LIMIT],
        )
    ]

    flow_rows = conn.execute(
        f"SELECT repo, issue, step, timestamp, id FROM sdlc_events"
        f"{build_clause(conds + ['issue IS NOT NULL'])} "
        "ORDER BY repo, issue, timestamp, id",
        params,
    ).fetchall()
    transitions: dict[tuple[str, str], int] = {}
    prev_key: tuple[Any, Any] | None = None
    prev_step: str | None = None
    for r in flow_rows:
        key = (r["repo"], r["issue"])
        if prev_key == key and prev_step and r["step"]:
            transitions[(prev_step, r["step"])] = (
                transitions.get((prev_step, r["step"]), 0) + 1
            )
        prev_key = key
        prev_step = r["step"]
    flow = {
        "links": [
            [src, dst, n]
            for (src, dst), n in sorted(transitions.items(), key=lambda kv: -kv[1])
        ]
    }

    return {
        "totals": {
            "events": totals["events"],
            "issues": totals["issues"],
            "repos": totals["repos"],
            "first_ts": totals["first_ts"],
            "last_ts": totals["last_ts"],
            "last7": last7,
        },
        "daily": daily,
        "by_step": by_step,
        "by_repo": by_repo,
        "pipeline": pipeline,
        "flow": flow,
        "pipeline_order": list(PIPELINE_STEPS),
        "heatmap": heatmap,
        "recent": recent,
    }


def create_app(db: Path) -> FastAPI:
    app = FastAPI(title="SDLC Telemetry Dashboard", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML_PAGE

    @app.get("/api/data")
    def data(repo: str = "") -> JSONResponse:
        if not db.exists():
            return JSONResponse({"error": f"No telemetry database at {db}"})
        try:
            with connect_ro(db) as conn:
                payload = query_data(conn, repo)
        except sqlite3.Error as exc:
            return JSONResponse({"error": f"Failed to read {db}: {exc}"})
        payload["db"] = str(db)
        return JSONResponse(payload)

    return app


def main() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(
        description="Serve a dashboard over the SDLC telemetry SQLite database (read-only).",
    )
    parser.add_argument(
        "--db", help="Path to telemetry database (overrides $SDLC_TELEMETRY_DB)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8788, help="Port (default 8788)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress logging")
    args = parser.parse_args()
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    db = Path(args.db).expanduser() if args.db else default_db_path()
    log = structlog.get_logger()
    log.info("dashboard_starting", db=str(db), exists=db.exists(), port=args.port)
    uvicorn.run(create_app(db), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
