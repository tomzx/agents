#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Build a self-contained HTML walkthrough for a pull request.

Two phases:

1. ``scaffold`` fetches the PR metadata and diff, parses the diff, decides
   whether the PR is large enough to warrant a walkthrough, and writes a
   ``narrative.json`` skeleton for an agent to fill in.
2. ``render`` merges the filled narrative with the diff and writes a single
   self-contained HTML page (inline CSS and JS, no network access).

The page groups files into a suggested reading order, renders each file's
annotated diff hunks, and carries the risk, findings, and open questions that
the reviewer should know before reading the code.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

DEFAULT_MIN_LINES = 200
DEFAULT_MIN_FILES = 10

GH_FIELDS = (
    "number,title,author,url,baseRefName,headRefName,baseRefOid,headRefOid,"
    "additions,deletions,changedFiles,commits,body,isDraft,createdAt,"
    "updatedAt,closingIssuesReferences,headRepository"
)

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# Diff model and parser
# ---------------------------------------------------------------------------


@dataclass
class DiffLine:
    kind: str  # add | del | ctx | meta
    old_no: int | None
    new_no: int | None
    text: str


@dataclass
class Hunk:
    header: str
    lines: list[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    path: str
    old_path: str | None = None
    change_type: str = "modified"
    hunks: list[Hunk] = field(default_factory=list)
    binary: bool = False


def decode_git_quoted(inner: str) -> str:
    out = bytearray()
    index = 0
    while index < len(inner):
        char = inner[index]
        if char != "\\" or index + 1 >= len(inner):
            out.extend(char.encode("utf-8"))
            index += 1
            continue
        next_char = inner[index + 1]
        if next_char in "01234567":
            digits = ""
            cursor = index + 1
            while cursor < len(inner) and len(digits) < 3 and inner[cursor] in "01234567":
                digits += inner[cursor]
                cursor += 1
            out.append(int(digits, 8) & 0xFF)
            index = cursor
            continue
        escapes = {
            "n": b"\n",
            "t": b"\t",
            "r": b"\r",
            "\\": b"\\",
            '"': b'"',
            "a": b"\a",
            "b": b"\b",
            "f": b"\f",
            "v": b"\v",
        }
        if next_char in escapes:
            out.extend(escapes[next_char])
            index += 2
            continue
        out.extend(next_char.encode("utf-8"))
        index += 2
    return out.decode("utf-8", errors="replace")


def git_path(raw: str, strip_prefix: bool = True) -> str | None:
    value = raw.strip()
    if value.startswith('"') and value.endswith('"'):
        value = decode_git_quoted(value[1:-1])
    if value == "/dev/null":
        return None
    if strip_prefix and value.startswith(("a/", "b/")):
        value = value[2:]
    return value


def parse_diff_git_paths(rest: str) -> tuple[str | None, str | None] | None:
    match = re.match(r'^(?:"((?:\\.|[^"])*)"|(\S+))\s+(?:"((?:\\.|[^"])*)"|(\S+))$', rest)
    if match:

        def value(quoted: str | None, plain: str | None) -> str | None:
            raw = f'"{quoted}"' if quoted is not None else plain
            return git_path(raw) if raw is not None else None

        return value(match.group(1), match.group(2)), value(match.group(3), match.group(4))

    parts = shlex.split(rest)
    if len(parts) < 2:
        return None
    return git_path(parts[-2]), git_path(parts[-1])


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    hunk: Hunk | None = None
    old_no = 0
    new_no = 0

    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            current = FileDiff(path="")
            paths = parse_diff_git_paths(raw[len("diff --git ") :])
            if paths:
                current.old_path, current.path = paths[0], paths[1] or paths[0] or ""
            files.append(current)
            hunk = None
            continue

        if current is None:
            continue

        if hunk is None:
            if raw.startswith("new file mode"):
                current.change_type = "added"
                continue
            if raw.startswith("deleted file mode"):
                current.change_type = "deleted"
                continue
            if raw.startswith("rename from "):
                current.old_path = git_path(
                    raw[len("rename from ") :], strip_prefix=False
                )
                current.change_type = "renamed"
                continue
            if raw.startswith("rename to "):
                current.path = (
                    git_path(raw[len("rename to ") :], strip_prefix=False) or current.path
                )
                continue
            if raw.startswith("Binary files ") or raw.startswith("GIT binary patch"):
                current.binary = True
                continue
            if raw.startswith("--- "):
                current.old_path = git_path(raw[len("--- ") :])
                continue
            if raw.startswith("+++ "):
                new = git_path(raw[len("+++ ") :])
                if new:
                    current.path = new
                continue

        match = HUNK_RE.match(raw)
        if match:
            old_no = int(match.group(1))
            new_no = int(match.group(3))
            hunk = Hunk(header=raw)
            current.hunks.append(hunk)
            continue

        if hunk is None:
            continue

        if raw.startswith("\\"):
            hunk.lines.append(DiffLine("meta", None, None, raw))
        elif raw.startswith("+"):
            hunk.lines.append(DiffLine("add", None, new_no, raw[1:]))
            new_no += 1
        elif raw.startswith("-"):
            hunk.lines.append(DiffLine("del", old_no, None, raw[1:]))
            old_no += 1
        elif raw.startswith(" "):
            hunk.lines.append(DiffLine("ctx", old_no, new_no, raw[1:]))
            old_no += 1
            new_no += 1
        else:
            hunk.lines.append(DiffLine("meta", None, None, raw))

    for item in files:
        if not item.path and item.old_path:
            item.path = item.old_path

    return [item for item in files if item.path]


def file_stats(item: FileDiff) -> tuple[int, int]:
    additions = 0
    deletions = 0
    for hunk in item.hunks:
        for line in hunk.lines:
            if line.kind == "add":
                additions += 1
            elif line.kind == "del":
                deletions += 1
    return additions, deletions


def diff_stats(files: list[FileDiff]) -> dict[str, int]:
    additions = 0
    deletions = 0
    for item in files:
        file_adds, file_dels = file_stats(item)
        additions += file_adds
        deletions += file_dels
    return {
        "files": len(files),
        "additions": additions,
        "deletions": deletions,
        "changed_lines": additions + deletions,
    }


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def fetch_meta(repo: str, pr: int) -> dict[str, Any]:
    result = run(["gh", "pr", "view", str(pr), "--repo", repo, "--json", GH_FIELDS])
    if result.returncode != 0:
        fail(f"gh pr view failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def normalize_meta(raw: dict[str, Any], repo: str, pr: int) -> dict[str, Any]:
    author = raw.get("author") or ""
    if isinstance(author, dict):
        author = author.get("login", "")
    head_repo = raw.get("headRepository") or {}
    if isinstance(head_repo, dict):
        head_repo = head_repo.get("nameWithOwner", "")
    commits = raw.get("commits")
    if isinstance(commits, list):
        commit_count = len(commits)
    elif isinstance(commits, int):
        commit_count = commits
    else:
        commit_count = 0
    issues = raw.get("closingIssuesReferences") or []
    issue_numbers = [
        item.get("number") for item in issues if isinstance(item, dict) and item.get("number")
    ]
    return {
        "repo": repo,
        "pr": raw.get("number", pr),
        "title": raw.get("title", ""),
        "author": author,
        "url": raw.get("url", f"https://github.com/{repo}/pull/{pr}"),
        "base_ref": raw.get("baseRefName", ""),
        "head_ref": raw.get("headRefName", ""),
        "base_sha": raw.get("baseRefOid", ""),
        "head_sha": raw.get("headRefOid", ""),
        "head_repo": head_repo,
        "body": raw.get("body", ""),
        "is_draft": bool(raw.get("isDraft", False)),
        "created_at": raw.get("createdAt", ""),
        "updated_at": raw.get("updatedAt", ""),
        "commits": commit_count,
        "closing_issues": issue_numbers,
        "generated_at": now_iso(),
    }


def fetch_diff(repo: str, pr: int, meta: dict[str, Any], worktree: str | None) -> str:
    result = run(["gh", "pr", "diff", str(pr), "--repo", repo])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout

    head_repo = meta.get("head_repo") or repo
    base_sha = meta.get("base_sha")
    head_sha = meta.get("head_sha")
    cwd = worktree or os.getcwd()
    if not base_sha or not head_sha:
        fail(f"gh pr diff failed and the PR SHAs are unknown: {result.stderr.strip()}")

    def fetch(url: str, ref: str) -> bool:
        fetched = run(["git", "fetch", "--no-tags", url, ref], cwd=cwd)
        return fetched.returncode == 0

    base_ok = fetch(f"https://github.com/{repo}.git", base_sha) or fetch(
        f"https://github.com/{repo}.git", meta.get("base_ref", "")
    )
    head_ok = fetch(f"https://github.com/{head_repo}.git", head_sha) or fetch(
        f"https://github.com/{head_repo}.git", meta.get("head_ref", "")
    )
    if not (base_ok and head_ok):
        fail("could not fetch the PR commits; pass --diff-file with a saved diff")

    diff = run(["git", "diff", f"{base_sha}...{head_sha}"], cwd=cwd)
    if diff.returncode != 0:
        fail(f"git diff failed: {diff.stderr.strip()}")
    return diff.stdout


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def report_sources(repo: str, pr: int) -> tuple[dict[str, str], dict[str, Any]]:
    base = Path.home() / ".sdlc" / repo / "pull-requests" / str(pr)
    names = {
        "assess-pr-risk": "assess-pr-risk.report.md",
        "summarize-behavior-changes": "summarize-behavior-changes.report.md",
        "analyze-test-coverage": "analyze-test-coverage.report.md",
        "validate-pr": "validate-pr.report.md",
        "verify-pr": "verify-pr.report.md",
        "review-pr": "review-pr.report.md",
    }
    sources = {step: str(base / name) for step, name in names.items() if (base / name).exists()}

    assess: dict[str, Any] = {}
    assess_path = base / names["assess-pr-risk"]
    if assess_path.exists():
        text = assess_path.read_text(errors="replace")
        match = re.search(r"<!--\s*(\{.*?\})\s*-->", text, re.DOTALL)
        if match:
            try:
                marker = json.loads(match.group(1))
                assess = {
                    "risk": marker.get("risk", ""),
                    "confidence": marker.get("confidence", ""),
                    "verdict": marker.get("verdict", ""),
                }
            except json.JSONDecodeError:
                pass
    return sources, assess


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------


def build_scaffold(
    meta: dict[str, Any], files: list[FileDiff], sources: dict[str, str], assess: dict[str, Any]
) -> dict[str, Any]:
    stats = diff_stats(files)
    entries = []
    for item in files:
        additions, deletions = file_stats(item)
        hunks = []
        for index, hunk in enumerate(item.hunks):
            changed = [line for line in hunk.lines if line.kind in ("add", "del")]
            preview = "\n".join(
                ("+" if line.kind == "add" else "-") + line.text for line in changed[:6]
            )
            hunks.append(
                {
                    "index": index,
                    "header": hunk.header,
                    "changed_lines": len(changed),
                    "preview": preview[:600],
                }
            )
        entries.append(
            {
                "path": item.path,
                "old_path": item.old_path,
                "change_type": item.change_type,
                "stats": {"additions": additions, "deletions": deletions},
                "hunks": hunks,
                "purpose": "",
                "annotations": {},
                "risks": [],
            }
        )

    return {
        "meta": {**meta, "stats": stats},
        "summary": "",
        "why": "",
        "reading_order": [],
        "files": entries,
        "risks": [],
        "findings": [],
        "questions": [],
        "verdict": "",
        "sources": sources,
        "assess": assess,
    }


def size_decision(stats: dict[str, int], min_lines: int, min_files: int) -> dict[str, Any]:
    reasons = []
    if stats["changed_lines"] >= min_lines:
        reasons.append(f"{stats['changed_lines']} changed lines >= {min_lines}")
    if stats["files"] >= min_files:
        reasons.append(f"{stats['files']} files >= {min_files}")
    return {
        "large": bool(reasons),
        "reasons": reasons,
        "thresholds": {"changed_lines": min_lines, "files": min_files},
        **stats,
    }


def cmd_scaffold(args: argparse.Namespace) -> int:
    if args.meta_file:
        raw_meta = json.loads(Path(args.meta_file).read_text())
        meta = normalize_meta(raw_meta, args.repo, args.pr)
    else:
        meta = normalize_meta(fetch_meta(args.repo, args.pr), args.repo, args.pr)

    if args.diff_file:
        diff_text = Path(args.diff_file).read_text(errors="replace")
    else:
        diff_text = fetch_diff(args.repo, args.pr, meta, args.worktree)

    files = parse_diff(diff_text)
    if not files:
        fail("the diff is empty or could not be parsed")

    out_dir = Path(args.out_dir) if args.out_dir else (
        Path.home() / ".sdlc" / args.repo / "pull-requests" / str(args.pr) / "walkthrough"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    diff_path = out_dir / "pr.diff"
    narrative_path = out_dir / "narrative.json"
    diff_path.write_text(diff_text)

    existing: dict[str, Any] | None = None
    if narrative_path.exists():
        try:
            existing = json.loads(narrative_path.read_text())
        except json.JSONDecodeError:
            existing = None

    existing_head = str((existing or {}).get("meta", {}).get("head_sha") or "")
    reuse = bool(existing) and existing_head == meta["head_sha"] and not args.rebuild

    if existing and existing_head and existing_head != meta["head_sha"]:
        backup = out_dir / f"narrative.{existing_head[:7]}.json"
        backup.write_text(json.dumps(existing, indent=2) + "\n")
        print(f"Backup:   {backup}")

    sources, assess = report_sources(args.repo, args.pr)
    fresh = build_scaffold(meta, files, sources, assess)
    if reuse:
        scaffold = existing or fresh
        scaffold.setdefault("meta", {})
        scaffold["meta"].update(fresh["meta"])
        scaffold["sources"] = sources
        scaffold["assess"] = assess
        known = {entry.get("path") for entry in scaffold.get("files", [])}
        for entry in fresh["files"]:
            if entry["path"] not in known:
                scaffold.setdefault("files", []).append(entry)
        print(
            "Narrative: reusing the existing narrative for the same head "
            f"({narrative_path}); pass --rebuild to rebuild it"
        )
    else:
        scaffold = fresh
        print(f"Narrative:{narrative_path}")
    narrative_path.write_text(json.dumps(scaffold, indent=2) + "\n")

    decision = size_decision(
        scaffold["meta"]["stats"], args.min_lines, args.min_files
    )

    print(f"PR:       {meta['repo']}#{meta['pr']} {meta['title']}")
    print(f"Head:     {meta['head_sha'][:12] or 'unknown'} ({meta['head_ref'] or 'unknown'})")
    print(
        "Stats:    "
        f"{decision['files']} files, +{decision['additions']} -{decision['deletions']} "
        f"({decision['changed_lines']} changed lines)"
    )
    print(f"Diff:     {diff_path}")
    if sources:
        print("Reports:  " + ", ".join(sorted(sources)))
    print(
        "Decision: "
        + ("LARGE" if decision["large"] else "SMALL")
        + (" (" + "; ".join(decision["reasons"]) + ")" if decision["reasons"] else "")
    )
    print("WALKTHROUGH_SIZE " + json.dumps(decision))
    return 0


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def slugify(path: str, used: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-").lower() or "file"
    slug = base
    counter = 2
    while slug in used:
        slug = f"{base}-{counter}"
        counter += 1
    used.add(slug)
    return slug


def severity_class(value: str) -> str:
    return {
        "must": "sev-must",
        "should": "sev-should",
        "may": "sev-may",
        "high": "sev-must",
        "medium": "sev-should",
        "low": "sev-may",
    }.get(str(value).lower(), "sev-info")


def change_class(value: str) -> str:
    return {
        "added": "chg-added",
        "deleted": "chg-deleted",
        "renamed": "chg-renamed",
        "modified": "chg-modified",
    }.get(value, "chg-modified")


def cluster_files(
    files: list[FileDiff], reading_order: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    by_path = {item.path: item for item in files}
    seen: set[str] = set()
    clusters: list[dict[str, Any]] = []
    for cluster in reading_order or []:
        paths = [
            path
            for path in cluster.get("files", [])
            if path in by_path and path not in seen
        ]
        if not paths:
            continue
        seen.update(paths)
        clusters.append(
            {
                "title": cluster.get("title") or "Files",
                "why": cluster.get("why") or "",
                "files": paths,
            }
        )
    rest = [item.path for item in files if item.path not in seen]
    if rest:
        clusters.append(
            {
                "title": "Other changes" if clusters else "All changes",
                "why": "" if clusters else "The diff in the order it was produced.",
                "files": rest,
            }
        )
    return clusters, rest


def render_diff(hunk: Hunk, slug: str, cited_lines: set[int]) -> str:
    rows = []
    for line in hunk.lines:
        old = "" if line.old_no is None else str(line.old_no)
        new = "" if line.new_no is None else str(line.new_no)
        marker = {"add": "+", "del": "-", "ctx": " ", "meta": "\\"}[line.kind]
        kind = line.kind
        row_id = ""
        if line.new_no is not None and line.new_no in cited_lines:
            row_id = f' id="file-{slug}-L{line.new_no}"'
        elif line.old_no is not None and line.old_no in cited_lines:
            row_id = f' id="file-{slug}-O{line.old_no}"'
        rows.append(
            f'<tr class="line {kind}"{row_id}>'
            f'<td class="ln">{old}</td>'
            f'<td class="ln">{new}</td>'
            f'<td class="code"><span class="marker">{marker}</span>{esc(line.text)}</td>'
            "</tr>"
        )
    return (
        '<div class="diff-scroll"><table class="diff"><colgroup>'
        '<col class="c-old"><col class="c-new"><col class="c-code"></colgroup><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
    )


def annotation_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("note") or value.get("text") or "")
    return str(value)


def render_annotation(note: str) -> str:
    if not note.strip():
        return ""
    return (
        '<div class="annotation"><div class="annotation-label">Why this hunk</div>'
        f"<p>{esc(note)}</p></div>"
    )


def render_file(
    item: FileDiff,
    entry: dict[str, Any],
    slug: str,
    pr_url: str,
    cited_lines: set[int],
) -> str:
    additions, deletions = file_stats(item)
    stat_items = []
    if additions:
        stat_items.append(f'<span class="add">+{additions}</span>')
    if deletions:
        stat_items.append(f'<span class="del">-{deletions}</span>')
    stat_html = " ".join(stat_items) if stat_items else '<span class="add">+0</span>'
    annotations = entry.get("annotations") or {}
    if isinstance(annotations, list):
        annotations = {
            str(annotation.get("hunk", index)): annotation.get("note", "")
            for index, annotation in enumerate(annotations)
        }
    purpose = entry.get("purpose") or ""
    file_risks = entry.get("risks") or []
    search = " ".join([item.path, entry.get("change_type", ""), purpose]).lower()

    hunk_html = []
    if item.binary:
        hunk_html.append(
            '<p class="binary-note">Binary file. Review it in the GitHub diff.</p>'
        )
    for index, hunk in enumerate(item.hunks):
        note = annotation_text(annotations.get(str(index), ""))
        hunk_html.append(
            f'<div class="hunk" id="{slug}-h{index}">'
            f'<div class="hunk-head"><code>{esc(hunk.header)}</code></div>'
            f"{render_diff(hunk, slug, cited_lines)}"
            f"{render_annotation(note)}"
            "</div>"
        )

    risks_html = ""
    if file_risks:
        risks_html = (
            '<div class="file-risks"><strong>Watch for</strong><ul>'
            + "".join(f"<li>{esc(risk)}</li>" for risk in file_risks)
            + "</ul></div>"
        )

    return (
        f'<section class="file" id="file-{slug}" data-search="{esc(search)}">'
        '<header class="file-head">'
        '<div class="file-title">'
        f'<span class="badge {change_class(item.change_type)}">{esc(item.change_type)}</span>'
        f'<a class="file-path" href="#file-{slug}">{esc(item.path)}</a>'
        '<span class="file-stats">'
        f"{stat_html}"
        "</span>"
        "</div>"
        '<div class="file-actions">'
        f'<button class="ghost" data-copy="{esc(item.path)}">Copy path</button>'
        f'<button class="ghost" data-toggle="{slug}" aria-expanded="true">Collapse</button>'
        f'<a class="ghost" href="{esc(pr_url)}/files" target="_blank" rel="noopener">GitHub</a>'
        "</div>"
        f'<p class="purpose">{esc(purpose)}</p>'
        "</header>"
        f'<div class="file-body">{"".join(hunk_html)}{risks_html}</div>'
        "</section>"
    )


def render_risk(risk: dict[str, Any]) -> str:
    level = str(risk.get("level") or risk.get("severity") or "info")
    source = risk.get("source") or ""
    source_html = f'<span class="source">{esc(source)}</span>' if source else ""
    return (
        f'<li class="risk {severity_class(level)}">'
        f'<span class="pill {severity_class(level)}">{esc(level)}</span>'
        f'<div><strong>{esc(risk.get("title", ""))}</strong>'
        f'<p>{esc(risk.get("detail", ""))}</p>{source_html}</div></li>'
    )


def render_finding(
    finding: dict[str, Any],
    slugs: dict[str, str],
    line_sets: dict[str, dict[str, set[int]]],
) -> str:
    severity = str(finding.get("severity") or "info")
    file_path = finding.get("file") or ""
    line = finding.get("line")
    pointer = ""
    if file_path:
        anchor = slugs.get(file_path)
        label = file_path + (f":{line}" if line else "")
        if anchor:
            href = f"#file-{anchor}"
            try:
                line_number = int(line) if line is not None else None
            except (TypeError, ValueError):
                line_number = None
            if line_number is not None:
                sets = line_sets.get(file_path, {})
                if line_number in sets.get("new", set()):
                    href = f"#file-{anchor}-L{line_number}"
                elif line_number in sets.get("old", set()):
                    href = f"#file-{anchor}-O{line_number}"
            pointer = f'<a class="pointer" href="{href}">{esc(label)}</a>'
        else:
            pointer = f'<span class="pointer">{esc(label)}</span>'
    source = finding.get("source") or ""
    source_html = f'<span class="source">{esc(source)}</span>' if source else ""
    return (
        f'<li class="finding {severity_class(severity)}">'
        f'<span class="pill {severity_class(severity)}">{esc(severity)}</span>'
        f'<div><strong>{esc(finding.get("title", ""))}</strong>'
        f'<p>{esc(finding.get("detail", ""))}</p>'
        f"{pointer}{source_html}</div></li>"
    )


CSS = r"""
:root{
  --bg:#ffffff;--fg:#1f2328;--muted:#59636e;--faint:#818b98;
  --border:#d1d9e0;--card:#f6f8fa;--card-2:#eef2f6;
  --accent:#0969da;--accent-soft:#ddf4ff;
  --add-bg:#e6ffec;--add-fg:#116329;--del-bg:#ffebe9;--del-fg:#a40e26;
  --must:#cf222e;--should:#9a6700;--may:#1a7f37;--info:#0969da;
  --shadow:0 1px 2px rgba(31,35,40,.06);
  --radius:12px;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
html[data-theme="dark"]{
  --bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--faint:#6e7681;
  --border:#30363d;--card:#161b22;--card-2:#1c2129;
  --accent:#58a6ff;--accent-soft:#12283f;
  --add-bg:#12261a;--add-fg:#7ee787;--del-bg:#2d1214;--del-fg:#ffa198;
  --must:#f85149;--should:#d29922;--may:#3fb950;--info:#58a6ff;
  --shadow:0 1px 2px rgba(0,0,0,.3);
}
@media (prefers-color-scheme:dark){
  html[data-theme="auto"]{
    --bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--faint:#6e7681;
    --border:#30363d;--card:#161b22;--card-2:#1c2129;
    --accent:#58a6ff;--accent-soft:#12283f;
    --add-bg:#12261a;--add-fg:#7ee787;--del-bg:#2d1214;--del-fg:#ffa198;
    --must:#f85149;--should:#d29922;--may:#3fb950;--info:#58a6ff;
    --shadow:0 1px 2px rgba(0,0,0,.3);
  }
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
code{font-family:var(--mono);font-size:.9em}
#progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:100}
.layout{display:grid;grid-template-columns:300px minmax(0,1fr);align-items:start}
.sidebar{position:sticky;top:0;height:100vh;overflow-y:auto;padding:24px 20px 40px;
  border-right:1px solid var(--border);background:var(--card)}
.brand{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);margin-bottom:14px}
.sidebar h1{font-size:17px;line-height:1.35;margin:0 0 10px}
.sidebar .meta{font-size:12.5px;color:var(--muted);margin-bottom:16px;word-break:break-word}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:18px}
.stat{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:8px 10px}
.stat b{display:block;font-size:16px;line-height:1.2}
.stat span{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.search{width:100%;padding:9px 11px;border:1px solid var(--border);border-radius:9px;
  background:var(--bg);color:var(--fg);font:inherit;font-size:13px;margin-bottom:16px}
.search:focus{outline:2px solid var(--accent);outline-offset:1px}
nav{font-size:13.5px}
nav .nav-top{display:flex;flex-direction:column;gap:2px;margin-bottom:14px}
nav .nav-top a{padding:4px 8px;border-radius:7px;color:var(--fg);font-weight:600}
nav .nav-top a:hover{background:var(--card-2);text-decoration:none}
.nav-group{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--faint);margin:16px 8px 6px}
.nav-file{display:flex;gap:8px;align-items:baseline;padding:4px 8px;border-radius:7px;
  color:var(--muted);font-family:var(--mono);font-size:11.5px;word-break:break-all}
.nav-file:hover{background:var(--card-2);text-decoration:none}
.nav-file.active{background:var(--accent-soft);color:var(--accent)}
.dot{width:7px;height:7px;border-radius:50%;flex:0 0 7px;margin-top:4px;background:var(--faint)}
.chg-added .dot,nav .dot.added{background:var(--may)}
.chg-deleted .dot,nav .dot.deleted{background:var(--must)}
.chg-renamed .dot,nav .dot.renamed{background:var(--info)}
.chg-modified .dot,nav .dot.modified{background:var(--should)}
.sidebar-actions{display:flex;gap:8px;margin:18px 0 0}
.ghost{border:1px solid var(--border);background:var(--bg);color:var(--muted);
  border-radius:8px;padding:5px 9px;font:inherit;font-size:12px;cursor:pointer}
.ghost:hover{color:var(--fg);border-color:var(--muted)}
.theme{position:fixed;right:18px;bottom:18px;z-index:60;background:var(--card);
  border:1px solid var(--border);color:var(--fg);padding:8px 12px;border-radius:999px;
  font:inherit;font-size:12px;cursor:pointer;box-shadow:var(--shadow)}
main{min-width:0;padding:40px 48px 80px;max-width:1100px}
.hero{margin-bottom:32px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--accent);margin-bottom:8px}
.hero h1{font-size:32px;line-height:1.2;margin:0 0 12px;letter-spacing:-.02em}
.hero .byline{color:var(--muted);font-size:14px;margin-bottom:18px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{background:var(--card);border:1px solid var(--border);border-radius:999px;
  padding:4px 11px;font-size:12.5px;color:var(--muted)}
.chip b{color:var(--fg)}
section.block{margin:0 0 34px}
section.block>h2{font-size:20px;margin:0 0 12px;letter-spacing:-.01em}
.prose{font-size:15.5px;max-width:76ch}
.prose p{margin:0 0 12px}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 20px;box-shadow:var(--shadow)}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.assess{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.assess .stat{background:var(--card)}
.clusters{display:flex;flex-direction:column;gap:12px}
.cluster{border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;
  background:var(--card)}
.cluster h3{margin:0 0 4px;font-size:15px}
.cluster .why{margin:0 0 10px;color:var(--muted);font-size:13.5px}
.cluster ol{margin:0;padding-left:20px}
.cluster li{margin:3px 0;font-family:var(--mono);font-size:12.5px}
.risk-list,.finding-list{list-style:none;margin:0;padding:0;display:flex;
  flex-direction:column;gap:10px}
.risk,.finding{display:flex;gap:12px;align-items:flex-start;background:var(--card);
  border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.risk p,.finding p{margin:2px 0 0;color:var(--muted);font-size:13.5px}
.pill{flex:0 0 auto;font-size:10.5px;font-weight:700;letter-spacing:.06em;
  text-transform:uppercase;padding:3px 8px;border-radius:999px;border:1px solid currentColor}
.sev-must.pill{color:var(--must)}
.sev-should.pill{color:var(--should)}
.sev-may.pill{color:var(--may)}
.sev-info.pill{color:var(--info)}
.source,.pointer{font-size:11.5px;color:var(--faint)}
.pointer{margin-left:8px;font-family:var(--mono)}
.source{margin-left:8px}
.file{border:1px solid var(--border);border-radius:var(--radius);margin:0 0 22px;
  overflow:hidden;background:var(--bg)}
.file-head{padding:16px 18px;background:var(--card);border-bottom:1px solid var(--border)}
.file-title{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.file-path{font-family:var(--mono);font-size:14px;font-weight:600;color:var(--fg);
  word-break:break-all}
.file-stats{font-family:var(--mono);font-size:12px;color:var(--muted)}
.file-stats .add{color:var(--add-fg)}
.file-stats .del{color:var(--del-fg)}
.file-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.purpose{margin:10px 0 0;color:var(--muted);font-size:14px;max-width:80ch}
.file.collapsed .file-body{display:none}
.file.collapsed .file-head{border-bottom:0}
.badge{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
  padding:3px 8px;border-radius:999px;border:1px solid currentColor}
.chg-added.badge{color:var(--may)}
.chg-deleted.badge{color:var(--must)}
.chg-renamed.badge{color:var(--info)}
.chg-modified.badge{color:var(--should)}
.hunk{border-top:1px solid var(--border)}
.hunk:first-child{border-top:0}
.hunk-head{padding:7px 16px;background:var(--card-2);font-size:12px;color:var(--muted);
  border-bottom:1px solid var(--border)}
.diff-scroll{overflow-x:auto;background:var(--bg)}
table.diff{border-collapse:collapse;width:100%;font-family:var(--mono);font-size:12.5px;
  line-height:1.55;tab-size:4}
table.diff col.c-old{width:52px}
table.diff col.c-new{width:52px}
table.diff td{padding:0 10px;vertical-align:top}
td.ln{width:52px;text-align:right;color:var(--faint);user-select:none;
  border-right:1px solid var(--border);background:var(--card);font-size:11.5px}
td.code{white-space:pre;min-width:max-content}
td.code .marker{display:inline-block;width:14px;color:var(--faint);user-select:none}
tr.add td.code{background:var(--add-bg)}
tr.add td.ln{background:var(--add-bg);color:var(--add-fg)}
tr.del td.code{background:var(--del-bg)}
tr.del td.ln{background:var(--del-bg);color:var(--del-fg)}
tr.meta td.code{color:var(--faint);font-style:italic}
.annotation{margin:10px 16px 16px;padding:12px 14px;border-left:3px solid var(--accent);
  background:var(--accent-soft);border-radius:0 9px 9px 0}
.annotation-label{font-size:10.5px;font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;color:var(--accent);margin-bottom:3px}
.annotation p{margin:0;font-size:14px}
.file-risks{margin:0 16px 16px;padding:12px 14px;border-left:3px solid var(--should);
  background:var(--card);border-radius:0 9px 9px 0;font-size:14px}
.file-risks ul{margin:6px 0 0;padding-left:20px}
.binary-note{padding:14px 16px;color:var(--muted)}
.empty{color:var(--muted);font-style:italic}
footer{border-top:1px solid var(--border);padding-top:18px;color:var(--faint);font-size:12.5px}
@media (max-width:900px){
  .layout{grid-template-columns:1fr}
  .sidebar{position:static;height:auto;max-height:none;border-right:0;
    border-bottom:1px solid var(--border)}
  .sidebar .brand,.sidebar h1,.sidebar .meta,.sidebar .stats{display:none}
  .search{margin-bottom:12px}
  nav .nav-top{flex-direction:row;flex-wrap:wrap}
  main{padding:26px 18px 60px}
  .hero h1{font-size:25px}
  .grid-2,.assess{grid-template-columns:1fr}
  body{font-size:14.5px}
}
@media print{
  .sidebar,.theme,#progress,.file-actions{display:none}
  .layout{display:block}
  main{max-width:none;padding:0}
  .file,.card,.cluster{break-inside:avoid;box-shadow:none}
  a{color:inherit;text-decoration:none}
}
"""

JS = r"""
(function(){
  const root=document.documentElement;
  const stored=localStorage.getItem('pw-theme');
  if(stored){root.dataset.theme=stored;}
  const theme=document.getElementById('theme');
  const nextTheme=()=>({auto:'light',light:'dark',dark:'auto'}[root.dataset.theme||'auto']);
  theme.addEventListener('click',()=>{
    root.dataset.theme=nextTheme();
    localStorage.setItem('pw-theme',root.dataset.theme);
    theme.textContent='Theme: '+root.dataset.theme;
  });
  theme.textContent='Theme: '+(root.dataset.theme||'auto');

  const bar=document.getElementById('progress');
  addEventListener('scroll',()=>{
    const h=document.documentElement;
    const max=h.scrollHeight-h.clientHeight;
    bar.style.width=(max>0?(h.scrollTop/max)*100:0)+'%';
  },{passive:true});

  const filter=document.getElementById('filter');
  filter.addEventListener('input',()=>{
    const q=filter.value.trim().toLowerCase();
    document.querySelectorAll('.file').forEach(section=>{
      const hay=(section.dataset.search||'').toLowerCase();
      section.hidden=Boolean(q)&&!hay.includes(q);
    });
    document.querySelectorAll('.nav-file').forEach(link=>{
      const hay=(link.dataset.search||'').toLowerCase();
      link.hidden=Boolean(q)&&!hay.includes(q);
    });
  });

  document.querySelectorAll('[data-toggle]').forEach(button=>{
    button.addEventListener('click',()=>{
      const section=document.getElementById('file-'+button.dataset.toggle);
      const collapsed=section.classList.toggle('collapsed');
      button.textContent=collapsed?'Expand':'Collapse';
      button.setAttribute('aria-expanded',String(!collapsed));
    });
  });
  const collapseAll=document.getElementById('collapse-all');
  if(collapseAll){
    collapseAll.addEventListener('click',()=>{
      const files=[...document.querySelectorAll('.file')];
      const collapse=files.some(file=>!file.classList.contains('collapsed'));
      files.forEach(file=>{
        file.classList.toggle('collapsed',collapse);
        const button=file.querySelector('[data-toggle]');
        if(button){button.textContent=collapse?'Expand':'Collapse';
          button.setAttribute('aria-expanded',String(!collapse));}
      });
      collapseAll.textContent=collapse?'Expand all':'Collapse all';
    });
  }

  document.querySelectorAll('[data-copy]').forEach(button=>{
    button.addEventListener('click',async()=>{
      const text=button.dataset.copy;
      try{await navigator.clipboard.writeText(text);}catch(_){
        const area=document.createElement('textarea');
        area.value=text;document.body.appendChild(area);area.select();
        document.execCommand('copy');area.remove();
      }
      const original=button.textContent;
      button.textContent='Copied';
      setTimeout(()=>{button.textContent=original;},1200);
    });
  });

  const links=new Map(
    [...document.querySelectorAll('.nav-file')].map(link=>[link.getAttribute('href').slice(1),link])
  );
  if('IntersectionObserver' in window && links.size){
    const observer=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{
        if(entry.isIntersecting){
          document.querySelectorAll('.nav-file').forEach(link=>link.classList.remove('active'));
          const link=links.get(entry.target.id);
          if(link){link.classList.add('active');}
        }
      });
    },{rootMargin:'-15% 0px -75% 0px'});
    document.querySelectorAll('.file').forEach(section=>observer.observe(section));
  }
})();
"""


def render_html(narrative: dict[str, Any], files: list[FileDiff]) -> str:
    meta = narrative.get("meta", {})
    stats = meta.get("stats") or diff_stats(files)
    reading_order = narrative.get("reading_order") or []
    clusters, _ = cluster_files(files, reading_order)
    entries = {entry.get("path"): entry for entry in narrative.get("files", [])}

    used: set[str] = set()
    slugs: dict[str, str] = {}
    for item in files:
        slugs[item.path] = slugify(item.path, used)

    line_sets: dict[str, dict[str, set[int]]] = {}
    for item in files:
        line_sets[item.path] = {
            "new": {
                line.new_no
                for hunk in item.hunks
                for line in hunk.lines
                if line.new_no is not None
            },
            "old": {
                line.old_no
                for hunk in item.hunks
                for line in hunk.lines
                if line.old_no is not None
            },
        }
    cited: dict[str, set[int]] = {}
    for finding in narrative.get("findings") or []:
        path = finding.get("file")
        line = finding.get("line")
        try:
            number = int(line) if line is not None else None
        except (TypeError, ValueError):
            number = None
        if path and number is not None:
            cited.setdefault(path, set()).add(number)

    title = meta.get("title") or f"PR #{meta.get('pr', '')}"
    repo = meta.get("repo", "")
    pr = meta.get("pr", "")
    pr_url = meta.get("url") or f"https://github.com/{repo}/pull/{pr}"
    head_sha = meta.get("head_sha", "")
    generated_at = meta.get("generated_at", now_iso())

    marker = json.dumps(
        {"step": "create-pr-walkthrough", "sha": head_sha, "generated_at": generated_at},
        separators=(",", ":"),
    )

    # Sidebar navigation, grouped by reading-order cluster.
    nav_parts = [
        '<nav>',
        '<div class="nav-top">',
        '<a href="#overview">Overview</a>',
        '<a href="#reading-order">Reading order</a>',
        '<a href="#risks">Risks &amp; findings</a>',
        "</div>",
    ]
    for cluster in clusters:
        nav_parts.append(f'<div class="nav-group">{esc(cluster["title"])}</div>')
        for path in cluster["files"]:
            item = next(file for file in files if file.path == path)
            nav_parts.append(
                f'<a class="nav-file" href="#file-{slugs[path]}" '
                f'data-search="{esc(path.lower())}">'
                f'<span class="dot {change_class(item.change_type).split("-")[-1]}"></span>'
                f'<span>{esc(path)}</span></a>'
            )
    nav_parts.append("</nav>")

    # Overview block.
    summary = narrative.get("summary") or ""
    why = narrative.get("why") or ""
    overview = [
        '<header class="hero" id="overview">',
        f'<div class="eyebrow">{esc(repo)} &middot; PR #{esc(pr)}</div>',
        f"<h1>{esc(title)}</h1>",
        '<div class="byline">'
        + (f"by @{esc(meta.get('author'))} &middot; " if meta.get("author") else "")
        + f"{esc(meta.get('base_ref', 'base'))} &larr; {esc(meta.get('head_ref', 'head'))}"
        + f" &middot; reviewed at {esc(head_sha[:12])}"
        + "</div>",
        '<div class="chips">',
        f'<span class="chip"><b>{stats.get("files", len(files))}</b> files</span>',
        f'<span class="chip"><b class="add">+{stats.get("additions", 0)}</b> additions</span>',
        f'<span class="chip"><b class="del">-{stats.get("deletions", 0)}</b> deletions</span>',
        f'<span class="chip"><b>{meta.get("commits", 0)}</b> commits</span>',
        (
            f'<span class="chip"><b>{len(meta.get("closing_issues") or [])}</b> linked issues</span>'
            if meta.get("closing_issues")
            else ""
        ),
        "</div>",
        "</header>",
    ]
    if summary or why:
        overview.append('<section class="block"><h2>What this PR does</h2><div class="prose">')
        if summary:
            overview.append(f"<p>{esc(summary)}</p>")
        if why:
            overview.append(f"<p>{esc(why)}</p>")
        overview.append("</div></section>")

    # Reading order.
    reading_parts = ['<section class="block" id="reading-order">', "<h2>Suggested reading order</h2>"]
    if clusters:
        reading_parts.append('<div class="clusters">')
        for number, cluster in enumerate(clusters, start=1):
            reading_parts.append('<div class="cluster">')
            reading_parts.append(f"<h3>{number}. {esc(cluster['title'])}</h3>")
            if cluster["why"]:
                reading_parts.append(f'<p class="why">{esc(cluster["why"])}</p>')
            reading_parts.append("<ol>")
            for path in cluster["files"]:
                reading_parts.append(
                    f'<li><a href="#file-{slugs[path]}">{esc(path)}</a></li>'
                )
            reading_parts.append("</ol></div>")
        reading_parts.append("</div>")
    else:
        reading_parts.append('<p class="empty">No reading order was supplied.</p>')
    reading_parts.append("</section>")

    # Risks, findings, questions.
    risk_parts = ['<section class="block" id="risks">', "<h2>Risks &amp; findings</h2>"]
    assess = narrative.get("assess") or {}
    if assess:
        risk_parts.append('<div class="assess">')
        for label, key in (("Risk", "risk"), ("Confidence", "confidence"), ("Route", "verdict")):
            if assess.get(key):
                risk_parts.append(
                    f'<div class="stat"><span>{esc(label)}</span><b>{esc(assess[key])}</b></div>'
                )
        risk_parts.append("</div>")
    risks = narrative.get("risks") or []
    if risks:
        risk_parts.append('<h3>Risks</h3><ul class="risk-list">')
        risk_parts.extend(render_risk(risk) for risk in risks)
        risk_parts.append("</ul>")
    findings = narrative.get("findings") or []
    if findings:
        risk_parts.append('<h3>Findings</h3><ul class="finding-list">')
        risk_parts.extend(render_finding(finding, slugs, line_sets) for finding in findings)
        risk_parts.append("</ul>")
    questions = narrative.get("questions") or []
    if questions:
        risk_parts.append('<h3>Open questions</h3><ul>')
        risk_parts.extend(f"<li>{esc(question)}</li>" for question in questions)
        risk_parts.append("</ul>")
    if not (assess or risks or findings or questions):
        risk_parts.append(
            '<p class="empty">No risks or findings were supplied for this walkthrough.</p>'
        )
    risk_parts.append("</section>")

    # File sections, in reading order.
    file_parts = ['<section class="block" id="files"><h2>File by file</h2>']
    rendered: set[str] = set()
    for cluster in clusters:
        for path in cluster["files"]:
            if path in rendered:
                continue
            item = next(file for file in files if file.path == path)
            entry = entries.get(path, {})
            file_parts.append(
                render_file(
                    item, entry, slugs[path], pr_url, cited.get(item.path, set())
                )
            )
            rendered.add(path)
    for item in files:
        if item.path not in rendered:
            entry = entries.get(item.path, {})
            file_parts.append(
                render_file(
                    item,
                    entry,
                    slugs[item.path],
                    pr_url,
                    cited.get(item.path, set()),
                )
            )
    file_parts.append("</section>")

    verdict = narrative.get("verdict") or ""
    verdict_html = (
        f'<section class="block"><div class="card"><strong>Reviewer take</strong>'
        f'<p class="prose">{esc(verdict)}</p></div></section>'
        if verdict
        else ""
    )

    sidebar = (
        '<aside class="sidebar">'
        '<div class="brand">PR walkthrough</div>'
        f"<h1>{esc(title)}</h1>"
        f'<div class="meta">{esc(repo)} &middot; #{esc(pr)}<br>'
        f"{esc(meta.get('base_ref', 'base'))} &larr; {esc(meta.get('head_ref', 'head'))}</div>"
        '<div class="stats">'
        f'<div class="stat"><b>{stats.get("files", len(files))}</b><span>files</span></div>'
        f'<div class="stat"><b>{stats.get("changed_lines", 0)}</b><span>lines changed</span></div>'
        "</div>"
        '<input id="filter" class="search" type="search" '
        'placeholder="Filter files and paths" aria-label="Filter files">'
        + "".join(nav_parts)
        + '<div class="sidebar-actions">'
        '<button class="ghost" id="collapse-all">Collapse all</button>'
        f'<a class="ghost" href="{esc(pr_url)}" target="_blank" rel="noopener">Open PR</a>'
        "</div>"
        "</aside>"
    )

    body = (
        "<main>"
        + "".join(overview)
        + "".join(reading_parts)
        + "".join(risk_parts)
        + "".join(file_parts)
        + verdict_html
        + '<footer>Generated by <code>create-pr-walkthrough</code> at '
        + esc(generated_at)
        + f" for {esc(repo)}#{esc(pr)} at {esc(head_sha[:12])}. "
        + "The page is self-contained and works offline.</footer>"
        + "</main>"
    )

    return (
        "<!doctype html>\n"
        f"<!-- {marker} -->\n"
        '<html lang="en" data-theme="auto">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(title)} &middot; PR #{esc(pr)} walkthrough</title>\n"
        "<style>" + CSS + "</style>\n"
        "</head>\n<body>\n"
        '<div id="progress"></div>\n'
        '<div class="layout">'
        + sidebar
        + body
        + "</div>\n"
        '<button class="theme" id="theme" aria-label="Toggle theme">Theme: auto</button>\n'
        "<script>" + JS + "</script>\n"
        "</body>\n</html>\n"
    )


def cmd_render(args: argparse.Namespace) -> int:
    narrative = json.loads(Path(args.narrative).read_text())
    diff_text = Path(args.diff).read_text(errors="replace")
    files = parse_diff(diff_text)
    if not files:
        fail("the diff is empty or could not be parsed")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(narrative, files))

    print(f"Wrote {out} ({out.stat().st_size:,} bytes, {len(files)} files)")
    return 0


def cmd_size(args: argparse.Namespace) -> int:
    diff_text = Path(args.diff).read_text(errors="replace")
    files = parse_diff(diff_text)
    decision = size_decision(diff_stats(files), args.min_lines, args.min_files)
    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(
            ("LARGE" if decision["large"] else "SMALL")
            + f": {decision['files']} files, {decision['changed_lines']} changed lines"
        )
        for reason in decision["reasons"]:
            print(f"  - {reason}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a self-contained HTML walkthrough for a pull request."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold = subparsers.add_parser(
        "scaffold", help="Fetch the PR diff and write the narrative skeleton."
    )
    scaffold.add_argument("--pr", type=int, required=True)
    scaffold.add_argument("--repo", required=True, help="owner/repository")
    scaffold.add_argument("--out-dir", help="Directory for narrative.json and pr.diff")
    scaffold.add_argument("--worktree", help="Git checkout to use for the diff fallback")
    scaffold.add_argument("--diff-file", help="Use a saved diff instead of fetching one")
    scaffold.add_argument("--meta-file", help="Use saved gh pr view JSON (offline)")
    scaffold.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES)
    scaffold.add_argument("--min-files", type=int, default=DEFAULT_MIN_FILES)
    scaffold.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild narrative.json even when the same head already has one",
    )
    scaffold.set_defaults(func=cmd_scaffold)

    render = subparsers.add_parser("render", help="Render the walkthrough HTML page.")
    render.add_argument("--narrative", required=True)
    render.add_argument("--diff", required=True)
    render.add_argument("--out", required=True)
    render.set_defaults(func=cmd_render)

    size = subparsers.add_parser("size", help="Report whether a diff is large enough.")
    size.add_argument("--diff", required=True)
    size.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES)
    size.add_argument("--min-files", type=int, default=DEFAULT_MIN_FILES)
    size.add_argument("--json", action="store_true")
    size.set_defaults(func=cmd_size)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
