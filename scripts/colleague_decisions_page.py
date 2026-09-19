# /// script
# requires-python = ">=3.11"
# ///
"""Build a static web page of colleague decisions from the markdown reports.

Reads every decisions report written by the extract-colleague-decisions skill
(``decisions/YYYY/MM/DD.md`` under NOTES_DIR, or any ``*.colleague-decisions.md``)
and renders a single self-contained HTML page showing each decision, who made it,
and who supported it. The page has three views: by author, by supporter, and a
support matrix, plus a free-text filter. No server and no network: everything is
inlined so the file can be opened locally or shared as-is.

Run:
    uv run scripts/colleague_decisions_page.py
    uv run scripts/colleague_decisions_page.py --notes-dir ~/notes --open
    uv run scripts/colleague_decisions_page.py --since 2026-09-01 --until 2026-09-30
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

BUCKETS = ("Decided", "Deferred", "Open", "Committed")

_DATE_RE = re.compile(r"(\d{4})[/-](\d{2})[/-](\d{2})")
_DECISION_RE = re.compile(
    r"^\s*[-*]\s+\*\*(Decided|Deferred|Open|Committed):\*\*\s*(.*)$"
)
_SUPPORT_RE = re.compile(r"^\s*[-*]\s+\*\*Supported by:\*\*\s*(.*)$")
_HEADLINE_RE = re.compile(r"^\*\*Headline:\*\*\s*(.*)$")
_SECTION_RE = re.compile(r"^##\s+(.*)$")
_URL_RE = re.compile(r"https?://[^\s)>\]]+")
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)]+)\)")
_NAME_SPLIT_RE = re.compile(r"\s*(?:,|;|/|\band\b)\s*", re.IGNORECASE)
_NOT_HEARD_RE = re.compile(r"^not heard", re.IGNORECASE)
_CROSS_RE = re.compile(r"^cross-cutting", re.IGNORECASE)


@dataclass
class Decision:
    date: str
    author: str
    bucket: str
    text: str
    permalink: str = ""
    supported_by: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class Report:
    day: str
    path: str
    decisions: list[Decision]
    headline: dict[str, str]
    not_heard: list[str]
    cross_cutting: str


def _clean_name(raw: str) -> str:
    return raw.strip().lstrip("@").strip()


def _split_names(raw: str) -> list[str]:
    raw = re.sub(r"\([^)]*\)", "", raw)
    names: list[str] = []
    for part in _NAME_SPLIT_RE.split(raw):
        name = _clean_name(part)
        if name:
            names.append(name)
    return names


def _extract_url(text: str) -> tuple[str, str]:
    links = _MD_LINK_RE.findall(text)
    if links:
        url = links[-1].rstrip(".,;")
        return _MD_LINK_RE.sub("", text).strip().rstrip("·-").strip(), url
    urls = _URL_RE.findall(text)
    if not urls:
        return text.strip(), ""
    url = urls[-1].rstrip(".,;")
    cleaned = text.replace(url, "")
    return cleaned.strip().rstrip("·-").strip(), url


def parse_report(path: Path, text: str) -> Report:
    match = _DATE_RE.search(str(path))
    if match:
        day = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    else:
        day = path.stem

    decisions: list[Decision] = []
    headline: dict[str, str] = {}
    not_heard: list[str] = []
    cross_lines: list[str] = []
    person: str | None = None
    special: str | None = None
    current: Decision | None = None

    for line in text.splitlines():
        section = _SECTION_RE.match(line)
        if section:
            person = None
            special = None
            name = section.group(1).strip()
            if _NOT_HEARD_RE.match(name):
                special = "not_heard"
            elif _CROSS_RE.match(name):
                special = "cross"
            else:
                person = _clean_name(name)
            current = None
            continue

        if special == "not_heard":
            stripped = line.strip()
            if stripped.startswith(("-", "*")):
                not_heard.extend(_split_names(stripped.lstrip("-* ").strip()))
            continue
        if special == "cross":
            if line.strip():
                cross_lines.append(line.rstrip())
            continue

        if person is None:
            continue

        if current is not None:
            support = _SUPPORT_RE.match(line)
            if support:
                for name in _split_names(support.group(1)):
                    if (
                        name.casefold() != person.casefold()
                        and name not in current.supported_by
                    ):
                        current.supported_by.append(name)
                continue
            if not current.permalink:
                _, url = _extract_url(line)
                if url:
                    current.permalink = url
                    continue

        head = _HEADLINE_RE.match(line)
        if head and current is None:
            headline[person] = head.group(1).strip()
            continue

        decision = _DECISION_RE.match(line)
        if decision:
            body, url = _extract_url(decision.group(2))
            current = Decision(
                date=day,
                author=person,
                bucket=decision.group(1),
                text=body,
                permalink=url,
                source=str(path),
            )
            decisions.append(current)
            continue

        if current is not None and line.strip() and line.startswith((" ", "\t")):
            continue

    return Report(
        day=day,
        path=str(path),
        decisions=decisions,
        headline=headline,
        not_heard=not_heard,
        cross_cutting="\n".join(cross_lines).strip(),
    )


def discover_reports(root: Path) -> list[Report]:
    seen: set[Path] = set()
    paths: list[Path] = []
    for pattern in ("**/decisions/*/*/*.md", "**/*.colleague-decisions.md"):
        for path in root.glob(pattern):
            if path.name.startswith(".") or path in seen:
                continue
            seen.add(path)
            paths.append(path)

    reports: list[Report] = []
    for path in sorted(paths):
        try:
            reports.append(parse_report(path, path.read_text(encoding="utf-8")))
        except OSError:
            continue
    reports.sort(key=lambda r: (r.day, r.path))
    return reports


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("'\"")
        if value:
            values[key.strip()] = os.path.expandvars(os.path.expanduser(value))
    return values


def resolve_notes_dir(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("NOTES_DIR")
    if env:
        return Path(env).expanduser()
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            value = parse_env_file(candidate).get("NOTES_DIR")
            if value:
                return Path(value).expanduser()
    return None


def build_payload(reports: list[Report], since: str | None, until: str | None) -> dict:
    selected = [
        r
        for r in reports
        if not (since and r.day < since) and not (until and r.day > until)
    ]

    decisions: list[Decision] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for report in selected:
        for decision in report.decisions:
            key = (
                decision.date,
                decision.author,
                decision.bucket,
                decision.text,
                decision.permalink,
            )
            if key in seen:
                continue
            seen.add(key)
            decisions.append(decision)

    decisions.sort(
        key=lambda d: (d.date, d.author, BUCKETS.index(d.bucket)), reverse=True
    )

    heard = {d.author.casefold() for d in decisions} | {
        s.casefold() for d in decisions for s in d.supported_by
    }
    not_heard = sorted(
        {
            name
            for report in selected
            for name in report.not_heard
            if name.casefold() not in heard
        },
        key=str.casefold,
    )
    headlines = {
        name: h for report in selected for name, h in report.headline.items() if h
    }
    cross = [r.cross_cutting for r in selected if r.cross_cutting]

    days = sorted({d.date for d in decisions})
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "reports": len(reports),
        "counts": {
            "decisions": len(decisions),
            "people": len({d.author for d in decisions}),
            "supporters": len({s for d in decisions for s in d.supported_by}),
        },
        "range": {"start": days[0], "end": days[-1]} if days else None,
        "decisions": [asdict(d) for d in decisions],
        "headlines": headlines,
        "not_heard": not_heard,
        "cross_cutting": cross,
    }


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Colleague Decisions</title>
<style>
:root {
  --bg:#0d1117; --panel:#161b22; --panel2:#1c2128; --border:#30363d;
  --fg:#e6edf3; --muted:#8b949e; --accent:#58a6ff;
  --decided:#3fb950; --deferred:#d29922; --open:#58a6ff; --committed:#a371f7;
  --header-h:230px;
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  margin:0; background:var(--bg); color:var(--fg);
  font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
}
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
header.top {
  position:sticky; top:0; z-index:20; background:rgba(13,17,23,.95);
  backdrop-filter:blur(8px); border-bottom:1px solid var(--border);
  padding:9px 22px;
}
.bar { display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  max-width:1360px; margin:0 auto; }
h1 { margin:0; font-size:17px; letter-spacing:.2px; white-space:nowrap; }
.sub { color:var(--muted); font-size:12.5px; margin-top:0; }
.toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-top:10px; }
.bar input[type=search] {
  flex:1; min-width:200px; background:var(--panel2); border:1px solid var(--border);
  color:var(--fg); border-radius:8px; padding:7px 12px; font-size:13.5px;
}
.bar input[type=search]:focus { outline:none; border-color:var(--accent); }
.controls { max-width:1360px; margin:0 auto; padding:12px 22px 0; }
.tabs { display:flex; gap:4px; background:var(--panel2); border:1px solid var(--border);
  border-radius:8px; padding:3px; }
.tabs button {
  background:transparent; border:0; color:var(--muted); padding:6px 12px;
  border-radius:6px; cursor:pointer; font-size:13px;
}
.tabs button.active { background:var(--panel); color:var(--fg); }
.tabs button:hover { color:var(--fg); }
.dates { margin-top:8px; }
.dates .label { color:var(--muted); font-size:12.5px; }
.toolbar input[type=date] {
  background:var(--panel2); border:1px solid var(--border); color:var(--fg);
  border-radius:8px; padding:6px 10px; font-size:13px;
}
.toolbar input[type=date]:focus { outline:none; border-color:var(--accent); }
.ghost { background:var(--panel2); border:1px solid var(--border); color:var(--fg);
  border-radius:8px; padding:6px 12px; cursor:pointer; font-size:13px; }
.ghost:hover { border-color:var(--accent); }
.presets { display:flex; gap:4px; background:var(--panel2); border:1px solid var(--border);
  border-radius:8px; padding:3px; }
.presets button { background:transparent; border:0; color:var(--muted); padding:5px 10px;
  border-radius:6px; cursor:pointer; font-size:12.5px; }
.presets button:hover { color:var(--fg); }
.presets button.active { background:var(--panel); color:var(--fg); }
.statuses { margin-top:8px; }
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.status-chip { display:inline-flex; align-items:center; gap:6px; background:var(--panel2);
  border:1px solid var(--border); color:var(--fg); border-radius:999px; padding:5px 12px;
  cursor:pointer; font-size:12.5px; }
.status-chip:hover { border-color:color-mix(in srgb, var(--b) 55%, var(--border)); }
.status-chip .cnt { color:var(--muted); font-variant-numeric:tabular-nums; }
.status-chip.active { border-color:var(--b); color:var(--b);
  background:color-mix(in srgb, var(--b) 14%, transparent); }
.status-chip.active .cnt { color:inherit; }
.status-chip.clear { color:var(--muted); --b:var(--border); }
.stats { display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 4px; }
.stat { background:var(--panel); border:1px solid var(--border); border-radius:8px;
  padding:8px 14px; }
.stat b { font-size:18px; }
.stat span { color:var(--muted); font-size:12px; margin-left:6px; }
.layout { display:flex; gap:26px; align-items:flex-start; max-width:1360px;
  margin:0 auto; padding:0 22px 60px; }
.controls .stats { margin-top:12px; }
main { flex:1; min-width:0; padding:18px 0 0; }
aside#sidebar { position:sticky; top:calc(var(--header-h) + 12px); flex:0 0 220px;
  width:220px; max-height:calc(100vh - var(--header-h) - 24px); overflow:auto; padding-top:22px; }
#sidebar .group { margin-bottom:16px; }
#sidebar .group-title { font-size:11px; text-transform:uppercase; letter-spacing:.6px;
  color:var(--muted); margin:0 0 6px 8px; }
#sidebar a.person-link { display:flex; justify-content:space-between; gap:8px;
  padding:4px 8px; border-radius:6px; color:var(--muted); font-size:13px; }
#sidebar a.person-link:hover { background:var(--panel2); color:var(--fg); text-decoration:none; }
#sidebar a.person-link.active { background:var(--panel2); color:var(--fg); }
#sidebar a.person-link .cnt { color:var(--muted); font-variant-numeric:tabular-nums; }
section[id] { scroll-margin-top:calc(var(--header-h) + 12px); }
@media (max-width: 900px) {
  aside#sidebar { display:none; }
  .layout { padding:0 16px 60px; }
}
.person { margin:24px 0 10px; display:flex; align-items:baseline; gap:10px; }
.person h2 { margin:0; font-size:15.5px; }
.person .pill-count { color:var(--muted); font-size:12px; }
.headline { color:var(--muted); font-size:13px; margin:2px 0 10px; font-style:italic; }
.card {
  background:var(--panel); border:1px solid var(--border); border-left:3px solid var(--b);
  border-radius:8px; padding:12px 14px; margin:8px 0;
}
.card .top { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:6px; }
.badge { font-size:11px; font-weight:600; letter-spacing:.4px; text-transform:uppercase;
  color:var(--b); border:1px solid color-mix(in srgb, var(--b) 45%, transparent);
  border-radius:999px; padding:2px 9px; }
.when { color:var(--muted); font-size:12px; }
.text { margin:2px 0 8px; }
.support { display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-top:6px; }
.support .label { color:var(--muted); font-size:12px; }
.chip { background:var(--panel2); border:1px solid var(--border); border-radius:999px;
  padding:1px 9px; font-size:12px; color:var(--fg); }
.chip.author { border-color:color-mix(in srgb, var(--accent) 45%, transparent); }
.meta { margin-top:8px; font-size:12px; }
.empty { color:var(--muted); text-align:center; padding:60px 0; }
table { border-collapse:collapse; width:100%; font-size:12.5px; }
th, td { border:1px solid var(--border); padding:5px 8px; text-align:center; }
th { background:var(--panel2); }
th.row, td.row { text-align:left; white-space:nowrap; }
thead th { position:sticky; top:0; z-index:2; }
tbody th.row { position:sticky; left:0; z-index:1; background:var(--panel); }
thead th.row { left:0; z-index:3; }
td.zero { color:#3a4149; }
td .n { font-weight:600; }
td.diag { background:color-mix(in srgb, var(--accent) 14%, transparent); color:var(--accent); }
td.pct { background:color-mix(in srgb, var(--b) 22%, transparent); color:var(--b); }
td.clickable { cursor:pointer; }
td.clickable:hover { background:color-mix(in srgb, var(--accent) 22%, transparent); }
td.selected { box-shadow:inset 0 0 0 2px var(--accent); }
.matrix-legend { margin:10px 0 0; }
.cell-detail { margin-top:22px; }
.cell-detail-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:10px; }
.cell-detail-head h3 { margin:0; font-size:14.5px; }
.matrix-wrap { overflow:auto; max-height:70vh; border:1px solid var(--border); border-radius:8px; }
.section-title { font-size:13px; text-transform:uppercase; letter-spacing:.6px;
  color:var(--muted); margin:26px 0 10px; }
footer { color:var(--muted); font-size:12px; margin-top:40px; }
.notheard { color:var(--muted); font-size:13px; }
</style>
</head>
<body>
<header class="top">
  <div class="bar">
    <h1>Colleague Decisions</h1>
    <input type="search" id="q" placeholder="Filter by text, person, supporter, date, status...">
    <div class="tabs" id="tabs">
      <button data-view="decisions" class="active">By author</button>
      <button data-view="supporters">By supporter</button>
      <button data-view="matrix">Matrix</button>
    </div>
  </div>
</header>
<div class="controls">
  <div class="sub" id="sub"></div>
  <div class="toolbar dates">
    <span class="label">Dates</span>
    <input type="date" id="from" aria-label="From date">
    <span class="label">to</span>
    <input type="date" id="to" aria-label="To date">
    <button type="button" class="ghost" id="clear-dates">All dates</button>
    <div class="presets" id="presets">
      <button type="button" data-days="7">Last 7d</button>
      <button type="button" data-days="30">Last 30d</button>
      <button type="button" data-days="90">Last 90d</button>
    </div>
  </div>
  <div class="toolbar statuses">
    <span class="label">Status</span>
    <div class="chips" id="status"></div>
  </div>
  <div class="stats" id="stats"></div>
</div>
<div class="layout">
  <aside id="sidebar"><nav id="people"></nav></aside>
  <main id="app"></main>
</div>
<footer id="footer" style="max-width:1360px;margin:0 auto;padding:0 22px 40px"></footer>
<script>
const DATA = /*__DATA__*/;
const COLORS = {Decided:'var(--decided)', Deferred:'var(--deferred)', Open:'var(--open)', Committed:'var(--committed)'};
const state = { view:'decisions', q:'', from:'', to:'', preset:'', buckets:new Set(), cell:null };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const key = s => String(s ?? '').toLowerCase();
const slug = s => String(s ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const DATE_RE = /^\\d{4}-\\d{2}-\\d{2}$/;

function validDate(s) { return DATE_RE.test(s); }
function inRange(d) {
  if (state.from && d.date < state.from) return false;
  if (state.to && d.date > state.to) return false;
  return true;
}
function baseMatch(d) {
  if (!inRange(d)) return false;
  if (!state.q) return true;
  const hay = [d.text, d.author, d.bucket, d.date, d.supported_by.join(' ')].join(' ').toLowerCase();
  return hay.includes(state.q);
}
function bucketMatch(d) { return !state.buckets.size || state.buckets.has(d.bucket); }
function matches(d) { return baseMatch(d) && bucketMatch(d); }
function shiftDays(date, days) {
  const dt = new Date(date + 'T00:00:00Z');
  dt.setUTCDate(dt.getUTCDate() + days);
  return dt.toISOString().slice(0, 10);
}
function isFiltering() { return Boolean(state.q || state.from || state.to || state.buckets.size); }

function badge(d) {
  return `<span class="badge" style="--b:${COLORS[d.bucket] || 'var(--muted)'}">${esc(d.bucket)}</span>`;
}

function card(d, showAuthor) {
  const supporter = d.supported_by.length
    ? `<div class="support"><span class="label">Supported by</span>${d.supported_by.map(s => `<span class="chip">${esc(s)}</span>`).join('')}</div>`
    : '';
  const author = showAuthor ? `<span class="chip author">${esc(d.author)}</span>` : '';
  const link = d.permalink ? ` · <a href="${esc(d.permalink)}" target="_blank" rel="noopener">Open in Slack</a>` : '';
  return `<article class="card" style="--b:${COLORS[d.bucket] || 'var(--muted)'}">
    <div class="top">${badge(d)}${author}<span class="when">${esc(d.date)}</span></div>
    <div class="text">${esc(d.text)}</div>
    ${supporter}
    <div class="meta">${link.replace(' · ', '')}</div>
  </article>`;
}

function renderDecisions(list) {
  const byAuthor = new Map();
  for (const d of list) {
    if (!byAuthor.has(d.author)) byAuthor.set(d.author, []);
    byAuthor.get(d.author).push(d);
  }
  const authors = [...byAuthor.keys()].sort((a, b) => byAuthor.get(b).length - byAuthor.get(a).length || a.localeCompare(b));
  if (!authors.length) return empty();
  return authors.map(author => {
    const items = byAuthor.get(author);
    const head = DATA.headlines[author] ? `<div class="headline">${esc(DATA.headlines[author])}</div>` : '';
    return `<section id="author-${slug(author)}">
      <div class="person"><h2>${esc(author)}</h2><span class="pill-count">${items.length} item${items.length === 1 ? '' : 's'}</span></div>
      ${head}
      ${items.map(d => card(d, false)).join('')}
    </section>`;
  }).join('');
}

function renderSupporters(list) {
  const bySupporter = new Map();
  for (const d of list) {
    for (const s of d.supported_by) {
      if (!bySupporter.has(s)) bySupporter.set(s, []);
      bySupporter.get(s).push(d);
    }
  }
  const supporters = [...bySupporter.keys()].sort((a, b) => bySupporter.get(b).length - bySupporter.get(a).length || a.localeCompare(b));
  if (!supporters.length) return `<p class="empty">No support recorded in the selected decisions.</p>`;
  return supporters.map(s => {
    const items = bySupporter.get(s);
    return `<section id="supporter-${slug(s)}">
      <div class="person"><h2>${esc(s)}</h2><span class="pill-count">backed ${items.length} decision${items.length === 1 ? '' : 's'}</span></div>
      ${items.map(d => card(d, true)).join('')}
    </section>`;
  }).join('');
}

function cellSelected(a, p) {
  const c = state.cell;
  if (!c || c.author !== a) return false;
  return p === a ? Boolean(c.diagonal) : c.supporter === p;
}

function renderCellDetail(list) {
  const c = state.cell;
  const items = list.filter(d => d.author === c.author && (c.diagonal || d.supported_by.includes(c.supporter)));
  const title = c.diagonal
    ? `${esc(c.author)}: ${items.length} decision${items.length === 1 ? '' : 's'} made`
    : `${esc(c.author)} supported by ${esc(c.supporter)}: ${items.length} decision${items.length === 1 ? '' : 's'}`;
  const body = items.length
    ? items.map(d => card(d, false)).join('')
    : `<p class="empty">No decisions for this combination under the current filter.</p>`;
  return `<div class="cell-detail" id="cell-detail">
    <div class="cell-detail-head"><h3>${title}</h3>
      <button type="button" class="ghost" id="cell-clear">Clear</button></div>
    ${body}
  </div>`;
}

function renderMatrix(list) {
  const authors = [...new Set(list.map(d => d.author))].sort((a, b) => a.localeCompare(b));
  const people = [...new Set([...authors, ...list.flatMap(d => d.supported_by)])].sort((a, b) => a.localeCompare(b));
  if (!authors.length || !people.length) return `<p class="empty">Not enough data for a support matrix yet.</p>`;
  const made = new Map();
  const supported = new Map();
  const counts = new Map();
  for (const d of list) {
    made.set(d.author, (made.get(d.author) || 0) + 1);
    if (d.supported_by.length) {
      supported.set(d.author, (supported.get(d.author) || 0) + 1);
    }
    for (const s of new Set(d.supported_by)) {
      const k = d.author + '\\u0000' + s;
      counts.set(k, (counts.get(k) || 0) + 1);
    }
  }
  const head = people.map(p => `<th>${esc(p)}</th>`).join('');
  const rows = authors.map(a => {
    let received = 0;
    const cells = people.map(p => {
      if (p === a) {
        const sel = cellSelected(a, p) ? ' selected' : '';
        return `<td class="diag clickable${sel}" data-author="${esc(a)}" data-supporter="${esc(a)}" title="Decisions made"><span class="n">${made.get(a) || 0}</span></td>`;
      }
      const n = counts.get(a + '\\u0000' + p) || 0;
      received += n;
      if (!n) return `<td class="zero">·</td>`;
      const sel = cellSelected(a, p) ? ' selected' : '';
      return `<td class="clickable${sel}" data-author="${esc(a)}" data-supporter="${esc(p)}"><span class="n">${n}</span></td>`;
    }).join('');
    const total = made.get(a) || 0;
    const got = supported.get(a) || 0;
    const pct = total ? Math.round((got / total) * 100) : 0;
    const hue = Math.round((pct / 100) * 120);
    const pctColor = `hsl(${hue}, 65%, 48%)`;
    const pctCell = `<td class="pct" style="--b:${pctColor}" title="${got} of ${total} decisions supported (${pct}%)"><span class="n">${pct}%</span></td>`;
    return `<tr><th class="row">${esc(a)}</th>${cells}${pctCell}<td><span class="n">${received}</span></td></tr>`;
  }).join('');
  const detail = state.cell ? renderCellDetail(list) : '';
  return `<div class="matrix-wrap"><table><thead><tr><th class="row">Author \\\\ Supporter</th>${head}<th>Supported</th><th>Received</th></tr></thead><tbody>${rows}</tbody></table></div>
    <div class="section-title matrix-legend">Rows are decision authors, columns are supporters. Diagonal = decisions made; off-diagonal = decisions by the row's author supported by the column's supporter. Supported = share of the author's decisions with at least one supporter; Received = total endorsements. Click a cell to list its decisions.</div>
    ${detail}`;
}

function empty() {
  return `<p class="empty">No decisions match. ${DATA.decisions.length ? 'Try clearing the filter.' : 'No reports found under the notes directory.'}</p>`;
}

function renderPeople(list) {
  const authors = new Map();
  const supporters = new Map();
  for (const d of list) {
    authors.set(d.author, (authors.get(d.author) || 0) + 1);
    for (const s of new Set(d.supported_by)) supporters.set(s, (supporters.get(s) || 0) + 1);
  }
  const group = (title, map, kind) => {
    if (!map.size) return '';
    const rows = [...map.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([name, count]) => {
        const target = (kind === 'author' ? 'author-' : 'supporter-') + slug(name);
        return `<a class="person-link" href="#" data-kind="${kind}" data-target="${esc(target)}">` +
          `<span>${esc(name)}</span><span class="cnt">${count}</span></a>`;
      }).join('');
    return `<div class="group"><div class="group-title">${title}</div>${rows}</div>`;
  };
  document.getElementById('people').innerHTML =
    group('Authors', authors, 'author') + group('Supporters', supporters, 'supporter') ||
    `<div class="group"><div class="group-title">No matches</div></div>`;
}

function renderStatusFilter(base) {
  const counts = new Map();
  for (const d of base) counts.set(d.bucket, (counts.get(d.bucket) || 0) + 1);
  const order = ['Decided', 'Deferred', 'Open', 'Committed'];
  const known = new Set(order);
  const extra = [...counts.keys()].filter(b => !known.has(b));
  const parts = [...order, ...extra]
    .filter(b => counts.get(b) || state.buckets.has(b))
    .map(b => {
      const on = state.buckets.has(b) ? ' active' : '';
      return `<button type="button" class="status-chip${on}" data-bucket="${esc(b)}" style="--b:${COLORS[b] || 'var(--muted)'}">` +
        `${esc(b)}<span class="cnt">${counts.get(b) || 0}</span></button>`;
    });
  if (state.buckets.size) parts.push('<button type="button" class="status-chip clear" id="status-clear">All</button>');
  document.getElementById('status').innerHTML = parts.join('') || '<span class="label">none</span>';
}

function headerHeight() {
  const header = document.querySelector('header.top');
  return header ? header.offsetHeight : 0;
}
function syncHeaderVar() {
  document.documentElement.style.setProperty('--header-h', headerHeight() + 'px');
}
function highlightTarget() {
  const links = [...document.querySelectorAll('#people a.person-link')];
  if (!links.length) return;
  const offset = headerHeight() + 24;
  const sections = [...document.querySelectorAll('main section[id]')];
  let active = null;
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= offset) active = section.id;
    else break;
  }
  links.forEach(a => a.classList.toggle('active', a.dataset.target === active));
}

function render() {
  document.getElementById('q').value = state.q;
  const fromEl = document.getElementById('from');
  const toEl = document.getElementById('to');
  if (DATA.range) {
    fromEl.min = toEl.min = DATA.range.start;
    fromEl.max = toEl.max = DATA.range.end;
  }
  fromEl.value = state.from;
  toEl.value = state.to;
  const active = isFiltering();
  const base = DATA.decisions.filter(baseMatch);
  const list = base.filter(bucketMatch);
  const app = document.getElementById('app');
  if (state.view === 'decisions') app.innerHTML = renderDecisions(list);
  else if (state.view === 'supporters') app.innerHTML = renderSupporters(list);
  else app.innerHTML = renderMatrix(list);
  renderPeople(list);
  renderStatusFilter(base);

  const c = DATA.counts;
  const range = DATA.range ? `${DATA.range.start} to ${DATA.range.end}` : 'no data';
  const span = active && (state.from || state.to)
    ? ` · showing ${state.from || 'start'} to ${state.to || 'end'}`
    : '';
  document.getElementById('sub').textContent =
    `${c.decisions} decisions · ${c.people} people · ${c.supporters} supporters · ${range} · generated ${DATA.generated}${span}`;
  document.getElementById('stats').innerHTML = [
    ['Decisions', list.length + (active ? ' / ' + c.decisions : '')],
    ['People', active ? new Set(list.map(d => d.author)).size + ' / ' + c.people : c.people],
    ['Supporters', active ? new Set(list.flatMap(d => d.supported_by)).size + ' / ' + c.supporters : c.supporters],
    ['Reports', DATA.reports],
  ].map(([label, value]) => `<div class="stat"><b>${esc(value)}</b><span>${esc(label)}</span></div>`).join('');

  const presets = document.getElementById('presets');
  [...presets.querySelectorAll('button')].forEach(b => b.classList.toggle('active', b.dataset.days === state.preset));

  const nh = DATA.not_heard.length
    ? `<div class="section-title">Not heard from</div><div class="notheard">${DATA.not_heard.map(esc).join(', ')}</div>` : '';
  document.getElementById('footer').innerHTML =
    (nh ? nh + '<br>' : '') + `Source: ${esc(DATA.notes_dir)}`;

  syncHeaderVar();
  highlightTarget();
}

function setView(view) {
  if (!['decisions', 'supporters', 'matrix'].includes(view)) return;
  state.view = view;
  [...document.querySelectorAll('#tabs button')].forEach(b => b.classList.toggle('active', b.dataset.view === view));
  render();
}
function applyRange(from, to, preset) {
  state.from = validDate(from) ? from : '';
  state.to = validDate(to) ? to : '';
  state.preset = preset || '';
  if (state.from && state.to && state.from > state.to) {
    [state.from, state.to] = [state.to, state.from];
  }
  render();
}
document.getElementById('q').addEventListener('input', e => { state.q = e.target.value.trim().toLowerCase(); render(); });
document.getElementById('tabs').addEventListener('click', e => {
  const btn = e.target.closest('button');
  if (!btn) return;
  location.hash = btn.dataset.view;
  setView(btn.dataset.view);
});
document.getElementById('from').addEventListener('change', e => applyRange(e.target.value, state.to));
document.getElementById('to').addEventListener('change', e => applyRange(state.from, e.target.value));
document.getElementById('clear-dates').addEventListener('click', () => applyRange('', ''));
document.getElementById('status').addEventListener('click', e => {
  if (e.target.closest('#status-clear')) { state.buckets.clear(); render(); return; }
  const btn = e.target.closest('button[data-bucket]');
  if (!btn) return;
  const bucket = btn.dataset.bucket;
  if (state.buckets.has(bucket)) state.buckets.delete(bucket);
  else state.buckets.add(bucket);
  render();
});
document.getElementById('presets').addEventListener('click', e => {
  const btn = e.target.closest('button');
  if (!btn || !DATA.range) return;
  const days = Number(btn.dataset.days);
  applyRange(shiftDays(DATA.range.end, -(days - 1)), DATA.range.end, btn.dataset.days);
});
document.getElementById('app').addEventListener('click', e => {
  if (e.target.closest('#cell-clear')) { state.cell = null; render(); return; }
  const td = e.target.closest('td[data-author]');
  if (!td) return;
  const author = td.dataset.author;
  const supporter = td.dataset.supporter;
  const diagonal = author === supporter;
  const c = state.cell;
  const same = c && c.author === author && c.diagonal === diagonal && (diagonal || c.supporter === supporter);
  state.cell = same ? null : { author, supporter, diagonal };
  render();
  const detail = document.getElementById('cell-detail');
  if (detail) detail.scrollIntoView({ behavior:'smooth', block:'nearest' });
});
document.getElementById('people').addEventListener('click', e => {
  const link = e.target.closest('a.person-link');
  if (!link) return;
  e.preventDefault();
  setView(link.dataset.kind === 'author' ? 'decisions' : 'supporters');
  const target = document.getElementById(link.dataset.target);
  if (target) target.scrollIntoView({ behavior:'smooth', block:'start' });
  highlightTarget();
});
window.addEventListener('scroll', highlightTarget, { passive:true });
window.addEventListener('resize', () => { syncHeaderVar(); highlightTarget(); });
setView(location.hash.slice(1) || 'decisions');
</script>
</body>
</html>
"""


def render_page(payload: dict, notes_dir: Path) -> str:
    payload["notes_dir"] = str(notes_dir)
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return PAGE_TEMPLATE.replace("/*__DATA__*/", data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--notes-dir", help="Notes root (default: NOTES_DIR env or nearest .env)"
    )
    parser.add_argument(
        "--output",
        help="HTML output path (default: <notes-dir>/colleague-decisions.html)",
    )
    parser.add_argument(
        "--since", help="Only include decisions on/after this YYYY-MM-DD"
    )
    parser.add_argument(
        "--until", help="Only include decisions on/before this YYYY-MM-DD"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open the page in a browser"
    )
    args = parser.parse_args()

    notes_dir = resolve_notes_dir(args.notes_dir)
    if notes_dir is None or not notes_dir.exists():
        print(
            "Could not resolve NOTES_DIR. Pass --notes-dir or set it in .env.",
            file=sys.stderr,
        )
        return 1

    reports = discover_reports(notes_dir)
    payload = build_payload(reports, args.since, args.until)
    html_text = render_page(payload, notes_dir)

    output = (
        Path(args.output).expanduser()
        if args.output
        else notes_dir / "colleague-decisions.html"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")

    count = payload["counts"]["decisions"]
    if count:
        print(f"Wrote {output} ({count} decisions from {len(reports)} report(s)).")
    else:
        print(f"Wrote {output} (no decisions found; {len(reports)} report(s) scanned).")
    if args.open:
        webbrowser.open(output.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
