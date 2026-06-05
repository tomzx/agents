#!/usr/bin/env python3
"""Render an SDLC status dashboard HTML page from .sdlc/ directory data."""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def read_feature(feature_dir: Path) -> dict | None:
    fm, _ = parse_frontmatter(feature_dir.name)
    progress_path = feature_dir / "progress.md"
    if progress_path.exists():
        progress_fm, _ = parse_frontmatter(progress_path.read_text())
    else:
        progress_fm = {}

    title = progress_fm.get("title", feature_dir.name)
    issue = str(progress_fm.get("issue", ""))
    current_phase = progress_fm.get("current_phase", "")
    re_entry_point = progress_fm.get("re_entry_point", "")
    last_updated = progress_fm.get("last_updated", "")

    summary = ""
    blocker = None
    pipeline_rows: list[dict] = []
    task_rows: list[dict] = []
    sessions: list[dict] = []

    if progress_path.exists():
        body = progress_path.read_text()
        _, content = parse_frontmatter(body)

        summary_m = re.search(r"## Summary\s*\n\s*(.+?)(?:\n##|\Z)", content, re.DOTALL)
        if summary_m:
            summary = summary_m.group(1).strip()

        blocker_m = re.search(r"## Current Blocker\s*\n\s*(.+?)(?:\n##|\Z)", content, re.DOTALL)
        if blocker_m:
            blocker_text = blocker_m.group(1).strip()
            if blocker_text and blocker_text.lower() not in ("none", "<describe the current blocker, or write \"none\".>"):
                blocker = blocker_text

        pipeline_m = re.search(r"## Pipeline Status\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL)
        if pipeline_m:
            pipeline_section = pipeline_m.group(1)
            for line in pipeline_section.split("\n"):
                line = line.strip()
                if line.startswith("|") and not line.startswith("| Stage"):
                    parts = [p.strip() for p in line.split("|")]
                    parts = [p for p in parts if p]
                    if len(parts) >= 3 and parts[0] not in ("Stage", "---"):
                        pipeline_rows.append({
                            "stage": parts[0],
                            "phase": parts[1],
                            "status": parts[2] if parts[2] != "—" else "not-started",
                        })

        task_m = re.search(r"## Task Progress\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL)
        if task_m:
            task_section = task_m.group(1)
            for line in task_section.split("\n"):
                line = line.strip()
                if line.startswith("|") and not line.startswith("| ID"):
                    parts = [p.strip() for p in line.split("|")]
                    parts = [p for p in parts if p]
                    if len(parts) >= 4 and parts[0] not in ("ID", "---"):
                        task_rows.append({
                            "id": parts[0],
                            "title": parts[1],
                            "size": parts[2],
                            "status": parts[3],
                            "completed": parts[4] if len(parts) > 4 and parts[4] != "—" else "",
                            "blocker": parts[5] if len(parts) > 5 and parts[5] not in ("—", "") else "",
                        })

        session_m = re.search(r"## Session Log\s*\n(.+?)\Z", content, re.DOTALL)
        if session_m:
            session_section = session_m.group(1)
            for line in session_section.split("\n"):
                line = line.strip()
                if line.startswith("|") and not line.startswith("| Date"):
                    parts = [p.strip() for p in line.split("|")]
                    parts = [p for p in parts if p]
                    if len(parts) >= 2 and parts[0] not in ("Date", "---"):
                        sessions.append({
                            "date": parts[0],
                            "summary": parts[1] if len(parts) > 1 else "",
                            "next": parts[2] if len(parts) > 2 else "",
                        })

    tasks_dir = feature_dir / "tasks"
    task_files: list[dict] = []
    if tasks_dir.exists():
        for tf in sorted(tasks_dir.glob("*.md")):
            tfm, _ = parse_frontmatter(tf.read_text())
            if tfm:
                task_files.append({
                    "id": str(tfm.get("id", tf.stem.split("-")[0])),
                    "title": tfm.get("title", ""),
                    "status": tfm.get("status", "pending"),
                    "size": tfm.get("size", ""),
                    "depends_on": tfm.get("depends_on", []),
                    "completed_date": tfm.get("completed_date") or "",
                    "blocker": tfm.get("blocker") or "",
                })

    if task_files and not task_rows:
        task_rows = task_files
    elif task_files:
        file_by_id = {t["id"]: t for t in task_files}
        for tr in task_rows:
            if tr["id"] in file_by_id:
                tf = file_by_id[tr["id"]]
                tr["status"] = tf["status"]
                tr["completed"] = tf.get("completed_date", "") or tr.get("completed", "")
                tr["blocker"] = tf.get("blocker", "") or tr.get("blocker", "")

    return {
        "id": feature_dir.name.split("-")[0] + "-" + feature_dir.name.split("-")[1],
        "dir_name": feature_dir.name,
        "title": title,
        "issue": issue,
        "current_phase": current_phase,
        "re_entry_point": re_entry_point,
        "last_updated": last_updated,
        "summary": summary,
        "blocker": blocker,
        "pipeline": pipeline_rows,
        "tasks": task_rows,
        "sessions": sessions,
    }


def collect_features(sdlc_dir: Path) -> list[dict]:
    features_dir = sdlc_dir / "features"
    if not features_dir.exists():
        return []
    features = []
    for d in sorted(features_dir.iterdir()):
        if d.is_dir() and d.name != "templates":
            feat = read_feature(d)
            if feat:
                features.append(feat)
    return features


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SDLC Status Dashboard</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface-alt: #222636;
    --border: #2e3347;
    --text: #e1e4ed;
    --text-muted: #8b8fa3;
    --accent: #6c8cff;
    --accent-dim: #3a4a7a;
    --green: #4ade80;
    --green-dim: #1a3a2a;
    --yellow: #facc15;
    --yellow-dim: #3a3520;
    --red: #f87171;
    --red-dim: #3a2020;
    --blue: #60a5fa;
    --blue-dim: #1e2d4a;
    --gray: #6b7280;
    --gray-dim: #2a2d37;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }
  h1 { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; }
  h3 { font-size: 0.8rem; font-weight: 600; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }

  .header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }
  .header h1 { color: var(--accent); }
  .header .date { color: var(--text-muted); font-size: 0.85rem; }

  .summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.25rem;
  }
  .card .label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
  .card .value { font-size: 1.4rem; font-weight: 700; margin-top: 0.25rem; }
  .c-green { color: var(--green) !important; }
  .c-blue { color: var(--blue) !important; }
  .c-yellow { color: var(--yellow) !important; }
  .c-red { color: var(--red) !important; }
  .c-accent { color: var(--accent) !important; }
  .c-muted { color: var(--text-muted) !important; }

  .section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
  }

  .pipeline-stages { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: flex-start; }
  .pipeline-stage .stage-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
  }
  .pipeline-phases { display: flex; gap: 0.25rem; flex-wrap: wrap; }
  .chip {
    font-size: 0.65rem;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    white-space: nowrap;
    font-weight: 500;
  }
  .chip-done { background: var(--green-dim); color: var(--green); }
  .chip-in-progress { background: var(--yellow-dim); color: var(--yellow); }
  .chip-blocked { background: var(--red-dim); color: var(--red); }
  .chip-skipped { background: var(--gray-dim); color: var(--gray); text-decoration: line-through; }
  .chip-not-started { background: var(--surface-alt); color: var(--text-muted); }
  .chip-approved { background: var(--green-dim); color: var(--green); }
  .chip-draft { background: var(--surface-alt); color: var(--text-muted); }
  .chip-in-review { background: var(--yellow-dim); color: var(--yellow); }

  .progress-bar-track { background: var(--surface-alt); border-radius: 6px; height: 8px; overflow: hidden; margin-bottom: 0.25rem; }
  .progress-bar-fill { height: 100%; border-radius: 6px; transition: width 0.3s ease; }
  .progress-meta { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem; }

  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { text-align: left; padding: 0.45rem 0.65rem; font-weight: 600; color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }
  td { padding: 0.45rem 0.65rem; border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }

  .badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 0.12rem 0.4rem;
    border-radius: 3px;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }
  .badge-done { background: var(--green-dim); color: var(--green); }
  .badge-in-progress { background: var(--blue-dim); color: var(--blue); }
  .badge-blocked { background: var(--red-dim); color: var(--red); }
  .badge-pending { background: var(--gray-dim); color: var(--gray); }
  .badge-cancelled { background: var(--gray-dim); color: var(--gray); text-decoration: line-through; }
  .badge-draft { background: var(--surface-alt); color: var(--text-muted); }
  .badge-approved { background: var(--green-dim); color: var(--green); }

  .size { display: inline-block; font-size: 0.65rem; font-weight: 600; padding: 0.1rem 0.35rem; border-radius: 3px; background: var(--surface-alt); color: var(--text-muted); }

  .blocker-banner {
    background: var(--red-dim);
    border: 1px solid var(--red);
    border-radius: 6px;
    padding: 0.65rem 0.9rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .blocker-banner .icon { color: var(--red); font-weight: 700; flex-shrink: 0; }
  .blocker-banner .btitle { font-weight: 600; color: var(--red); font-size: 0.8rem; }
  .blocker-banner .bdesc { color: var(--text); font-size: 0.8rem; margin-top: 0.1rem; }

  .feature-tabs { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
  .ftab {
    padding: 0.35rem 0.85rem;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-muted);
    font-size: 0.82rem;
    cursor: pointer;
  }
  .ftab:hover { border-color: var(--accent); color: var(--text); }
  .ftab.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); font-weight: 600; }
  .ftab .fid { font-weight: 600; }

  .session-log { max-height: 220px; overflow-y: auto; }
  .session-date { white-space: nowrap; color: var(--text-muted); font-size: 0.78rem; }
  .session-next { color: var(--accent); font-size: 0.78rem; }

  .crit-path { display: flex; align-items: center; gap: 0.2rem; flex-wrap: wrap; margin-top: 0.5rem; }
  .cpn { display: inline-flex; align-items: center; padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 600; }
  .cpn-done { background: var(--green-dim); color: var(--green); }
  .cpn-in-progress { background: var(--blue-dim); color: var(--blue); }
  .cpn-blocked { background: var(--red-dim); color: var(--red); }
  .cpn-pending { background: var(--surface-alt); color: var(--text-muted); }
  .cp-arrow { color: var(--border); font-size: 0.75rem; }

  .hidden { display: none; }
  .empty { color: var(--text-muted); font-style: italic; font-size: 0.85rem; padding: 0.5rem 0; }

  @media (max-width: 768px) {
    body { padding: 1rem; }
    .summary-cards { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div class="header">
  <h1>SDLC Status Dashboard</h1>
  <span class="date">{{generated_date}}</span>
</div>

<div class="feature-tabs">
{{feature_tabs}}
</div>

{{feature_panels}}

<script>
function selectFeature(idx) {
  document.querySelectorAll('.ftab').forEach((t, i) => t.classList.toggle('active', i === idx));
  document.querySelectorAll('.fpanel').forEach((p, i) => p.classList.toggle('hidden', i !== idx));
}
</script>
</body>
</html>"""

FEATURE_PANEL = """
<div class="fpanel {{first_class}}">
  <p class="c-muted" style="margin-bottom:1.25rem;font-size:0.88rem">{{summary}}</p>
  {{blockers}}
  <div class="summary-cards">
    <div class="card"><div class="label">Current Phase</div><div class="value c-accent">{{current_phase}}</div></div>
    <div class="card"><div class="label">Tasks Done</div><div class="value {{task_color}}">{{tasks_done}} / {{tasks_total}}</div></div>
    <div class="card"><div class="label">Completion</div><div class="value {{pct_color}}">{{pct}}%</div></div>
    <div class="card"><div class="label">Re-enter At</div><div class="value c-accent">{{re_entry_point}}</div></div>
  </div>
  <div class="progress-bar-track"><div class="progress-bar-fill" style="width:{{pct}}%;background:{{bar_color}}"></div></div>
  <div class="progress-meta"><span>{{tasks_done}} completed</span><span>{{tasks_remaining}} remaining</span></div>

  <div class="section">
    <h3>Pipeline Progress</h3>
    <div class="pipeline-stages">{{pipeline_html}}</div>
  </div>

  {{task_section}}

  {{session_section}}
</div>"""


def chip(status: str) -> str:
    cls = status.replace(" ", "-")
    label = status if status != "not-started" else "\u2014"
    return f'<span class="chip chip-{cls}">{label}</span>'


def badge(status: str) -> str:
    cls = status.replace(" ", "-")
    return f'<span class="badge badge-{cls}">{status}</span>'


def render_pipeline(pipeline_rows: list[dict]) -> str:
    stages: dict[str, list[dict]] = {}
    for row in pipeline_rows:
        stages.setdefault(row["stage"], []).append(row)
    if not stages:
        return '<span class="empty">No pipeline data</span>'
    parts = []
    for stage_name, phases in stages.items():
        chips = "".join(chip(p["status"]) for p in phases)
        parts.append(
            f'<div class="pipeline-stage">'
            f'<div class="stage-label">{stage_name}</div>'
            f'<div class="pipeline-phases">{chips}</div>'
            f'</div>'
        )
    return '<span class="cp-arrow">&rsaquo;</span>'.join(parts)


def render_tasks(tasks: list[dict]) -> str:
    if not tasks:
        return ""
    rows = ""
    for t in tasks:
        completed = t.get("completed", "") or ""
        blocker = t.get("blocker", "") or ""
        blocker_cell = blocker if blocker else '<span class="c-muted">\u2014</span>'
        rows += (
            f"<tr>"
            f'<td style="font-weight:600;color:var(--text-muted)">{t["id"]}</td>'
            f"<td>{t['title']}</td>"
            f'<td><span class="size">{t.get("size", "")}</span></td>'
            f"<td>{badge(t['status'])}</td>"
            f'<td class="c-muted" style="font-size:0.78rem">{completed or "\u2014"}</td>'
            f"<td>{blocker_cell}</td>"
            f"</tr>"
        )
    return (
        '<div class="section"><h3>Tasks</h3>'
        '<table><thead><tr><th>ID</th><th>Title</th><th>Size</th><th>Status</th><th>Completed</th><th>Blocker</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


def render_sessions(sessions: list[dict]) -> str:
    if not sessions:
        return ""
    rows = ""
    for s in sessions:
        rows += (
            f"<tr>"
            f'<td class="session-date">{s["date"]}</td>'
            f"<td>{s['summary']}</td>"
            f'<td class="session-next">{s.get("next", "")}</td>'
            f"</tr>"
        )
    return (
        '<div class="section"><h3>Session Log</h3><div class="session-log">'
        '<table><thead><tr><th>Date</th><th>Summary</th><th>Next Step</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div></div>"
    )


def render_blockers(feature: dict) -> str:
    parts = ""
    if feature.get("blocker"):
        parts += (
            '<div class="blocker-banner">'
            '<span class="icon">!</span>'
            f'<div><div class="btitle">Feature Blocker</div>'
            f'<div class="bdesc">{feature["blocker"]}</div></div></div>'
        )
    for t in feature.get("tasks", []):
        if t.get("status") == "blocked" and t.get("blocker"):
            parts += (
                '<div class="blocker-banner">'
                '<span class="icon">!</span>'
                f'<div><div class="btitle">Task {t["id"]} Blocked</div>'
                f'<div class="bdesc">{t["blocker"]}</div></div></div>'
            )
    return parts


def render_feature(feature: dict, is_first: bool) -> str:
    done = sum(1 for t in feature["tasks"] if t["status"] == "done")
    total = len(feature["tasks"])
    pct = round((done / total) * 100) if total > 0 else 0
    has_blocked = any(t.get("status") == "blocked" for t in feature["tasks"])

    if has_blocked:
        bar_color = "var(--red)"
    elif pct == 100:
        bar_color = "var(--green)"
    else:
        bar_color = "var(--accent)"

    return (
        FEATURE_PANEL
        .replace("{{first_class}}", "" if is_first else "hidden")
        .replace("{{summary}}", feature.get("summary", ""))
        .replace("{{blockers}}", render_blockers(feature))
        .replace("{{current_phase}}", feature.get("current_phase", "\u2014"))
        .replace("{{re_entry_point}}", feature.get("re_entry_point", "\u2014"))
        .replace("{{tasks_done}}", str(done))
        .replace("{{tasks_total}}", str(total))
        .replace("{{tasks_remaining}}", str(total - done))
        .replace("{{pct}}", str(pct))
        .replace("{{task_color}}", "c-green" if pct == 100 else "c-blue")
        .replace("{{pct_color}}", "c-green" if pct == 100 else "c-yellow" if pct < 50 else "c-blue")
        .replace("{{bar_color}}", bar_color)
        .replace("{{pipeline_html}}", render_pipeline(feature.get("pipeline", [])))
        .replace("{{task_section}}", render_tasks(feature.get("tasks", [])))
        .replace("{{session_section}}", render_sessions(feature.get("sessions", [])))
    )


def render_tab(feature: dict, is_first: bool, idx: int) -> str:
    done = sum(1 for t in feature["tasks"] if t["status"] == "done")
    total = len(feature["tasks"])
    has_blocked = any(t.get("status") == "blocked" for t in feature["tasks"])
    dot = "c-red" if has_blocked else "c-green" if total > 0 and done == total else "c-yellow"
    active_cls = " active" if is_first else ""
    return (
        f'<div class="ftab{active_cls}" onclick="selectFeature({idx})">'
        f'<span class="{dot}">&bull;</span> '
        f'<span class="fid">{feature["id"]}</span> {feature["title"]}'
        f"</div>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render SDLC status dashboard from .sdlc/ directory")
    parser.add_argument("sdlc_dir", nargs="?", default=".sdlc", help="Path to .sdlc directory (default: .sdlc)")
    parser.add_argument("-o", "--output", default="-", help="Output HTML file path (default: stdout)")
    args = parser.parse_args()

    sdlc_path = Path(args.sdlc_dir)
    if not sdlc_path.exists():
        print(f"Error: {sdlc_path} does not exist", file=sys.stderr)
        sys.exit(1)

    features = collect_features(sdlc_path)
    if not features:
        print(f"No features found in {sdlc_path}/features/", file=sys.stderr)
        sys.exit(1)

    from datetime import date

    tabs_html = ""
    panels_html = ""
    for i, feat in enumerate(features):
        tabs_html += render_tab(feat, i == 0, i) + "\n"
        panels_html += render_feature(feat, i == 0) + "\n"

    html = (
        HTML_TEMPLATE
        .replace("{{generated_date}}", date.today().isoformat())
        .replace("{{feature_tabs}}", tabs_html)
        .replace("{{feature_panels}}", panels_html)
    )

    if args.output == "-":
        print(html)
    else:
        Path(args.output).write_text(html)
        print(f"Written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
