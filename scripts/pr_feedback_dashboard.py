# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn",
#   "pyyaml",
#   "markdown",
# ]
# ///
"""Dashboard for triaging PR review feedback.

Scans $HOME/.sdlc/*/pull-requests/*/feedback/*.md files written by the
triage-pr-feedback skill, renders them as a control panel, and lets you record
an implement / decline / defer decision into each file's frontmatter (the same
keys that skill and handle-pr-reviewer-feedback consume).

Run:
    uv run scripts/pr_feedback_dashboard.py
    uv run scripts/pr_feedback_dashboard.py --dir ~/.sdlc --port 8787
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

import markdown as md
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

SECTION_ORDER = [
    "Comment",
    "Analysis",
    "Recommended action",
    "Suggested reply",
    "Suggested change",
]

RECOMMENDATION_COLORS = {
    "implement": "#3fb950",
    "reject": "#f85149",
    "clarify": "#d29922",
    "no-action": "#8b949e",
}

DECISION_COLORS = {
    "implement": "#3fb950",
    "decline": "#f85149",
    "defer": "#d29922",
}

_frontmatter_re = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
_fence_re = re.compile(r"^---\s*$")


@dataclass
class FeedbackItem:
    feedback_id: str
    kind: str
    repo: str
    pr: str
    author: str
    created_at: str
    head_commit: str
    analyzed_at: str
    recommendation: str
    confidence: str
    session_link: str
    decision: str | None
    decided_at: str | None
    title: str
    path: str
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return self.decision or "pending"


def _render_md(text: str) -> str:
    return md.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists", "nl2br"],
    )


def _split_sections(body: str) -> tuple[str, dict[str, str]]:
    title = ""
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return title, sections


def parse_feedback(path: Path) -> FeedbackItem | None:
    text = path.read_text(encoding="utf-8")
    m = _frontmatter_re.match(text)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    title, sections = _split_sections(m.group(2))
    return FeedbackItem(
        feedback_id=str(data.get("feedback_id") or path.stem),
        kind=str(data.get("kind") or ""),
        repo=str(data.get("repo") or ""),
        pr=str(data.get("pr") or ""),
        author=str(data.get("author") or ""),
        created_at=str(data.get("created_at") or ""),
        head_commit=str(data.get("head_commit") or ""),
        analyzed_at=str(data.get("analyzed_at") or ""),
        recommendation=str(data.get("recommendation") or ""),
        confidence=str(data.get("confidence") or ""),
        session_link=str(data.get("session_link") or ""),
        decision=(str(data["decision"]) if data.get("decision") else None),
        decided_at=(str(data["decided_at"]) if data.get("decided_at") else None),
        title=title or path.stem,
        path=str(path),
        sections=sections,
    )


def discover(root: Path) -> list[FeedbackItem]:
    items: list[FeedbackItem] = []
    for path in sorted(root.glob("**/pull-requests/*/feedback/*.md")):
        if path.name.startswith("."):
            continue
        item = parse_feedback(path)
        if item is not None:
            items.append(item)

    def sort_key(it: FeedbackItem):
        return (
            0 if it.decision is None else 1,
            it.repo,
            int(it.pr) if it.pr.isdigit() else 0,
            it.created_at,
            it.feedback_id,
        )

    items.sort(key=sort_key)
    return items


def find_item(root: Path, feedback_id: str) -> Path:
    for path in root.glob("**/pull-requests/*/feedback/*.md"):
        if path.stem == feedback_id:
            return path
    raise HTTPException(status_code=404, detail=f"feedback {feedback_id} not found")


def write_decision(path: Path, decision: str | None) -> None:
    text = path.read_text(encoding="utf-8")
    m = _frontmatter_re.match(text)
    if not m:
        raise HTTPException(status_code=422, detail="file has no frontmatter")
    fm, rest = m.group(1), m.group(2)

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[str] = []
    seen_decision = False
    seen_decided = False
    for line in fm.splitlines():
        if re.match(r"^decision\s*:", line):
            seen_decision = True
            if decision:
                out.append(f"decision: {decision}")
        elif re.match(r"^decided_at\s*:", line):
            seen_decided = True
            if decision:
                out.append(f"decided_at: {now}")
        else:
            out.append(line)
    if decision:
        if not seen_decision:
            out.append(f"decision: {decision}")
        if not seen_decided:
            out.append(f"decided_at: {now}")

    new_text = "---\n" + "\n".join(out) + "\n---\n" + rest
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as fh:
        fh.write(new_text)
        tmp = Path(fh.name)
    tmp.replace(path)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower() or "group"


def _sections_html(item: FeedbackItem) -> str:
    ordered = [s for s in SECTION_ORDER if s in item.sections]
    ordered += [s for s in item.sections if s not in SECTION_ORDER]
    blocks = []
    for i, name in enumerate(ordered):
        body = item.sections[name]
        content = _render_md(body)
        open_attr = " open" if i == 0 else ""
        extra = ""
        if name == "Suggested reply":
            extra = (
                '<button class="copy-btn" type="button" '
                f'data-copy-target="reply-{esc(item.feedback_id)}">copy</button>'
            )
        blocks.append(
            f'<details class="section"{open_attr}>'
            f"<summary>{esc(name)}{extra}</summary>"
            f'<div class="section-body" id="reply-{esc(item.feedback_id)}">{content}</div>'
            "</details>"
        )
    return "\n".join(blocks)


def _card(item: FeedbackItem) -> str:
    rec = item.recommendation or "none"
    rec_color = RECOMMENDATION_COLORS.get(rec, "#8b949e")
    decision = item.decision
    decision_color = DECISION_COLORS.get(decision or "", "#8b949e")
    thread = ""
    m = re.search(r"\[thread\]\((https?://[^)]+)\)", item.sections.get("Comment", ""))
    if m:
        thread = m.group(1)

    pr_url = ""
    if item.repo and item.pr:
        pr_url = f"https://github.com/{item.repo}/pull/{item.pr}"

    search_blob = (
        f"{item.title} {item.repo} {item.pr} {item.author} {item.kind} {item.recommendation}"
    ).lower()

    def btn(value: str, label: str) -> str:
        active = " active" if (item.decision or "pending") == value else ""
        return (
            f'<button type="button" class="decision-btn {value}{active}" '
            f'data-decision="{value}" data-id="{esc(item.feedback_id)}">{esc(label)}</button>'
        )

    reply_md = item.sections.get("Suggested reply", "")
    reply_text = _render_md(reply_md) if reply_md else ""

    return f"""
<article class="card"
  data-id="{esc(item.feedback_id)}"
  data-repo="{esc(item.repo)}"
  data-pr="{esc(item.pr)}"
  data-author="{esc(item.author)}"
  data-rec="{esc(item.recommendation)}"
  data-status="{esc(item.status)}"
  data-title="{esc(item.title)}"
  data-date="{esc(item.created_at)}"
  data-confidence="{esc(item.confidence)}"
  data-kind="{esc(item.kind)}"
  data-search="{esc(search_blob)}"
  style="--rec-color:{rec_color};--decision-color:{decision_color}">
  <div class="card-rail"></div>
  <div class="card-main">
    <div class="card-top">
      <div class="pills">
        <span class="pill rec" style="--c:{rec_color}">{esc(item.recommendation or "n/a")}</span>
        <span class="pill confidence">{esc(item.confidence or "?")} confidence</span>
        <span class="pill kind">{esc(item.kind or "comment")}</span>
        <span class="pill decision" data-role="decision-pill" style="--c:{decision_color}">{esc(item.status)}</span>
      </div>
      <div class="card-when">{esc((item.created_at or "")[:10])}</div>
    </div>
    <h2>{esc(item.title)}</h2>
    <div class="card-meta">
      <a href="{esc(pr_url)}" target="_blank" rel="noopener">{esc(item.repo)}#{esc(item.pr)}</a>
      <span>·</span><span class="author">{esc(item.author)}</span>
      <span>·</span><span class="id">{esc(item.feedback_id)}</span>
    </div>
    <div class="actions">
      {btn("implement", "Implement")}
      {btn("decline", "Decline")}
      {btn("defer", "Defer")}
      {btn("pending", "Reset")}
      <span class="spacer"></span>
      {f'<a class="link-btn" href="{esc(thread)}" target="_blank" rel="noopener">Thread</a>' if thread else ""}
      {f'<a class="link-btn" href="{esc(pr_url)}" target="_blank" rel="noopener">PR</a>' if pr_url else ""}
      <a class="link-btn" href="file://{esc(item.path)}">Analysis</a>
    </div>
    <div class="sections">{_sections_html(item)}</div>
    <pre class="reply-source" hidden>{esc(reply_text)}</pre>
  </div>
</article>"""


def render_page(items: list[FeedbackItem], root: Path) -> str:
    repos = sorted({i.repo for i in items if i.repo})
    repo_options = "".join(f'<option value="{esc(r)}">{esc(r)}</option>' for r in repos)
    author_counts: dict[str, int] = {}
    for i in items:
        if i.author:
            author_counts[i.author] = author_counts.get(i.author, 0) + 1
    author_checkboxes = "".join(
        f'<label class="menu-item"><input type="checkbox" '
        f'value="{esc(a)}" data-author-box>'
        f'<span>{esc(a)}</span><span class="menu-count">{author_counts[a]}</span></label>'
        for a in sorted(author_counts)
    )
    counts = {"pending": 0, "implement": 0, "decline": 0, "defer": 0}
    for i in items:
        counts[i.status] = counts.get(i.status, 0) + 1
    cards = "\n".join(_card(i) for i in items) or (
        f'<p class="empty">No feedback files found under <code>{esc(root)}</code>.</p>'
    )
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PR Feedback Dashboard</title>
<style>
:root {{
  --bg:#0d1117; --panel:#161b22; --panel2:#1c2128; --border:#30363d;
  --fg:#e6edf3; --muted:#8b949e; --accent:#58a6ff;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--bg); color:var(--fg);
  font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
}}
header.top {{
  position:sticky; top:0; z-index:20; background:rgba(13,17,23,.95);
  backdrop-filter:blur(8px); border-bottom:1px solid var(--border);
  padding:14px 20px;
}}
.top-row {{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }}
h1 {{ font-size:17px; margin:0; font-weight:600; }}
.top-row .root {{ color:var(--muted); font-size:12px; font-family:ui-monospace,monospace; }}
.stats {{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }}
.stat {{
  background:var(--panel); border:1px solid var(--border); border-radius:8px;
  padding:6px 12px; min-width:76px;
}}
.stat .n {{ font-size:18px; font-weight:700; }}
.stat .l {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }}
.stat.pending .n {{ color:#d29922; }} .stat.implement .n {{ color:#3fb950; }}
.stat.decline .n {{ color:#f85149; }} .stat.defer .n {{ color:#d29922; }}
.controls {{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }}
.controls input, .controls select {{
  background:var(--panel); color:var(--fg); border:1px solid var(--border);
  border-radius:6px; padding:7px 10px; font-size:13px;
}}
.controls input {{ flex:1; min-width:200px; }}
.filter-menu {{ position:relative; }}
.filter-menu > summary {{
  list-style:none; cursor:pointer; background:var(--panel); color:var(--fg);
  border:1px solid var(--border); border-radius:6px; padding:7px 10px;
  font-size:13px; user-select:none;
}}
.filter-menu > summary::-webkit-details-marker {{ display:none; }}
.filter-menu > summary::after {{ content:" \\25BE"; color:var(--muted); }}
.filter-menu-body {{
  position:absolute; top:calc(100% + 4px); left:0; z-index:30; min-width:220px;
  max-height:320px; overflow:auto; background:var(--panel);
  border:1px solid var(--border); border-radius:8px; padding:8px;
  box-shadow:0 8px 24px rgba(0,0,0,.5);
}}
.menu-actions {{ display:flex; gap:10px; padding:2px 6px 8px; }}
.menu-link {{ background:none; border:0; color:var(--accent); font-size:12px; padding:0; }}
.menu-item {{
  display:flex; align-items:center; gap:8px; padding:5px 6px;
  border-radius:5px; font-size:13px; cursor:pointer;
}}
.menu-item:hover {{ background:var(--panel2); }}
.menu-item .menu-count {{
  margin-left:auto; color:var(--muted); font-size:12px;
  font-variant-numeric:tabular-nums;
}}
.menu-item input {{
  flex:none; min-width:0; width:15px; height:15px; margin:0; padding:0;
  background:none; border:0; accent-color:var(--accent);
}}
button {{ cursor:pointer; font-size:13px; }}
.reload-btn {{
  background:var(--accent); color:#04121f; border:0; border-radius:6px;
  padding:7px 12px; font-weight:600;
}}
.layout {{ display:flex; align-items:flex-start; }}
.sidebar {{
  position:sticky; top:var(--header-h,0px); flex:none; width:250px;
  height:calc(100vh - var(--header-h,0px)); overflow-y:auto;
  padding:16px 12px; border-right:1px solid var(--border);
  background:var(--panel);
}}
.sidebar-title {{
  font-size:11px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); margin:0 6px 8px;
}}
.nav-item {{
  display:flex; align-items:center; gap:8px; padding:6px 8px;
  border-radius:6px; text-decoration:none; color:var(--muted);
  font-size:12.5px; margin-bottom:2px;
}}
.nav-item:hover {{ background:var(--panel2); color:var(--fg); }}
.nav-item.active {{ background:var(--panel2); color:var(--fg); }}
.nav-item .nav-label {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.nav-item .nav-count {{
  margin-left:auto; flex:none; font-size:11px; color:var(--muted);
  font-variant-numeric:tabular-nums;
}}
main {{ padding:20px 24px; flex:1; min-width:0; max-width:1100px; }}
.group {{ margin-bottom:30px; }}
.group + .group {{ border-top:1px solid var(--border); padding-top:26px; }}
.group-head {{
  display:flex; align-items:baseline; gap:10px; margin-bottom:14px;
  scroll-margin-top:calc(var(--header-h,0px) + 12px);
}}
.group-head > a, .group-head > span:first-child {{
  color:var(--fg); font-weight:600; font-size:15px; text-decoration:none;
}}
.group-head > a:hover {{ color:var(--accent); }}
.group-head .group-count {{ color:var(--muted); font-size:12px; }}
.card {{
  display:flex; background:var(--panel); border:1px solid var(--border);
  border-radius:10px; margin-bottom:16px; overflow:hidden;
}}
.card-rail {{ width:4px; background:var(--decision-color); flex:none; }}
.card[data-status="pending"] .card-rail {{
  background:var(--rec-color);
  background:linear-gradient(180deg,var(--rec-color),var(--rec-color) 55%,transparent 55%);
}}
.card-main {{ padding:14px 16px; flex:1; min-width:0; }}
.card-top {{ display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }}
.pills {{ display:flex; gap:6px; flex-wrap:wrap; }}
.pill {{
  font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid var(--border);
  color:var(--muted); text-transform:lowercase;
}}
.pill.rec, .pill.decision {{ color:var(--c); border-color:var(--c); font-weight:600; }}
.pill.decision {{ text-transform:uppercase; letter-spacing:.04em; }}
.card-when {{ color:var(--muted); font-size:12px; white-space:nowrap; }}
h2 {{ font-size:15px; margin:10px 0 4px; line-height:1.4; }}
.card-meta {{ color:var(--muted); font-size:12px; display:flex; gap:6px; flex-wrap:wrap; }}
.card-meta a {{ color:var(--accent); text-decoration:none; }}
.card-meta .id {{ font-family:ui-monospace,monospace; }}
.actions {{ display:flex; gap:6px; align-items:center; margin:12px 0; flex-wrap:wrap; }}
.actions .spacer {{ flex:1; }}
.decision-btn {{
  background:var(--panel2); color:var(--fg); border:1px solid var(--border);
  border-radius:6px; padding:5px 11px;
}}
.decision-btn:hover {{ border-color:#8b949e; }}
.decision-btn.implement.active {{ background:#3fb950; color:#04120a; border-color:#3fb950; }}
.decision-btn.decline.active {{ background:#f85149; color:#1a0503; border-color:#f85149; }}
.decision-btn.defer.active {{ background:#d29922; color:#1a1305; border-color:#d29922; }}
.decision-btn.pending.active {{ background:#30363d; color:var(--fg); }}
.link-btn {{
  color:var(--muted); border:1px solid var(--border); border-radius:6px;
  padding:5px 10px; text-decoration:none; font-size:12px;
}}
.link-btn:hover {{ color:var(--fg); border-color:#8b949e; }}
details.section {{ border-top:1px solid var(--border); padding:8px 0 2px; }}
details.section summary {{
  cursor:pointer; font-weight:600; font-size:13px; color:#c9d1d9;
  display:flex; align-items:center; gap:8px; list-style:none;
}}
details.section summary::-webkit-details-marker {{ display:none; }}
details.section summary::before {{ content:"\\25B8"; color:var(--muted); font-size:11px; }}
details.section[open] summary::before {{ content:"\\25BE"; }}
.copy-btn {{
  margin-left:auto; background:transparent; border:1px solid var(--border);
  color:var(--muted); border-radius:5px; font-size:11px; padding:1px 7px;
}}
.section-body {{ padding:8px 0 10px 14px; }}
.section-body :first-child {{ margin-top:0; }}
.section-body h1, .section-body h2, .section-body h3 {{ font-size:13px; }}
.section-body blockquote {{
  margin:6px 0; padding:2px 0 2px 12px; border-left:3px solid #3d444d;
  color:#c9d1d9;
}}
.section-body pre {{
  background:#0b0f14; border:1px solid var(--border); border-radius:6px;
  padding:10px; overflow:auto; font-size:12px;
}}
.section-body code {{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px;
  background:#0b0f14; padding:1px 4px; border-radius:4px;
}}
.section-body pre code {{ background:none; padding:0; }}
.section-body table {{ border-collapse:collapse; }}
.section-body th, .section-body td {{ border:1px solid var(--border); padding:4px 8px; }}
.section-body a {{ color:var(--accent); }}
.empty {{ color:var(--muted); padding:40px; text-align:center; }}
.hidden {{ display:none !important; }}
.toast {{
  position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
  background:#238636; color:#fff; padding:9px 16px; border-radius:8px;
  opacity:0; transition:opacity .2s; pointer-events:none; font-size:13px;
}}
.toast.show {{ opacity:1; }}
</style>
</head>
<body>
<header class="top">
  <div class="top-row">
    <h1>PR Feedback Dashboard</h1>
    <span class="root">{esc(root)}</span>
    <span class="root" style="margin-left:auto">generated {esc(generated)}</span>
  </div>
  <div class="stats" id="stats">
    <div class="stat pending"><div class="n" data-count="pending">{counts.get("pending", 0)}</div><div class="l">Pending</div></div>
    <div class="stat implement"><div class="n" data-count="implement">{counts.get("implement", 0)}</div><div class="l">Implement</div></div>
    <div class="stat decline"><div class="n" data-count="decline">{counts.get("decline", 0)}</div><div class="l">Decline</div></div>
    <div class="stat defer"><div class="n" data-count="defer">{counts.get("defer", 0)}</div><div class="l">Defer</div></div>
  </div>
  <div class="controls">
    <input id="search" type="search" placeholder="Search title, author, repo, id...">
    <select id="repo-filter"><option value="">All repos</option>{repo_options}</select>
    <details class="filter-menu" id="author-menu">
      <summary id="author-summary">All authors</summary>
      <div class="filter-menu-body">
        <div class="menu-actions">
          <button type="button" class="menu-link" data-author-all>Select all</button>
          <button type="button" class="menu-link" data-author-none>Clear</button>
        </div>
        <div class="menu-items">{author_checkboxes}</div>
      </div>
    </details>
    <select id="status-filter">
      <option value="">All statuses</option>
      <option value="pending">Pending</option>
      <option value="implement">Implement</option>
      <option value="decline">Decline</option>
      <option value="defer">Defer</option>
    </select>
    <select id="rec-filter">
      <option value="">All recommendations</option>
      <option value="implement">implement</option>
      <option value="reject">reject</option>
      <option value="clarify">clarify</option>
      <option value="no-action">no-action</option>
    </select>
    <select id="group-by" title="Group feedback into sections by">
      <option value="pr">Group: pull request</option>
      <option value="repo">Group: repository</option>
      <option value="author">Group: author</option>
      <option value="recommendation">Group: recommendation</option>
      <option value="status">Group: status</option>
      <option value="kind">Group: type</option>
    </select>
    <select id="sort-by" title="Sort items within each group">
      <option value="date-desc">Sort: newest first</option>
      <option value="date-asc">Sort: oldest first</option>
      <option value="title">Sort: title</option>
      <option value="confidence">Sort: confidence</option>
      <option value="recommendation">Sort: recommendation</option>
      <option value="author">Sort: author</option>
    </select>
    <button class="reload-btn" id="reload">Reload</button>
  </div>
</header>
<div class="layout">
<aside class="sidebar">
  <div class="sidebar-title" id="sidebar-title">Pull requests</div>
  <nav id="sidebar-nav"></nav>
</aside>
<main id="cards">
{cards}
</main>
</div>
<div class="toast" id="toast"></div>
<script>
const cards = Array.from(document.querySelectorAll('.card'));
const search = document.getElementById('search');
const repoFilter = document.getElementById('repo-filter');
const authorMenu = document.getElementById('author-menu');
const authorSummary = document.getElementById('author-summary');
const authorBoxes = Array.from(document.querySelectorAll('[data-author-box]'));
const selectedAuthors = new Set();
const statusFilter = document.getElementById('status-filter');
const recFilter = document.getElementById('rec-filter');
const toast = document.getElementById('toast');
const cardsContainer = document.getElementById('cards');
const sidebarTitle = document.getElementById('sidebar-title');
const sidebarNav = document.getElementById('sidebar-nav');
const groupBy = document.getElementById('group-by');
const sortBy = document.getElementById('sort-by');

const CONF_RANK = {{ high:0, medium:1, low:2 }};
const REC_RANK = {{ implement:0, reject:1, clarify:2, 'no-action':3 }};
const STATUS_RANK = {{ pending:0, implement:1, decline:2, defer:3 }};

function slugify(value) {{
  return 'g-' + String(value).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}}

const GROUPINGS = {{
  pr: {{
    title: 'Pull requests',
    key: c => (c.dataset.repo || '?') + '#' + (c.dataset.pr || '?'),
    link: c => (c.dataset.repo && c.dataset.pr)
      ? 'https://github.com/' + c.dataset.repo + '/pull/' + c.dataset.pr : null
  }},
  repo: {{
    title: 'Repositories',
    key: c => c.dataset.repo || '(none)',
    link: c => c.dataset.repo ? 'https://github.com/' + c.dataset.repo : null
  }},
  author: {{ title:'Authors', key:c => c.dataset.author || '(none)' }},
  recommendation: {{
    title:'Recommendations',
    key:c => c.dataset.rec || '(none)',
    order:['implement','reject','clarify','no-action']
  }},
  status: {{
    title:'Statuses',
    key:c => c.dataset.status || 'pending',
    order:['pending','implement','decline','defer']
  }},
  kind: {{ title:'Comment types', key:c => c.dataset.kind || '(none)' }}
}};

const SORTS = {{
  'date-desc': (a,b) => (b.dataset.date || '').localeCompare(a.dataset.date || ''),
  'date-asc': (a,b) => (a.dataset.date || '').localeCompare(b.dataset.date || ''),
  'title': (a,b) => (a.dataset.title || '').localeCompare(b.dataset.title || '', undefined, {{sensitivity:'base'}}),
  'confidence': (a,b) => (CONF_RANK[a.dataset.confidence] ?? 9) - (CONF_RANK[b.dataset.confidence] ?? 9),
  'recommendation': (a,b) => (REC_RANK[a.dataset.rec] ?? 9) - (REC_RANK[b.dataset.rec] ?? 9),
  'author': (a,b) => (a.dataset.author || '').localeCompare(b.dataset.author || '', undefined, {{sensitivity:'base'}})
}};

let spy = null;
if ('IntersectionObserver' in window) {{
  spy = new IntersectionObserver(entries => {{
    for (const entry of entries) {{
      if (!entry.isIntersecting) continue;
      const id = entry.target.dataset.group;
      document.querySelectorAll('.nav-item')
        .forEach(a => a.classList.toggle('active', a.dataset.target === id));
    }}
  }}, {{ rootMargin: '-120px 0px -70% 0px', threshold: 0 }});
}}

function observeGroups() {{
  if (!spy) return;
  spy.disconnect();
  document.querySelectorAll('.group').forEach(g => spy.observe(g));
}}

function makeNavItem(label, count, slug) {{
  const nav = document.createElement('a');
  nav.className = 'nav-item';
  nav.href = '#' + slug;
  nav.dataset.target = slug;
  const name = document.createElement('span');
  name.className = 'nav-label';
  name.textContent = label;
  const num = document.createElement('span');
  num.className = 'nav-count';
  num.textContent = count;
  nav.appendChild(name);
  nav.appendChild(num);
  return nav;
}}

function renderGroups() {{
  const grouping = GROUPINGS[groupBy.value] || GROUPINGS.pr;
  const compare = SORTS[sortBy.value] || SORTS['date-desc'];
  const visible = cards.filter(c => !c.classList.contains('hidden'));

  const groups = new Map();
  for (const card of visible) {{
    const key = grouping.key(card) || '(none)';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(card);
  }}

  let keys = Array.from(groups.keys());
  if (grouping.order) {{
    keys.sort((a,b) => {{
      const ia = grouping.order.indexOf(a), ib = grouping.order.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    }});
  }} else {{
    keys.sort((a,b) => a.localeCompare(b, undefined, {{ numeric:true, sensitivity:'base' }}));
  }}

  cardsContainer.innerHTML = '';
  sidebarNav.innerHTML = '';
  sidebarTitle.textContent = grouping.title;

  for (const key of keys) {{
    const items = groups.get(key).slice().sort(compare);
    const slug = slugify(key);
    const section = document.createElement('section');
    section.className = 'group';
    section.dataset.group = slug;

    const head = document.createElement('div');
    head.className = 'group-head';
    head.id = slug;
    const url = grouping.link ? grouping.link(items[0]) : null;
    let titleEl;
    if (url) {{
      titleEl = document.createElement('a');
      titleEl.href = url;
      titleEl.target = '_blank';
      titleEl.rel = 'noopener';
    }} else {{
      titleEl = document.createElement('span');
    }}
    titleEl.textContent = key;
    const pending = items.filter(c => c.dataset.status === 'pending').length;
    const meta = document.createElement('span');
    meta.className = 'group-count';
    meta.textContent = items.length + ' item' + (items.length === 1 ? '' : 's')
      + (pending ? ' · ' + pending + ' pending' : '');
    head.appendChild(titleEl);
    head.appendChild(meta);
    section.appendChild(head);

    for (const card of items) section.appendChild(card);
    cardsContainer.appendChild(section);
    sidebarNav.appendChild(makeNavItem(key, items.length, slug));
  }}

  if (!visible.length) {{
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = cards.length
      ? 'No items match the current filters.'
      : 'No feedback files found.';
    cardsContainer.appendChild(empty);
  }}

  observeGroups();
}}

function applyFilters() {{
  const q = search.value.trim().toLowerCase();
  const repo = repoFilter.value;
  const status = statusFilter.value;
  const rec = recFilter.value;
  for (const card of cards) {{
    let show = true;
    if (q && !card.dataset.search.includes(q)) show = false;
    if (repo && card.dataset.repo !== repo) show = false;
    if (selectedAuthors.size && !selectedAuthors.has(card.dataset.author)) show = false;
    if (status && card.dataset.status !== status) show = false;
    if (rec && card.dataset.rec !== rec) show = false;
    card.classList.toggle('hidden', !show);
  }}
  renderGroups();
}}

function updateStats() {{
  const counts = {{}};
  for (const card of cards) {{
    const s = card.dataset.status;
    counts[s] = (counts[s] || 0) + 1;
  }}
  document.querySelectorAll('[data-count]').forEach(el => {{
    el.textContent = counts[el.dataset.count] || 0;
  }});
}}

function showToast(msg) {{
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove('show'), 1600);
}}

async function setDecision(id, decision) {{
  const card = document.querySelector(`.card[data-id="${{id}}"]`);
  const res = await fetch(`/api/items/${{encodeURIComponent(id)}}/decision`, {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ decision }})
  }});
  if (!res.ok) {{
    showToast('Failed to save decision');
    return;
  }}
  const data = await res.json();
  const status = data.decision || 'pending';
  card.dataset.status = status;
  const pill = card.querySelector('[data-role="decision-pill"]');
  const colors = {{ implement:'#3fb950', decline:'#f85149', defer:'#d29922', pending:'#8b949e' }};
  pill.textContent = status;
  pill.style.setProperty('--c', colors[status] || '#8b949e');
  card.style.setProperty('--decision-color', colors[status] || '#8b949e');
  card.querySelectorAll('.decision-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.decision === status);
  }});
  updateStats();
  renderGroups();
  showToast(`${{id}} -> ${{status}}`);
}}

document.querySelectorAll('.decision-btn').forEach(btn => {{
  btn.addEventListener('click', () => setDecision(btn.dataset.id, btn.dataset.decision));
}});

function syncAuthors() {{
  if (selectedAuthors.size === 0) authorSummary.textContent = 'All authors';
  else if (selectedAuthors.size === 1) authorSummary.textContent = Array.from(selectedAuthors)[0];
  else authorSummary.textContent = `${{selectedAuthors.size}} authors`;
  applyFilters();
}}

authorBoxes.forEach(box => box.addEventListener('change', () => {{
  if (box.checked) selectedAuthors.add(box.value);
  else selectedAuthors.delete(box.value);
  syncAuthors();
}}));

document.querySelector('[data-author-all]').addEventListener('click', (e) => {{
  e.preventDefault();
  authorBoxes.forEach(box => {{ box.checked = true; selectedAuthors.add(box.value); }});
  syncAuthors();
}});
document.querySelector('[data-author-none]').addEventListener('click', (e) => {{
  e.preventDefault();
  authorBoxes.forEach(box => {{ box.checked = false; }});
  selectedAuthors.clear();
  syncAuthors();
}});
document.addEventListener('click', (e) => {{
  if (authorMenu.open && !authorMenu.contains(e.target)) authorMenu.open = false;
}});

search.addEventListener('input', applyFilters);
[repoFilter, statusFilter, recFilter].forEach(el => el.addEventListener('change', applyFilters));
[groupBy, sortBy].forEach(el => el.addEventListener('change', renderGroups));

document.getElementById('reload').addEventListener('click', () => location.reload());

document.querySelectorAll('.copy-btn').forEach(btn => {{
  btn.addEventListener('click', async (e) => {{
    e.preventDefault();
    const target = document.getElementById(btn.dataset.copyTarget);
    if (!target) return;
    try {{
      await navigator.clipboard.writeText(target.innerText);
      showToast('Reply copied');
    }} catch {{ showToast('Copy failed'); }}
  }});
}});

const headerEl = document.querySelector('header.top');
function setHeaderH() {{
  if (headerEl) {{
    document.documentElement.style.setProperty('--header-h', headerEl.offsetHeight + 'px');
  }}
}}
setHeaderH();
window.addEventListener('resize', setHeaderH);

applyFilters();
</script>
</body>
</html>"""


def build_app(root: Path) -> FastAPI:
    app = FastAPI(title="PR Feedback Dashboard")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(render_page(discover(root), root))

    @app.get("/api/items")
    def api_items() -> JSONResponse:
        return JSONResponse([asdict(i) for i in discover(root)])

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "root": str(root), "count": len(discover(root))}

    @app.post("/api/items/{feedback_id}/decision")
    async def api_set_decision(feedback_id: str, payload: dict) -> JSONResponse:
        raw = payload.get("decision")
        if raw in (None, "", "pending"):
            decision = None
        elif raw in ("implement", "decline", "defer"):
            decision = raw
        else:
            raise HTTPException(status_code=422, detail="invalid decision")
        path = find_item(root, feedback_id)
        write_decision(path, decision)
        item = parse_feedback(path)
        return JSONResponse(
            {"feedback_id": feedback_id, "decision": decision, "item": asdict(item)}
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        default=str(Path.home() / ".sdlc"),
        help="SDLC root to scan (default: ~/.sdlc)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    root = Path(args.dir).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"SDLC root not found: {root}")

    print(f"PR feedback dashboard on http://{args.host}:{args.port}  (root: {root})")
    uvicorn.run(build_app(root), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
