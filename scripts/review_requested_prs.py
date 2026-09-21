#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "PyGithub",
#     "rich",
#     "structlog",
# ]
# ///
"""Deterministic orchestrator for the review-requested-prs skill.

Discovers PRs needing review (requested from you, plus open PRs you have
already reviewed), checks staleness of assess-pr-risk / validate-pr /
verify-pr / review-pr comment markers against each PR's HEAD commit, and
outputs which review steps need to be dispatched.

assess-pr-risk runs in parallel with the validate -> verify -> review chain:
it is stale independently of the chain, never gates a chain step, and is
never gated by one.

All GitHub access goes through PyGithub (token from GITHUB_TOKEN env var
or ``gh auth token`` as fallback).

Usage:
    scripts/review_requested_prs.py [pr-url ... | owner/repo ...]
        [--limit N] [--json] [--dispatch] [--dispatch-prs] [--quiet]
        [--log-level LEVEL] [--exclude-author LOGIN ...] [--sort {id,age}]

Examples:
    # All PRs where you are a requested reviewer
    scripts/review_requested_prs.py

    # Specific repos only
    scripts/review_requested_prs.py acme/api acme/web-app

    # One PR by URL
    scripts/review_requested_prs.py https://github.com/acme/api/pull/42

    # Machine-readable JSON
    scripts/review_requested_prs.py --json

    # Just the dispatch commands, one per line
    scripts/review_requested_prs.py --dispatch
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path

import structlog
from github import Auth, Github
from github.GithubException import GithubException
from rich.console import Console, Group
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

log = structlog.get_logger()

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def configure_logging(level: str) -> None:
    """Configure structlog with the given level name."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            LOG_LEVELS.get(level, logging.WARNING)
        ),
        cache_logger_on_first_use=True,
    )


@contextmanager
def timed(action: str, **kwargs: object) -> Iterator[None]:
    """Log the elapsed time of a code block at debug level."""
    start = time.monotonic()
    log.debug("start", action=action, **kwargs)
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        log.debug("done", action=action, elapsed_s=f"{elapsed:.2f}", **kwargs)


JSON_MARKER_PATTERN = re.compile(r"<!--\s*(\{.*?\})\s*-->")

LEGACY_MARKER_PATTERNS: dict[str, re.Pattern[str]] = {
    "validate-pr": re.compile(r"<!-- validate-pr:([a-f0-9]+) -->"),
    "verify-pr": re.compile(r"<!-- verify-pr:([a-f0-9]+) -->"),
    "review-pr": re.compile(r"<!-- review-pr:([a-f0-9]+) -->"),
}

CHAIN_STEPS = ("validate-pr", "verify-pr", "review-pr")

# assess-pr-risk runs in parallel with the chain: independent staleness,
# no gating in either direction.
PARALLEL_STEPS = ("assess-pr-risk",)

# Every step the skills write markers for.
VALID_STEPS = PARALLEL_STEPS + CHAIN_STEPS

STEP_ORDER: dict[str, int] = {step: index for index, step in enumerate(VALID_STEPS)}

VERDICT_FIELDS: dict[str, str] = {
    "validate-pr": "validate_verdict",
    "verify-pr": "verify_verdict",
}

STEP_TO_FIELD: dict[str, str] = {
    "assess-pr-risk": "assess_commit",
    "validate-pr": "validate_commit",
    "verify-pr": "verify_commit",
    "review-pr": "review_commit",
}

STEP_TO_POSTED_FIELD: dict[str, str] = {
    "assess-pr-risk": "assess_posted",
    "validate-pr": "validate_posted",
    "verify-pr": "verify_posted",
    "review-pr": "review_posted",
}

STEP_TO_VERDICT_FIELD: dict[str, str] = {
    "assess-pr-risk": "assess_verdict",
    "validate-pr": "validate_verdict",
    "verify-pr": "verify_verdict",
    "review-pr": "review_verdict",
}

FIELD_TO_STEP: dict[str, str] = {v: k for k, v in STEP_TO_FIELD.items()}

VERDICT_STYLES: dict[str, str] = {
    "pass": "green",
    "fail": "red",
    "": "dim",
}

VERDICT_DISPLAY: dict[str, str] = {
    "pass": "✅",
    "fail": "❌",
}

# assess-pr-risk report fields. Risk/confidence travel in the marker JSON
# ("risk"/"confidence" keys) and, for reports written before those keys
# existed, are scraped from the report body line
# ("**Risk: High** · **Confidence: Low** · ...").
BODY_RISK_PATTERN = re.compile(r"Risk:\s*(Low|Medium|High)\b", re.IGNORECASE)
BODY_CONFIDENCE_PATTERN = re.compile(r"Confidence:\s*(Low|Medium|High)\b", re.IGNORECASE)

RISK_STYLES: dict[str, str] = {
    "high": "bold red",
    "medium": "yellow",
    "low": "green",
}

# Routing tokens colored by how much reviewer attention they ask for.
ROUTE_STYLES: dict[str, str] = {
    "fast-track": "green",
    "confirm": "green",
    "decide": "yellow",
    "investigate": "yellow",
    "block": "red",
    "hold": "red",
}


@dataclass
class PRReviewState:
    repo: str
    number: int
    title: str = ""
    author: str = ""
    created_at: str = ""
    ready_at: str = ""
    last_comment_at: str = ""
    last_comment_by: str = ""
    draft: bool = False
    head_commit: str = ""
    head_repo: str = ""
    head_branch: str = ""
    last_commit_at: str = ""
    validate_commit: str = ""
    verify_commit: str = ""
    review_commit: str = ""
    assess_commit: str = ""
    validate_posted: bool = False
    verify_posted: bool = False
    review_posted: bool = False
    assess_posted: bool = False
    validate_verdict: str = ""
    verify_verdict: str = ""
    review_verdict: str = ""
    assess_verdict: str = ""
    assess_risk: str = ""
    assess_confidence: str = ""
    approvers: list[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    stale_steps: list[str] = field(default_factory=list)
    skipped: bool = False
    skipped_reason: str = ""
    error: str = ""


def get_github_token() -> str:
    """Return a GitHub token from GITHUB_TOKEN env var or ``gh auth token``."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        log.debug("token_source", source="env")
        return token

    with timed("gh auth token"):
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True,
            )
            token = result.stdout.strip()
        except FileNotFoundError as ex:
            raise RuntimeError(
                "No GITHUB_TOKEN env var and gh CLI not found. "
                "Set GITHUB_TOKEN or install gh from https://cli.github.com/",
            ) from ex
    log.debug("token_source", source="gh")
    return token


def create_client(token: str) -> Github:
    """Create a new authenticated GitHub client from a token."""
    return Github(auth=Auth.Token(token), lazy=True)


def parse_pr_url(arg: str) -> tuple[str, int] | None:
    """Extract (owner/repo, pr_number) from a GitHub PR URL."""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", arg)
    if match:
        return match.group(1), int(match.group(2))
    return None


def is_repo_arg(arg: str) -> bool:
    """Return True if *arg* looks like an owner/repo identifier (not a URL)."""
    return "/" in arg and not arg.startswith("http")


def is_owner_arg(arg: str) -> bool:
    """Return True if *arg* looks like a standalone owner (org or user)."""
    return "/" not in arg and not arg.startswith("http") and len(arg) > 0


def classify_args(args: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split positional arguments into PR URLs, repos, and owners."""
    pr_urls: list[str] = []
    repos: list[str] = []
    owners: list[str] = []
    for arg in args:
        if parse_pr_url(arg):
            pr_urls.append(arg)
        elif is_repo_arg(arg):
            repos.append(arg)
        elif is_owner_arg(arg):
            owners.append(arg)
        else:
            print(f"Warning: unrecognized argument '{arg}', skipping", file=sys.stderr)
    return pr_urls, repos, owners


def _resolve_owner_qualifier(client: Github, owner: str) -> str:
    """Determine whether *owner* is an org or a user on GitHub.

    Returns ``org`` or ``user``. Defaults to ``org`` if the check fails
    (e.g. rate limited), since orgs are the more common case for PR review
    requests.
    """
    with timed("resolve_owner", owner=owner):
        try:
            client.get_organization(owner)
            return "org"
        except GithubException:
            return "user"


def _search_prs(
    client: Github,
    query: str,
    limit: int,
    seen: set[tuple[str, int]],
) -> list[PRReviewState]:
    """Run a search query and return PRs not already in *seen*.

    Does not mutate *seen*, so concurrent discovery queries can run without
    racing; the caller merges and de-duplicates the batches in priority order.
    Silently skips queries that fail with validation errors (e.g. when an
    owner name is valid as an org but not as a user, or vice versa).
    """
    found: list[PRReviewState] = []
    with timed("search_issues", query=query, limit=limit):
        try:
            results = client.search_issues(query)
            for issue in islice(results, limit):
                repo_full = (
                    issue.repository_url.rsplit("/", 2)[-2]
                    + "/"
                    + issue.repository_url.rsplit("/", 2)[-1]
                )
                if (repo_full, issue.number) in seen:
                    continue
                found.append(
                    PRReviewState(
                        repo=repo_full,
                        number=issue.number,
                        title=issue.title,
                        author=issue.user.login if issue.user else "",
                    ),
                )
        except GithubException as ex:
            log.debug("search_failed", query=query, error=str(ex))
    return found


def discover_prs(
    client: Github,
    token: str,
    pr_urls: list[str],
    repos: list[str],
    owners: list[str],
    limit: int,
    include_drafts: bool = False,
    exclude_authors: list[str] | None = None,
) -> list[PRReviewState]:
    """Build the list of target PRs from explicit URLs and/or repo search.

    Discovery combines two search queries: PRs requesting the user's review
    and open PRs the user has already reviewed. The second query keeps PRs
    whose review request was consumed (e.g. by submitting a comment review)
    visible until they are closed or fully approved. The two queries run
    concurrently, each against its own client; their results are merged with
    review-requested PRs taking priority, and the overall *limit* applies
    across both.
    """
    prs: list[PRReviewState] = []
    seen: set[tuple[str, int]] = set()

    for url in pr_urls:
        parsed = parse_pr_url(url)
        if parsed:
            repo, number = parsed
            key = (repo, number)
            if key not in seen:
                seen.add(key)
                prs.append(PRReviewState(repo=repo, number=number))

    should_search = len(repos) > 0 or len(owners) > 0 or len(pr_urls) == 0
    if should_search:
        filters = ""
        if not include_drafts:
            filters += " draft:false"
        for repo in repos:
            filters += f" repo:{repo}"
        for owner in owners:
            qualifier = _resolve_owner_qualifier(client, owner)
            filters += f" {qualifier}:{owner}"
        for author in exclude_authors or []:
            filters += f" -author:{author}"

        queries = (
            f"is:pr is:open review-requested:@me -author:@me{filters}",
            f"is:pr is:open reviewed-by:@me -author:@me sort:updated-desc{filters}",
        )
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            futures = [
                executor.submit(_search_prs, create_client(token), query, limit, seen)
                for query in queries
            ]
            batches = [future.result() for future in futures]

        # Review-requested PRs take priority; previously-reviewed PRs fill the
        # remaining slots up to the overall limit.
        for batch in batches:
            for candidate in batch:
                key = (candidate.repo, candidate.number)
                if key in seen:
                    continue
                seen.add(key)
                prs.append(candidate)
                if len(prs) >= limit:
                    break
            if len(prs) >= limit:
                break

    log.debug(
        "discovered_prs",
        count=len(prs),
        from_urls=len(pr_urls),
        from_search=len(prs) - len(pr_urls),
    )
    return prs


GRAPHQL_PR_QUERY = """
query($owner:String!,$name:String!,$number:Int!){
  repository(owner:$owner,name:$name){
    pullRequest(number:$number){
      headRefOid
      headRefName
      headRepository{nameWithOwner}
      isDraft
      additions
      deletions
      author{login}
      createdAt
      commits(last:1){nodes{commit{committedDate}}}
      reviews(last:100){nodes{state author{login} submittedAt body}}
      comments(last:100){nodes{body createdAt author{login}}}
      reviewThreads(first:100){nodes{comments(last:100){nodes{body createdAt author{login}}}}}
      timelineItems(itemTypes:[READY_FOR_REVIEW_EVENT],last:1){nodes{... on ReadyForReviewEvent{createdAt}}}
    }
  }
}
"""


def _format_iso(value: str | None) -> str:
    """Normalize a GraphQL ISO-8601 timestamp (``Z`` suffix) to offset form."""
    if not value:
        return ""
    return value.replace("Z", "+00:00")


def _parse_iso(value: str | None) -> datetime | None:
    """Parse a GraphQL ISO-8601 timestamp into an aware datetime."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_pr_data(client: Github, pr: PRReviewState) -> None:
    """Populate *pr* from one GraphQL query, then scan local report files.

    A single ``POST /graphql`` replaces the dozen REST round trips that
    fetching the head commit and scanning activity separately required, and
    draws on the GraphQL rate-limit budget rather than the core budget. The
    ``last:100`` / ``first:100`` connections deliberately keep the most recent
    activity, which is what the marker logic (most recent match wins) needs.
    """
    with timed("fetch_pr_data", repo=pr.repo, pr=pr.number):
        owner, name = pr.repo.split("/", 1)
        _headers, data = client.requester.graphql_query(
            GRAPHQL_PR_QUERY,
            {"owner": owner, "name": name, "number": pr.number},
        )
        pull = data["data"]["repository"]["pullRequest"]

        pr.head_commit = pull["headRefOid"]
        pr.head_repo = (pull["headRepository"] or {}).get("nameWithOwner") or pr.repo
        pr.head_branch = pull["headRefName"] or ""
        pr.draft = pull["isDraft"]
        pr.additions = pull["additions"] or 0
        pr.deletions = pull["deletions"] or 0
        pr.author = (pull["author"] or {}).get("login", "")
        pr.created_at = _format_iso(pull["createdAt"])
        commits = pull["commits"]["nodes"]
        if commits:
            pr.last_commit_at = _format_iso(commits[-1]["commit"]["committedDate"])
        ready_times = [
            node["createdAt"]
            for node in pull["timelineItems"]["nodes"]
            if node.get("createdAt")
        ]
        if ready_times and not pr.draft:
            pr.ready_at = _format_iso(max(ready_times))

        for comment in pull["comments"]["nodes"]:
            login = (comment.get("author") or {}).get("login", "")
            _note_last_comment(pr, _parse_iso(comment.get("createdAt")), login)
            _parse_markers(comment.get("body") or "", pr, posted=True)

        for thread in pull["reviewThreads"]["nodes"]:
            for comment in thread["comments"]["nodes"]:
                login = (comment.get("author") or {}).get("login", "")
                _note_last_comment(pr, _parse_iso(comment.get("createdAt")), login)
                _parse_markers(comment.get("body") or "", pr, posted=True)

        latest_state: dict[str, str] = {}
        for review in pull["reviews"]["nodes"]:
            login = (review.get("author") or {}).get("login", "")
            _note_last_comment(pr, _parse_iso(review.get("submittedAt")), login)
            _parse_markers(review.get("body") or "", pr, posted=True)
            if login and review["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
                latest_state[login] = review["state"]
        pr.approvers = sorted(u for u, s in latest_state.items() if s == "APPROVED")

        check_local_markers(pr)

    log.debug("fetched_pr_data", repo=pr.repo, pr=pr.number, sha=pr.head_commit[:8])


SDLC_REVIEW_DIR = Path.home() / ".sdlc"


def _extract_assess_fields(text: str, data: dict, pr: PRReviewState) -> None:
    """Pull risk and confidence for an assess-pr-risk marker into *pr*.

    Prefers the marker's own ``risk``/``confidence`` keys; falls back to
    scraping the report body line from the surrounding *text* for reports
    written before the keys existed. Overwrites only when a value is found,
    so the most recent report wins without erasing older data.
    """
    risk = str(data.get("risk", "")).lower()
    confidence = str(data.get("confidence", "")).lower()
    if risk not in ("low", "medium", "high"):
        match = BODY_RISK_PATTERN.search(text)
        risk = match.group(1).lower() if match else ""
    if confidence not in ("low", "medium", "high"):
        match = BODY_CONFIDENCE_PATTERN.search(text)
        confidence = match.group(1).lower() if match else ""
    if risk:
        pr.assess_risk = risk
    if confidence:
        pr.assess_confidence = confidence


def _parse_markers(text: str, pr: PRReviewState, posted: bool) -> None:
    """Extract marker data from text and update *pr* in place.

    Supports both the new JSON format ``<!-- {"step":"validate-pr","sha":"...","verdict":"pass"} -->``
    and the legacy format ``<!-- validate-pr:SHA -->``.
    Overwrites on each match so the most recent marker wins.
    """
    for match in JSON_MARKER_PATTERN.finditer(text):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        step = data.get("step", "")
        if step not in VALID_STEPS:
            continue
        sha = data.get("sha", "")
        verdict = data.get("verdict", "")
        if sha:
            setattr(pr, STEP_TO_FIELD[step], sha)
            setattr(pr, STEP_TO_POSTED_FIELD[step], posted)
            if verdict:
                setattr(pr, STEP_TO_VERDICT_FIELD[step], verdict)
            if step == "assess-pr-risk":
                _extract_assess_fields(text, data, pr)

    for step, pattern in LEGACY_MARKER_PATTERNS.items():
        field_name = STEP_TO_FIELD[step]
        if getattr(pr, field_name):
            continue
        match = pattern.search(text)
        if match:
            setattr(pr, field_name, match.group(1))
            setattr(pr, STEP_TO_POSTED_FIELD[step], posted)


def _note_last_comment(pr: PRReviewState, when: datetime | None, login: str | None) -> None:
    """Record *when* as the PR's last comment if it is newer than what is stored."""
    if when is None:
        return
    iso = when.isoformat()
    if pr.last_comment_at and iso <= pr.last_comment_at:
        return
    pr.last_comment_at = iso
    pr.last_comment_by = login or ""


def check_local_markers(pr: PRReviewState) -> None:
    """Scan local report files for review-skill markers.

    Markers posted to GitHub are read from the GraphQL response in
    :func:`fetch_pr_data`; this covers the case where posting to GitHub is
    disabled or a marker only exists locally, at
    ``~/.sdlc/<owner>/<repo>/pull-requests/<pr>/``.
    """
    local_dir = SDLC_REVIEW_DIR / pr.repo / "pull-requests" / str(pr.number)
    if not local_dir.is_dir():
        return

    for step in VALID_STEPS:
        field_name = STEP_TO_FIELD[step]
        if getattr(pr, field_name):
            continue

        # Prefer the file matching the current HEAD commit, if any.
        # Reports are named with the short (7-char) SHA; accept a full
        # SHA name too for older files.
        for name in (f"{step}.{pr.head_commit}.md", f"{step}.{pr.head_commit[:7]}.md"):
            head_file = local_dir / name
            if head_file.is_file():
                _parse_markers(head_file.read_text(errors="replace"), pr, posted=False)
                if getattr(pr, field_name):
                    break
        if getattr(pr, field_name):
            continue

        # Fall back to the most recently modified file for this step.
        step_files = sorted(
            local_dir.glob(f"{step}.*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        for md_file in step_files:
            _parse_markers(md_file.read_text(errors="replace"), pr, posted=False)
            if getattr(pr, field_name):
                break

    log.debug(
        "local_markers_checked",
        repo=pr.repo,
        pr=pr.number,
        assess_commit=pr.assess_commit[:8] or "none",
        validate_commit=pr.validate_commit[:8] or "none",
        verify_commit=pr.verify_commit[:8] or "none",
        review_commit=pr.review_commit[:8] or "none",
        assess_verdict=pr.assess_verdict or "none",
        assess_risk=pr.assess_risk or "none",
        assess_confidence=pr.assess_confidence or "none",
        validate_verdict=pr.validate_verdict or "none",
        verify_verdict=pr.verify_verdict or "none",
        review_verdict=pr.review_verdict or "none",
    )


def determine_stale_steps(pr: PRReviewState) -> list[str]:
    """Return the ordered list of review steps that are stale for *pr*.

    assess-pr-risk comes first so it can be dispatched concurrently with the
    first stale chain step; it is stale independently of the chain.
    """
    head = pr.head_commit
    if not head:
        return []

    if (
        pr.assess_commit == head
        and pr.validate_commit == head
        and pr.verify_commit == head
        and pr.review_commit == head
    ):
        return []

    steps: list[str] = []
    if pr.assess_commit != head:
        steps.append("assess-pr-risk")

    if pr.validate_commit != head:
        return steps + ["validate-pr", "verify-pr", "review-pr"]

    if pr.verify_commit != head:
        return steps + ["verify-pr", "review-pr"]

    if pr.review_commit != head:
        steps.append("review-pr")

    return steps


def build_summary_table(prs: list[PRReviewState]) -> Group:
    """Build Rich tables grouped by repository, summarizing PR review states."""
    tables: list[Table] = []
    for repo, repo_prs in _group_by_repo(prs):
        table = Table(title=repo, title_style="bold cyan", show_header=True)
        table.add_column("PR", style="blue", justify="right")
        table.add_column("Author")
        table.add_column("Age", justify="right")
        table.add_column("Commit age", justify="right")
        table.add_column("Last comment", justify="right")
        table.add_column("HEAD", justify="center")
        table.add_column("Diff", justify="right")
        table.add_column("Validate", justify="center")
        table.add_column("Verify", justify="center")
        table.add_column("Review", justify="center")
        table.add_column("Risk", justify="center")
        table.add_column("Status")
        table.add_column("Approver")

        for pr in repo_prs:
            status = (
                f"[red]Error: {pr.error}[/red]"
                if pr.error
                else "[green]Ready for approval[/green]"
                if not pr.stale_steps
                else "[bold yellow]Needs review[/bold yellow]"
            )
            approver_col = (
                f"[green]{', '.join(pr.approvers)}[/green]"
                if pr.approvers
                else "[dim]—[/dim]"
            )
            head_col = (
                f"[blue]{pr.head_commit[:8]}[/blue]"
                if pr.head_commit
                else "[dim]—[/dim]"
            )
            validate_col = _marker_cell(
                pr.validate_commit, pr.validate_posted, pr.validate_verdict, pr.head_commit,
                _step_report_path(pr, "validate_commit"),
            )
            verify_col = _marker_cell(
                pr.verify_commit, pr.verify_posted, pr.verify_verdict, pr.head_commit,
                _step_report_path(pr, "verify_commit"),
            )
            review_col = _marker_cell(
                pr.review_commit, pr.review_posted, pr.review_verdict, pr.head_commit,
                _step_report_path(pr, "review_commit"),
            )
            assess_col = _assess_cell(pr)
            table.add_row(
                _pr_cell(pr),
                pr.author or "[dim]—[/dim]",
                _age_cell(pr.ready_at or pr.created_at),
                _age_cell(pr.last_commit_at),
                _age_cell(pr.last_comment_at, pr.last_comment_by),
                head_col,
                f"[green]+{pr.additions}[/green] [red]-{pr.deletions}[/red]",
                validate_col,
                verify_col,
                review_col,
                assess_col,
                status,
                approver_col,
            )
        tables.append(table)
    return Group(*tables)


def _group_by_repo(prs: list[PRReviewState]) -> list[tuple[str, list[PRReviewState]]]:
    """Group PRs by repo, preserving order of first appearance."""
    groups: dict[str, list[PRReviewState]] = {}
    order: list[str] = []
    for pr in prs:
        if pr.repo not in groups:
            groups[pr.repo] = []
            order.append(pr.repo)
        groups[pr.repo].append(pr)
    return [(repo, groups[repo]) for repo in order]


def _age_cell(created_at: str, by: str = "") -> str:
    """Return a compact age string (e.g. 3h, 2d by alice) for a timestamp."""
    if not created_at:
        return "[dim]—[/dim]"
    seconds = (datetime.now(timezone.utc) - datetime.fromisoformat(created_at)).total_seconds()
    style = "bold red" if seconds >= 86400 else "dim"
    if seconds < 3600:
        age = f"{int(seconds // 60)}m"
    elif seconds < 48 * 3600:
        age = f"{int(seconds // 3600)}h"
    else:
        age = f"{int(seconds // 86400)}d"
    suffix = f" by {by}" if by else ""
    return f"[{style}]{age}{suffix}[/{style}]"


def _pr_cell(pr: PRReviewState) -> str:
    """Return the PR number cell as a hyperlink to the GitHub pull request."""
    url = f"https://github.com/{pr.repo}/pull/{pr.number}"
    label = f"#{pr.number}{' [dim](draft)[/dim]' if pr.draft else ''}"
    return f"[link={url}]{label}[/link]"


def _step_report_path(pr: PRReviewState, commit_field: str) -> Path | None:
    """Return the local report file for a step marker, if it exists.

    Two naming conventions are supported:

    * ``<step>.<sha>.md`` (full or short SHA in the filename), the canonical
      per-run report written by the skills.
    * ``<step>.report.md``, a stable symlink to the most recent run's report
      (also accepted as a plain file for older runs).
    """
    commit = getattr(pr, commit_field)
    if not commit:
        return None
    step = FIELD_TO_STEP[commit_field]
    local_dir = SDLC_REVIEW_DIR / pr.repo / "pull-requests" / str(pr.number)
    exact = local_dir / f"{step}.{commit}.md"
    if exact.is_file():
        return exact
    matches = sorted(local_dir.glob(f"{step}.{commit[:7]}*.md"))
    if matches:
        return matches[0]
    report = local_dir / f"{step}.report.md"
    if report.is_file():
        return report
    return None


def _assess_cell(pr: PRReviewState) -> str:
    """Return the Risk column cell for assess-pr-risk.

    Shows the risk/confidence letters (risk colored by severity, confidence
    dim) followed by the routing token colored by how much reviewer attention
    it asks for, e.g. ``H/L hold (local)``. Falls back to the plain marker
    display when the report carries no risk data.
    """
    if not pr.assess_commit:
        return "[dim]—[/dim]"
    location = "github" if pr.assess_posted else "local"
    parts: list[str] = []
    if pr.assess_risk or pr.assess_confidence:
        risk_letter = pr.assess_risk[:1].upper() if pr.assess_risk else "—"
        conf_letter = pr.assess_confidence[:1].upper() if pr.assess_confidence else "—"
        risk_style = RISK_STYLES.get(pr.assess_risk, "dim")
        parts.append(f"[{risk_style}]{risk_letter}[/{risk_style}][dim]/{conf_letter}[/dim]")
    if pr.assess_verdict:
        route_style = ROUTE_STYLES.get(pr.assess_verdict, "dim")
        parts.append(f"[{route_style}]{pr.assess_verdict}[/{route_style}]")
    if parts:
        cell = " ".join(parts) + f" [dim]({location})[/dim]"
    else:
        base_style = "blue" if pr.assess_posted else "dim"
        cell = f"[{base_style}]{location}[/{base_style}]"
    if pr.assess_commit != pr.head_commit:
        cell += f" [red]{pr.assess_commit[:8]}[/red]"
    report_path = _step_report_path(pr, "assess_commit")
    if report_path:
        return f"[link={report_path.as_uri()}]{cell}[/link]"
    return cell


def _marker_cell(
    commit: str,
    posted: bool,
    verdict: str,
    head_commit: str,
    report_path: Path | None = None,
) -> str:
    """Return a display string for a marker column with verdict and SHA indicator.

    The SHA is shown only when it does not match *head_commit* (stale), colored
    red; when it matches, it is omitted since the HEAD column already shows it.
    The verdict retains its own color (pass=green, fail=red). When
    *report_path* is given, the cell becomes a hyperlink that opens the
    associated report file.
    """
    if not commit:
        return "[dim]—[/dim]"
    location = "github" if posted else "local"
    short = commit[:8]
    is_current = commit == head_commit
    if not verdict:
        base_style = "blue" if posted else "dim"
        cell = f"[{base_style}]{location}[/{base_style}]"
        if not is_current:
            cell += f" [red]{short}[/red]"
    else:
        verdict_style = VERDICT_STYLES.get(verdict, "dim")
        verdict_text = VERDICT_DISPLAY.get(verdict, verdict)
        cell = f"[{verdict_style}]{verdict_text}[/{verdict_style}]"
        if not is_current:
            cell += f" [red]{short}[/red]"
        cell += f" ({location})"
    if report_path:
        return f"[link={report_path.as_uri()}]{cell}[/link]"
    return cell


def format_dispatch_commands(prs: list[PRReviewState]) -> str:
    """Return dispatch commands for PRs needing work, separated by --- per PR.

    Steps after a failed prior step are skipped (e.g. if validate-pr failed,
    verify-pr and review-pr are not dispatched).
    """
    blocks: list[str] = []
    for pr in prs:
        steps = effective_stale_steps(pr)
        if not steps:
            continue
        lines = [f"/{step} {pr.number} {pr.repo}" for step in steps]
        blocks.append("\n".join(lines))
    return "\n---\n".join(blocks)


def effective_stale_steps(pr: PRReviewState) -> list[str]:
    """Return the stale steps not skipped because an earlier chain step failed.

    A failed chain step cuts off the chain steps at and after it, but
    assess-pr-risk is never cut off: it neither gates nor is gated.
    """
    cutoff = len(CHAIN_STEPS) + 1
    for step, field_name in VERDICT_FIELDS.items():
        if getattr(pr, field_name) == "fail":
            cutoff = STEP_ORDER[step] + 1
    chain = [
        s for s in pr.stale_steps
        if s in CHAIN_STEPS and STEP_ORDER[s] < cutoff
    ]
    parallel = [s for s in pr.stale_steps if s in PARALLEL_STEPS]
    return parallel + chain


def format_review_full_commands(prs: list[PRReviewState]) -> str:
    """Return self-contained /review-pr-full commands, separated by --- per PR.

    Each command carries the precomputed stale steps and the head repo/branch
    so the receiving review-pr-full session can start immediately without
    re-querying GitHub for staleness or PR status. Steps after a failed prior
    step are skipped, same as format_dispatch_commands.
    """
    blocks: list[str] = []
    for pr in prs:
        steps = effective_stale_steps(pr)
        if not steps:
            continue
        parts = [
            f"/review-pr-full {pr.number} {pr.repo}",
            f"--steps {','.join(steps)}",
        ]
        if pr.head_repo:
            parts.append(f"--head-repo {pr.head_repo}")
        if pr.head_branch:
            parts.append(f"--head-branch {pr.head_branch}")
        blocks.append(" ".join(parts))
    return "\n---\n".join(blocks)


def format_json(prs: list[PRReviewState]) -> str:
    """Return a JSON representation of all PR review states."""
    return json.dumps([asdict(pr) for pr in prs], indent=2)


def process_pr(
    token: str,
    pr: PRReviewState,
    include_drafts: bool = False,
    exclude_authors: list[str] | None = None,
) -> PRReviewState:
    """Process a single PR: fetch data and markers, determine stale steps.

    Creates its own GitHub client for thread safety. Skips draft PRs unless
    *include_drafts* is True. Skips PRs whose author is in *exclude_authors*.
    """
    with timed("process_pr", repo=pr.repo, pr=pr.number):
        client = create_client(token)
        try:
            fetch_pr_data(client, pr)
            if exclude_authors and pr.author in exclude_authors:
                pr.skipped = True
                pr.skipped_reason = "excluded_author"
                log.info("skip_excluded_author", repo=pr.repo, pr=pr.number, author=pr.author)
                return pr
            if pr.draft and not include_drafts:
                pr.skipped = True
                pr.skipped_reason = "draft"
                log.info("skip_draft", repo=pr.repo, pr=pr.number)
                return pr
            pr.stale_steps = determine_stale_steps(pr)
            if not pr.stale_steps:
                pr.skipped = True
        except GithubException as ex:
            pr.error = str(ex)
            log.warning("pr_error", repo=pr.repo, pr=pr.number, error=str(ex))
    return pr


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover PRs needing review and determine which review steps "
            "(assess-pr-risk, validate-pr, verify-pr, review-pr) are stale."
        ),
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help=(
            "PR URLs (https://github.com/owner/repo/pull/N) and/or repos "
            "(owner/repo). With no arguments, searches all PRs where you are "
            "a requested reviewer."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of PRs to discover via search (default: 100).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of a markdown table.",
    )
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help="Output only the dispatch commands (one per line) for PRs needing work.",
    )
    parser.add_argument(
        "--dispatch-prs",
        action="store_true",
        help=(
            "Output one self-contained /review-pr-full command per PR needing work, "
            "carrying the precomputed stale steps and head refs."
        ),
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Include draft PRs in the dispatch output (excluded by default).",
    )
    parser.add_argument(
        "--exclude-author",
        nargs="*",
        default=["dependabot[bot]"],
        metavar="LOGIN",
        help="GitHub logins of PR authors to exclude (default: dependabot[bot]).",
    )
    parser.add_argument(
        "--sort",
        choices=("id", "age"),
        default="id",
        help="Sort order: 'id' (PR number, descending, default) or 'age' "
        "(oldest first, measured from the most recent draft -> ready "
        "transition or from opening when there is none).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output for PRs that are ready for approval.",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS.keys(),
        default="warning",
        help="Logging verbosity (default: warning). Use 'debug' to see API call timings.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of PRs to process in parallel (default: 8).",
    )
    args = parser.parse_args()

    configure_logging(args.log_level)

    try:
        token = get_github_token()
    except RuntimeError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1

    client = create_client(token)
    pr_urls, repos, owners = classify_args(args.targets)
    prs = discover_prs(
        client,
        token,
        pr_urls,
        repos,
        owners,
        args.limit,
        include_drafts=args.draft,
        exclude_authors=args.exclude_author,
    )

    if not prs:
        print("No PRs found needing review.")
        return 0

    log.info("processing_prs", count=len(prs), workers=args.workers)
    console = Console()
    with (
        timed("process_all_prs", count=len(prs), workers=args.workers),
        ThreadPoolExecutor(max_workers=min(args.workers, len(prs))) as executor,
        Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress,
    ):
        task = progress.add_task(
            f"Processing PRs (0/{len(prs)})",
            total=len(prs),
        )
        futures = {
            executor.submit(process_pr, token, pr, args.draft, args.exclude_author): pr for pr in prs
        }
        for future in as_completed(futures):
            future.result()
            progress.advance(task)
            completed = progress.tasks[task].completed
            progress.update(
                task,
                description=f"Processing PRs ({completed}/{len(prs)})",
            )

    if args.sort == "age":
        # Oldest first, so the largest age (descending age) comes first.
        prs.sort(key=lambda pr: ((pr.ready_at or pr.created_at) == "", pr.ready_at or pr.created_at or ""))
    else:
        prs.sort(key=lambda pr: pr.number, reverse=True)

    if args.quiet:
        prs = [pr for pr in prs if pr.stale_steps or pr.error]

    log.info(
        "done",
        total=len(prs),
        needs_review=sum(1 for p in prs if p.stale_steps),
        skipped=sum(1 for p in prs if p.skipped),
        errors=sum(1 for p in prs if p.error),
    )

    if args.json:
        print(format_json(prs))
    elif args.dispatch:
        commands = format_dispatch_commands(prs)
        if commands:
            print(commands)
        else:
            print(f"processed {len(prs)} PRs, nothing to dispatch")
    elif args.dispatch_prs:
        commands = format_review_full_commands(prs)
        if commands:
            print(commands)
        else:
            print(f"processed {len(prs)} PRs, nothing to dispatch")
    else:
        console.print(build_summary_table(prs))

    return 0


if __name__ == "__main__":
    sys.exit(main())
