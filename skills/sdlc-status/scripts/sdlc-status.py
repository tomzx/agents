#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
#     "markdown",
#     "pymdown-extensions",
#     "structlog",
# ]
# ///
"""Render an SDLC status dashboard HTML page from .sdlc/ directory data."""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import structlog

import yaml


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def resolve_git_info() -> tuple[str, str, str]:
    script = Path(__file__).resolve()
    git_dir = script.parent
    while git_dir.parent != git_dir:
        if (git_dir / ".git").exists() or (git_dir / ".git").is_dir():
            repo_root = git_dir
            break
        git_dir = git_dir.parent
    else:
        return "", "", ""

    head_file = repo_root / ".git" / "HEAD"
    if not head_file.exists():
        return "", "", ""

    ref = head_file.read_text().strip()
    if ref.startswith("ref: "):
        ref_path = repo_root / ".git" / ref[5:]
        commit = ref_path.read_text().strip() if ref_path.exists() else ""
    else:
        commit = ref

    remote_file = repo_root / ".git" / "config"
    remote_url = ""
    if remote_file.exists():
        for line in remote_file.read_text().splitlines():
            if "url = " in line:
                url = line.split("url = ", 1)[1].strip()
                if url.endswith(".git"):
                    url = url[:-4]
                remote_url = url
                break

    rel_path = str(script.relative_to(repo_root))
    return remote_url, commit, rel_path


PHASE_ORDER: list[tuple[str, str, str | None]] = [
    ("Foundation", "requirements", "requirements.md"),
    ("Foundation", "existing-solutions", "existing-solutions.md"),
    ("Foundation", "codebase-analysis", "codebase-analysis.md"),
    ("Foundation", "feasibility", "feasibility.md"),
    ("Foundation", "specification", "specification.md"),
    ("Foundation", "plan", "plan.md"),
    ("Build", "implementation", None),
    ("Build", "testing", "tests.md"),
    ("Ship", "documentation", None),
]


def infer_pipeline_from_files(feature_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for stage, phase, fname in PHASE_ORDER:
        if fname:
            fpath = feature_dir / fname
            if fpath.exists():
                art_fm, _ = parse_frontmatter(fpath.read_text())
                status = art_fm.get("status", "done")
            else:
                status = "not-started"
        else:
            if phase == "implementation":
                tasks_dir = feature_dir / "tasks"
                if tasks_dir.exists() and any(tasks_dir.iterdir()):
                    status = "done"
                else:
                    status = "not-started"
            else:
                status = "not-started"
        rows.append({"stage": stage, "phase": phase, "status": status})
    return rows


def read_feature(feature_dir: Path) -> dict | None:
    log = structlog.get_logger()
    log.info("reading_feature", dir=feature_dir.name)
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
    file_contents: dict[str, str] = {}

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
                            "status": parts[2] if parts[2] not in ("—", "--") else "not-started",
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
    else:
        pipeline_rows = infer_pipeline_from_files(feature_dir)
        last_active = -1
        for i, row in enumerate(pipeline_rows):
            if row["status"] != "not-started":
                last_active = i
        if last_active >= 0:
            last_status = pipeline_rows[last_active]["status"]
            if last_status in ("done", "approved", "skipped"):
                if last_active + 1 < len(pipeline_rows):
                    current_phase = pipeline_rows[last_active + 1]["phase"]
                else:
                    current_phase = "complete"
            else:
                current_phase = pipeline_rows[last_active]["phase"]
        # Extract title from the most advanced artifact file with a title
        for _, _, fname in reversed(PHASE_ORDER):
            if fname and (feature_dir / fname).exists():
                art_fm, _ = parse_frontmatter((feature_dir / fname).read_text())
                t = art_fm.get("title") or ""
                if t:
                    title = t
                    break

    # Read phase file contents for inline display
    for _, phase, fname in PHASE_ORDER:
        if fname:
            fpath = feature_dir / fname
            if fpath.exists():
                _, content = parse_frontmatter(fpath.read_text())
                file_contents[phase] = content.strip()

    # Collect FR/NFR references from requirements for tooltips
    refs: dict[str, dict] = {}
    req_content = file_contents.get("requirements", "")
    if req_content:
        refs.update(parse_refs(req_content))

    # Collect open questions from phase files
    open_questions: dict[str, str] = {}
    for phase, content in file_contents.items():
        qs = parse_open_questions(content)
        if qs:
            open_questions[phase] = qs

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

    if not re_entry_point and pipeline_rows:
        for row in pipeline_rows:
            if row["status"] not in ("done", "approved", "skipped"):
                re_entry_point = row["phase"]
                break

    feature_dict = {
        "id": feature_dir.name.split("-")[0] + "-" + feature_dir.name.split("-")[1],
        "dir_name": feature_dir.name,
        "dir_path": str(feature_dir.resolve()),
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
        "file_contents": file_contents,
        "refs": refs,
        "open_questions": open_questions,
    }

    log.info(
        "feature_parsed",
        title=title,
        pipeline_phases=len(pipeline_rows),
        tasks=len(task_rows),
        sessions=len(sessions),
        files=len(file_contents),
        open_questions=len(open_questions),
    )
    return feature_dict


def collect_features(sdlc_dir: Path) -> list[dict]:
    log = structlog.get_logger()
    features_dir = sdlc_dir / "features"
    if not features_dir.exists():
        log.warning("features_dir_not_found", path=str(features_dir))
        return []
    features = []
    for d in sorted(features_dir.iterdir()):
        if d.is_dir() and d.name != "templates":
            feat = read_feature(d)
            if feat:
                features.append(feat)
                log.info("feature_loaded", id=feat["id"], title=feat["title"])
    log.info("features_collected", count=len(features))
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
  }
  h1 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0; }
  h3 { font-size: 0.8rem; font-weight: 600; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }

  .header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
  }
  .header h1 { color: var(--accent); }
  .header .date { color: var(--text-muted); font-size: 0.75rem; }

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
    font-size: 0.72rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    white-space: nowrap;
    font-weight: 500;
  }
  .chip-done { background: var(--green-dim); color: var(--green); }
  .chip-approved { background: var(--green-dim); color: var(--green); }
  .chip-in-progress { background: var(--yellow-dim); color: var(--yellow); }
  .chip-blocked { background: var(--red-dim); color: var(--red); }
  .chip-skipped { background: var(--gray-dim); color: var(--gray); text-decoration: line-through; }
  .chip-open-questions { background: var(--blue-dim); color: var(--blue); }
  .chip-vocabulary { background: var(--green-dim); color: var(--green); }
  .chip-not-started { background: var(--surface-alt); color: var(--text-muted); }
  .chip-draft { background: var(--blue-dim); color: var(--blue); }
  .chip-in-review { background: var(--yellow-dim); color: var(--yellow); }
  .chip-link { cursor: pointer; text-decoration: none; }
  .chip-link:hover { filter: brightness(1.3); }
  .chip-icon-wrap { position: relative; cursor: help; }
  .chip-icon-tip {
    visibility: hidden; opacity: 0; pointer-events: none;
    position: absolute; z-index: 100; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%);
    background: #1e1e2e; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 6px;
    padding: 0.35rem 0.6rem; min-width: max-content;
    font-size: 0.72rem; font-weight: 400; line-height: 1.3;
    box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    transition: opacity 0.12s ease;
  }
  .chip-icon-tip::after {
    content: ""; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
    border: 5px solid transparent; border-top-color: #45475a;
  }
  .chip-icon-wrap:hover .chip-icon-tip { visibility: visible; opacity: 1; }

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

  .layout { display: flex; gap: 1.5rem; align-items: flex-start; }
  .sidebar {
    flex: 0 0 220px;
    position: sticky;
    top: 2rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
  }
  .sidebar h3 { margin-bottom: 0.5rem; }
  .feature-list { display: flex; flex-direction: column; gap: 0.25rem; }
  .main { flex: 1; min-width: 0; }
  .ftab {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.4rem 0.65rem;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.82rem;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
    text-align: left;
    width: 100%;
  }
  .ftab:hover { border-color: var(--accent-dim); background: var(--surface-alt); color: var(--text); }
  .ftab.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); font-weight: 600; }
  .ftab .fid { font-weight: 600; flex-shrink: 0; }
  .ftab .ftitle { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .session-log { max-height: 220px; overflow-y: auto; }
  .session-date { white-space: nowrap; color: var(--text-muted); font-size: 0.78rem; }
  .session-next { color: var(--accent); font-size: 0.78rem; }

  .crit-path { display: flex; align-items: center; gap: 0.2rem; flex-wrap: wrap; margin-top: 0.5rem; }
  .cpn { display: inline-flex; align-items: center; padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 600; }
  .cpn-done { background: var(--green-dim); color: var(--green); }
  .cpn-in-progress { background: var(--blue-dim); color: var(--blue); }
  .cpn-blocked { background: var(--red-dim); color: var(--red); }
  .cpn-pending { background: var(--surface-alt); color: var(--text-muted); }
  .cp-arrow { color: var(--text-muted); font-size: 0.8rem; margin: 0 0.5rem; }

  .phase-detail {
    margin-top: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-alt);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.85rem;
    line-height: 1.7;
  }
  .phase-detail h2 { font-size: 1.1rem; margin: 0.75rem 0 0.5rem; color: var(--accent); }
  .phase-detail h3 { font-size: 0.95rem; margin: 0.5rem 0 0.25rem; }
  .phase-detail p { margin: 0.25rem 0; }
  .phase-detail ul, .phase-detail ol { margin: 0.25rem 0; padding-left: 1.25rem; }
  .phase-detail li { margin: 0.15rem 0; }
  .phase-detail code { background: var(--bg); padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.8rem; }
  .phase-detail pre { background: var(--bg); padding: 0.6rem; border-radius: 4px; overflow-x: auto; margin: 0.5rem 0; }
  .phase-detail pre code { background: none; padding: 0; }
  .phase-detail a { color: var(--accent); }
  .phase-detail table { border-collapse: collapse; margin: 0.5rem 0; font-size: 0.82rem; }
  .phase-detail th, .phase-detail td { border: 1px solid var(--border); padding: 0.35rem 0.65rem; text-align: left; }
  .phase-detail th { background: var(--surface); color: var(--text-muted); font-weight: 600; }
  .phase-detail input[type="checkbox"] { margin: 0 0.35rem 0 0; pointer-events: none; }
  .ref { color: var(--accent); cursor: help; border-bottom: 1px dotted var(--accent); position: relative; display: inline; }
  .ref .ref-tip {
    visibility: hidden; opacity: 0; pointer-events: none;
    position: absolute; z-index: 100; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%);
    background: #1e1e2e; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 6px;
    padding: 0.5rem 0.75rem; min-width: 220px; max-width: 360px;
    font-size: 0.78rem; font-weight: 400; line-height: 1.4;
    box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    transition: opacity 0.12s ease;
    white-space: normal;
  }
  .ref .ref-tip::after {
    content: ""; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
    border: 5px solid transparent; border-top-color: #45475a;
  }
  .ref:hover .ref-tip { visibility: visible; opacity: 1; }
  .ref-prio { display: inline-block; background: var(--accent); color: var(--bg); padding: 0.05rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 600; margin-bottom: 0.3rem; text-transform: uppercase; }
  .ref-prio-must { background: #e64553; }
  .ref-prio-should { background: #f9c74f; color: #1e1e2e; }
  .ref-prio-may { background: #4c9aff; }
  .ref .ref-prio { margin-bottom: 0; }
  .ref-desc { display: block; }

  .hidden { display: none; }
  .empty { color: var(--text-muted); font-style: italic; font-size: 0.85rem; padding: 0.5rem 0; }
  .oq-row { flex-basis: 100%; margin-top: 0.5rem; }
  .pipeline-stages-row { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 0; }
  .pipeline-stages > .chip-open-questions { margin-left: auto; }
  .oq-row .chip { font-size: 0.72rem; padding: 0.2rem 0.5rem; border-radius: 4px; white-space: nowrap; font-weight: 500; }
  .oq-group:last-child { margin-bottom: 0; }
  .oq-group h4 { margin: 0 0 0.25rem; font-size: 0.85rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em; }
  .oq-group ol { margin: 0.25rem 0; padding-left: 1.25rem; }
  .oq-group li { margin: 0.35rem 0; font-size: 0.85rem; line-height: 1.4; }
  .oq-list { margin: 0; padding: 0; list-style: none; }
  .oq-list li { padding: 0.35rem 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
  .oq-list li:last-child { border-bottom: none; }
  .oq-list li::before { content: "?"; color: var(--accent); font-weight: 700; margin-right: 0.5rem; }
  .footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.72rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center; }
  .footer a { color: var(--accent); }
  .footer .commit { font-family: monospace; }

  .legend { margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
  .legend-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.72rem; color: var(--text-muted); padding: 0.15rem 0; }
  .legend-chip {
    display: inline-block;
    font-size: 0.6rem;
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    font-weight: 500;
    white-space: nowrap;
    min-width: 3.5em;
    text-align: center;
  }

  .help-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--surface-alt);
    color: var(--text-muted);
    font-size: 0.65rem;
    font-weight: 700;
    cursor: help;
    margin-left: 0.35rem;
    vertical-align: middle;
    position: relative;
  }
  .help-icon:hover .help-tip {
    visibility: visible; opacity: 1;
  }
  .help-tip {
    visibility: hidden; opacity: 0; pointer-events: none;
    position: absolute;
    top: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: #1e1e2e; color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 0.6rem 0.75rem;
    white-space: nowrap;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    transition: opacity 0.12s ease;
  }
  .help-tip::after {
    content: ""; position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%);
    border: 5px solid transparent; border-bottom-color: #45475a;
  }
  .help-tip .legend-item { font-size: 0.75rem; gap: 0.45rem; display: flex; align-items: center; padding: 0.15rem 0; }
  .help-tip .legend-chip { font-size: 0.7rem; padding: 0.1rem 0.35rem; border-radius: 3px; font-weight: 500; }

  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }

  @media (max-width: 768px) {
    body { padding: 0.75rem; font-size: 0.9rem; }
    .header { flex-direction: column; align-items: flex-start; gap: 0.25rem; }
    .header .date { font-size: 0.7rem; }

    .layout { display: block; }
    .sidebar {
      flex: none;
      width: 100%;
      position: static;
      top: auto;
      padding: 0.75rem;
      margin-bottom: 1rem;
    }
    .sidebar h3 { margin-bottom: 0.4rem; }
    .feature-list {
      flex-direction: row;
      flex-wrap: nowrap;
      overflow-x: auto;
      gap: 0.4rem;
      padding-bottom: 0.25rem;
      -webkit-overflow-scrolling: touch;
    }
    .ftab {
      flex: 0 0 auto;
      width: auto;
      min-height: 44px;
      align-items: center;
      white-space: nowrap;
    }
    .ftab .ftitle { max-width: 60vw; }

    .summary-cards { grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
    .card { padding: 0.75rem 0.85rem; }
    .card .value { font-size: 1.15rem; }

    .section { padding: 0.85rem; }

    .pipeline-stages { flex-direction: column; align-items: stretch; flex-wrap: nowrap; gap: 0.6rem; }
    .pipeline-stages-row { display: flex; flex-direction: column; flex-wrap: nowrap; width: 100%; gap: 0.6rem; align-items: stretch; }
    .pipeline-stages-row .cp-arrow { display: none; }
    .pipeline-stage { width: 100%; }
    .pipeline-phases { gap: 0.35rem; }
    .chip { padding: 0.35rem 0.55rem; font-size: 0.75rem; }

    .progress-meta { font-size: 0.72rem; }

    .phase-detail { font-size: 0.82rem; padding: 0.65rem 0.75rem; overflow-wrap: break-word; word-break: break-word; }
    .phase-detail pre { max-width: 100%; overflow-x: auto; }

    .blocker-banner { padding: 0.55rem 0.7rem; }

    .footer { flex-direction: column; align-items: flex-start; gap: 0.25rem; }

    .session-log { max-height: 320px; }
  }
</style>
</head>
<body>
<div class="header">
  <h1>SDLC Status Dashboard</h1>
  <span class="date">{{generated_date}}</span>
</div>

<div class="layout">
  <div class="sidebar">
    <h3>Features</h3>
    <div class="feature-list">
      {{feature_tabs}}
    </div>
  </div>
  <div class="main">
    {{feature_panels}}
  </div>
</div>

<script>
function selectFeature(idx) {
  document.querySelectorAll('.ftab').forEach(function(t, i) { t.classList.toggle('active', i === idx); });
  document.querySelectorAll('.fpanel').forEach(function(p, i) { p.classList.toggle('hidden', i !== idx); });
  // Show first non-hidden phase detail for this feature
  var shown = false;
  document.querySelectorAll('.fpanel:not(.hidden) .phase-detail').forEach(function(d) {
    if (!shown) { d.classList.remove('hidden'); shown = true; }
    else { d.classList.add('hidden'); }
  });
  localStorage.setItem('sdlc_feature', idx);
}
function showPhase(featIdx, phase) {
  var el = document.getElementById('pd-' + featIdx + '-' + phase);
  if (!el) return;
  var isHidden = el.classList.contains('hidden');
  document.querySelectorAll('.fpanel:not(.hidden) .phase-detail').forEach(function(d) { d.classList.add('hidden'); });
  if (isHidden) {
    el.classList.remove('hidden');
    localStorage.setItem('sdlc_phase', featIdx + ':' + phase);
  } else {
    localStorage.removeItem('sdlc_phase');
  }
}
function restoreState() {
  var feat = localStorage.getItem('sdlc_feature');
  if (feat !== null) {
    document.querySelectorAll('.ftab').forEach(function(t, i) { t.classList.toggle('active', i === parseInt(feat, 10)); });
    document.querySelectorAll('.fpanel').forEach(function(p, i) { p.classList.toggle('hidden', i !== parseInt(feat, 10)); });
  }
  var phase = localStorage.getItem('sdlc_phase');
  if (phase !== null) {
    var parts = phase.split(':');
    if (parts.length === 2 && parts[0] === (feat || '0')) {
      document.querySelectorAll('.phase-detail').forEach(function(d) { d.classList.add('hidden'); });
      var el = document.getElementById('pd-' + parts[0] + '-' + parts[1]);
      if (el) { el.classList.remove('hidden'); }
    }
  }
}
document.addEventListener('DOMContentLoaded', restoreState);
</script>
{{footer}}
</body>
</html>"""


def parse_refs(content: str) -> dict[str, dict]:
    refs: dict[str, dict] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        if not re.search(r"(FR|NFR)-\d+", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        ref_id = cells[0]
        if not re.match(r"(FR|NFR)-\d+$", ref_id):
            continue
        if ref_id in refs:
            continue
        priority = cells[1]
        requirement = cells[3] if len(cells) >= 4 else cells[2]
        refs[ref_id] = {"priority": priority, "requirement": requirement}
    return refs


def badge_priorities_in_tables(content: str) -> str:
    lines = content.splitlines()
    result: list[str] = []
    in_ref_table = False
    for line in lines:
        stripped = line.strip()
        is_table_row = stripped.startswith("|") and stripped.endswith("|")
        has_ref_id = bool(re.search(r"(FR|NFR)-\d+", stripped))

        if has_ref_id and is_table_row:
            in_ref_table = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 3:
                priority = cells[1]
                prio_lower = priority.lower()
                if prio_lower in ("must", "should", "may"):
                    cells[1] = f'<span class="ref-prio ref-prio-{prio_lower}">{priority}</span>'
                    line = "| " + " | ".join(cells) + " |"
            result.append(line)
        elif in_ref_table and is_table_row:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 3:
                priority = cells[1]
                prio_lower = priority.lower()
                if prio_lower in ("must", "should", "may"):
                    cells[1] = f'<span class="ref-prio ref-prio-{prio_lower}">{priority}</span>'
                    line = "| " + " | ".join(cells) + " |"
            result.append(line)
        else:
            in_ref_table = False
            result.append(line)
    return "\n".join(result)


def parse_open_questions(content: str) -> str:
    m = re.search(r"## Open Questions\s*\n(.+?)(?=\n## |\Z)", content, re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def parse_vocabulary(filepath: Path) -> tuple[str, dict[str, str]]:
    if not filepath.exists():
        return "", {}
    _, content = parse_frontmatter(filepath.read_text())
    refs: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        term = cells[0]
        if term in ("Term", "Abbreviation", "---"):
            continue
        definition = cells[1]
        refs[term] = definition
    return content.strip(), refs


FEATURE_PANEL = """
<div class="fpanel {{first_class}}">
  <p class="c-muted" style="margin-bottom:1.25rem;font-size:0.88rem">{{summary}}</p>
  {{blockers}}
  <div class="summary-cards">
    <div class="card"><div class="label">Current Phase</div><div class="value c-accent">{{current_phase}}</div></div>
    <div class="card"><div class="label">{{tasks_label}}</div><div class="value {{task_color}}">{{tasks_done}} / {{tasks_total}}</div></div>
    <div class="card"><div class="label">Completion</div><div class="value {{pct_color}}">{{pct}}%</div></div>
    <div class="card"><div class="label">Re-enter At</div><div class="value c-accent">{{re_entry_point}}</div></div>
  </div>
  <div class="progress-bar-track"><div class="progress-bar-fill" style="width:{{pct}}%;background:{{bar_color}}"></div></div>
  <div class="progress-meta"><span>{{tasks_done}} completed</span><span>{{tasks_remaining}} remaining</span></div>

  <div class="section">
    <h3>Pipeline Progress <span class="help-icon">?<span class="help-tip"><div class="legend-item"><span class="legend-chip chip-not-started">⚪ not started</span> not yet begun</div><div class="legend-item"><span class="legend-chip chip-draft">✏️ draft</span> initial version</div><div class="legend-item"><span class="legend-chip chip-in-review">🔍 in review</span> under review</div><div class="legend-item"><span class="legend-chip chip-in-progress">🚧 in progress</span> actively worked on</div><div class="legend-item"><span class="legend-chip chip-blocked">⛔ blocked</span> waiting on dependency</div><div class="legend-item"><span class="legend-chip chip-done">✅ done</span> completed</div><div class="legend-item"><span class="legend-chip chip-skipped">⏭️ skipped</span> not applicable</div></span></span></h3>
    <div class="pipeline-stages">{{pipeline_html}}</div>
    {{phase_details}}
  </div>

  {{task_section}}

  {{session_section}}
</div>"""




def badge(status: str) -> str:
    cls = status.replace(" ", "-")
    return f'<span class="badge badge-{cls}">{status}</span>'


def render_markdown(text: str) -> str:
    if not text:
        return ""
    import markdown as md
    return md.markdown(text, extensions=["extra", "pymdownx.tasklist"])


def wrap_tables(html: str) -> str:
    if not html:
        return html
    return re.sub(
        r"(<table\b.*?</table>)",
        r'<div class="table-wrap">\1</div>',
        html,
        flags=re.DOTALL,
    )


def annotate_refs(html: str, refs: dict[str, dict]) -> str:
    if not refs:
        return html

    def repl(m: re.Match) -> str:
        ref_id = m.group(0)
        info = refs.get(ref_id)
        if info:
            prio = info["priority"]
            req = info["requirement"].replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
            prio_class = f"ref-prio-{prio.lower()}"
            return (
                f'<span class="ref">'
                f'<span class="ref-label">{ref_id}</span>'
                f'<span class="ref-tip">'
                f'<span class="ref-prio {prio_class}">{prio}</span>'
                f'<span class="ref-desc">{req}</span>'
                f'</span>'
                f'</span>'
            )
        return ref_id

    return re.sub(r"(FR|NFR)-\d+", repl, html)


def annotate_vocab_refs(html: str, vocab_refs: dict[str, str]) -> str:
    if not vocab_refs:
        return html
    terms = sorted(vocab_refs, key=len, reverse=True)
    escaped = [re.escape(t) for t in terms]
    pattern = r"\b(" + "|".join(escaped) + r")\b"

    def repl(m: re.Match) -> str:
        term = m.group(0)
        definition = vocab_refs[term].replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<span class="ref"><span class="ref-label">{term}</span><span class="ref-tip">{definition}</span></span>'

    return re.sub(pattern, repl, html)


STATUS_ICONS = {
    "done": "\u2705",
    "approved": "\u2705",
    "in-progress": "\U0001f6a7",
    "in-review": "\U0001f50d",
    "draft": "\u270f\ufe0f",
    "blocked": "\u26d4",
    "skipped": "\u23ed\ufe0f",
    "not-started": "\u26aa",
    "open-questions": "\u2753",
    "vocabulary": "\U0001f4d6",
}

STATUS_DESCRIPTIONS: dict[str, str] = {
    "not-started": "not yet begun",
    "draft": "initial version",
    "in-review": "under review",
    "in-progress": "actively worked on",
    "blocked": "waiting on dependency",
    "done": "completed",
    "approved": "completed",
    "skipped": "not applicable",
    "open-questions": "open questions",
}

PHASE_FILE: dict[str, str | None] = {
    "feasibility": "feasibility.md",
    "requirements": "requirements.md",
    "existing-solutions": "existing-solutions.md",
    "codebase-analysis": "codebase-analysis.md",
    "specification": "specification.md",
    "plan": "plan.md",
    "implementation": None,
    "testing": "tests.md",
    "documentation": None,
}


def chip(phase: str, status: str, has_content: bool, feat_idx: int = 0) -> str:
    cls = status.replace(" ", "-")
    icon = STATUS_ICONS.get(status, "")
    desc = STATUS_DESCRIPTIONS.get(status, "")
    label = status.replace("-", " ").title()
    icon_wrapper = f'<span class="chip-icon-wrap">{icon}<span class="chip-icon-tip">{label}: {desc}</span></span>' if icon else ""
    inner = f"{icon_wrapper} {phase}" if icon else phase
    if has_content:
        return f'<span class="chip chip-{cls} chip-link" onclick="showPhase({feat_idx},\'{phase}\')">{inner}</span>'
    return f'<span class="chip chip-{cls}">{inner}</span>'


def render_pipeline(pipeline_rows: list[dict], file_contents: dict[str, str], open_questions: dict[str, str], has_vocab: bool = False, feat_idx: int = 0) -> str:
    stages: dict[str, list[dict]] = {}
    for row in pipeline_rows:
        stages.setdefault(row["stage"], []).append(row)
    if not stages:
        return '<span class="empty">No pipeline data</span>'
    parts = []
    for stage_name, phases in stages.items():
        chips = "".join(chip(p["phase"], p["status"], p["phase"] in file_contents, feat_idx) for p in phases)
        parts.append(
            f'<div class="pipeline-stage">'
            f'<div class="stage-label">{stage_name}</div>'
            f'<div class="pipeline-phases">{chips}</div>'
            f'</div>'
        )
    # Append Open Questions and Vocabulary chips
    extra_chips = ""
    if open_questions:
        cls = "chip-open-questions chip-link"
        icon = STATUS_ICONS.get("open-questions", "")
        extra_chips += f'<span class="chip {cls}" onclick="showPhase({feat_idx},\'open-questions\')">{icon} Open Questions</span>'
    if has_vocab:
        cls = "chip-vocabulary chip-link"
        icon = STATUS_ICONS.get("vocabulary", "")
        extra_chips += f'<span class="chip {cls}" onclick="showPhase({feat_idx},\'vocabulary\')">{icon} Vocabulary</span>'
    stages_html = '<span class="pipeline-stages-row">' + '<span class="cp-arrow">&rsaquo;</span>'.join(parts) + '</span>'
    return stages_html + extra_chips


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
        '<div class="table-wrap">'
        '<table><thead><tr><th>ID</th><th>Title</th><th>Size</th><th>Status</th><th>Completed</th><th>Blocker</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div></div>"
    )


def render_questions(questions: dict[str, str]) -> str:
    if not questions:
        return ""
    items = ""
    for phase, section in questions.items():
        rendered = render_markdown(section)
        items += f'<div class="oq-group"><h4>{phase}</h4>{rendered}</div>'
    return items


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
        '<div class="table-wrap"><table><thead><tr><th>Date</th><th>Summary</th><th>Next Step</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div></div></div>"
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


def render_feature(feature: dict, is_first: bool, feat_idx: int = 0) -> str:
    tasks = feature.get("tasks", [])
    pipeline = feature.get("pipeline", [])

    if tasks:
        done = sum(1 for t in tasks if t["status"] == "done")
        total = len(tasks)
        has_blocked = any(t.get("status") == "blocked" for t in tasks)
        label = "Tasks Done"
    else:
        done = sum(1 for p in pipeline if p["status"] in ("done", "approved"))
        total = len(pipeline)
        has_blocked = any(p["status"] == "blocked" for p in pipeline)
        label = "Phases Done"

    pct = round((done / total) * 100) if total > 0 else 0

    if has_blocked:
        bar_color = "var(--red)"
    elif pct == 100:
        bar_color = "var(--green)"
    else:
        bar_color = "var(--accent)"

    fc = feature.get("file_contents", {})
    refs = feature.get("refs", {})
    open_questions = feature.get("open_questions", {})
    vocab_content = feature.get("vocab_content", "")
    vocab_refs = feature.get("vocab_refs", {})

    # Find first phase with status != "not-started" to auto-expand
    first_active = None
    for row in pipeline:
        if row["status"] != "not-started" and row["phase"] in fc:
            first_active = row["phase"]
            break

    phase_details = ""
    for phase, content in fc.items():
        rendered = annotate_vocab_refs(annotate_refs(render_markdown(badge_priorities_in_tables(content)), refs), vocab_refs)
        rendered = wrap_tables(rendered)
        cls = "" if phase == first_active else "hidden"
        phase_details += f'<div id="pd-{feat_idx}-{phase}" class="phase-detail {cls}">{rendered}</div>'

    # Generate open questions detail
    oq_rendered = render_questions(open_questions) if open_questions else ""
    oq_rendered = wrap_tables(oq_rendered)
    phase_details += f'<div id="pd-{feat_idx}-open-questions" class="phase-detail hidden">{oq_rendered}</div>'

    # Generate vocabulary detail
    if vocab_content:
        vocab_rendered = annotate_vocab_refs(render_markdown(vocab_content), vocab_refs)
        vocab_rendered = wrap_tables(vocab_rendered)
        phase_details += f'<div id="pd-{feat_idx}-vocabulary" class="phase-detail hidden">{vocab_rendered}</div>'

    return (
        FEATURE_PANEL
        .replace("{{first_class}}", "" if is_first else "hidden")
        .replace("{{summary}}", feature.get("summary", ""))
        .replace("{{blockers}}", render_blockers(feature))
        .replace("{{current_phase}}", feature.get("current_phase", "\u2014"))
        .replace("{{re_entry_point}}", feature.get("re_entry_point", "\u2014"))
        .replace("{{tasks_label}}", label)
        .replace("{{tasks_done}}", str(done))
        .replace("{{tasks_total}}", str(total))
        .replace("{{tasks_remaining}}", str(total - done))
        .replace("{{pct}}", str(pct))
        .replace("{{task_color}}", "c-green" if pct == 100 else "c-blue")
        .replace("{{pct_color}}", "c-green" if pct == 100 else "c-yellow" if pct < 50 else "c-blue")
        .replace("{{bar_color}}", bar_color)
        .replace("{{pipeline_html}}", render_pipeline(feature.get("pipeline", []), fc, open_questions, bool(vocab_content), feat_idx))
        .replace("{{phase_details}}", phase_details)
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
        f'<span class="fid">{feature["id"]}</span>'
        f'<span class="ftitle">{feature["title"]}</span>'
        f"</div>"
    )


def build_footer() -> str:
    remote, commit, rel_path = resolve_git_info()
    if not remote or not commit:
        return ""
    blob_url = f"{remote}/blob/{commit}/{rel_path}"
    return (
        '<div class="footer">'
        f'<span>Generated by <a href="{blob_url}">{rel_path}</a></span>'
        f'<span class="commit">{commit[:10]}</span>'
        "</div>"
    )


def main() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO, stream=sys.stderr)
    log = structlog.get_logger()

    parser = argparse.ArgumentParser(description="Render SDLC status dashboard from .sdlc/ directory")
    parser.add_argument("sdlc_dir", nargs="?", default=".sdlc", help="Path to .sdlc directory (default: .sdlc)")
    parser.add_argument("-o", "--output", default="-", help="Output HTML file path (default: stdout)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress logging")
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    sdlc_path = Path(args.sdlc_dir)
    if not sdlc_path.exists():
        log.error("sdlc_dir_not_found", path=str(sdlc_path))
        print(f"Error: {sdlc_path} does not exist", file=sys.stderr)
        sys.exit(1)
    log.info("reading_sdlc_dir", path=str(sdlc_path))

    features = collect_features(sdlc_path)
    if not features:
        log.warning("no_features_found", path=str(sdlc_path / "features"))
        print(f"No features found in {sdlc_path}/features/", file=sys.stderr)
        sys.exit(1)
    log.info("features_found", count=len(features), names=[f["id"] for f in features])

    # Read project-level vocabulary
    vocab_path = sdlc_path / "context" / "vocabulary.md"
    vocab_content, vocab_refs = parse_vocabulary(vocab_path)
    if vocab_content:
        log.info("vocabulary_loaded", path=str(vocab_path), terms=len(vocab_refs))
    else:
        log.info("no_vocabulary_found", path=str(vocab_path))

    tabs_html = ""
    panels_html = ""
    for i, feat in enumerate(features):
        feat["vocab_content"] = vocab_content
        feat["vocab_refs"] = vocab_refs
        tabs_html += render_tab(feat, i == 0, i) + "\n"
        panels_html += render_feature(feat, i == 0, i) + "\n"

    from datetime import datetime
    now = datetime.now().astimezone()
    tz = now.strftime("%z")
    generated = now.strftime("%Y-%m-%d %H:%M:%S ") + tz[:3] + ":" + tz[3:]

    tabs_html = ""
    panels_html = ""
    for i, feat in enumerate(features):
        tabs_html += render_tab(feat, i == 0, i) + "\n"
        panels_html += render_feature(feat, i == 0, i) + "\n"

    html = (
        HTML_TEMPLATE
        .replace("{{generated_date}}", generated)
        .replace("{{feature_tabs}}", tabs_html)
        .replace("{{feature_panels}}", panels_html)
        .replace("{{footer}}", build_footer())
    )

    if args.output == "-":
        print(html)
    else:
        Path(args.output).write_text(html)
        print(f"Written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
