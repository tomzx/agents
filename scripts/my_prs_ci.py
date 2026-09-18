#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "PyGithub",
#     "rich",
#     "structlog",
# ]
# ///
"""Deterministic orchestrator for the handle-failing-pr-ci skill.

Discovers the authenticated user's open pull requests, resolves each PR's
combined CI status from its head commit's ``statusCheckRollup``, and reports
which PRs have failing checks. With ``--dispatch`` it emits one
``/handle-pr-ci`` command per failing PR.

All GitHub access goes through PyGithub (token from GITHUB_TOKEN env var
or ``gh auth token`` as fallback).

Usage:
    scripts/my_prs_ci.py [owner/repo ... | pr-url ...]
        [--limit N] [--json] [--dispatch] [--only-failing] [--draft]
        [--exclude-check NAME ...] [--include-check NAME ...] [--quiet]
        [--log-level LEVEL] [--workers N]

Examples:
    # All of my open PRs across GitHub
    scripts/my_prs_ci.py

    # Only PRs in specific repos
    scripts/my_prs_ci.py acme/api acme/web-app

    # One PR by URL
    scripts/my_prs_ci.py https://github.com/acme/api/pull/42

    # Machine-readable JSON
    scripts/my_prs_ci.py --json

    # Dispatch commands for failing PRs, one per line
    scripts/my_prs_ci.py --dispatch

    # Exclude a flaky or known-irrelevant check (repeatable, globs allowed)
    scripts/my_prs_ci.py --exclude-check "PR Review Bot Comments Addressed" \\
        --exclude-check "buildkite/*"

    # Include only specific checks, excluding all others
    scripts/my_prs_ci.py --include-check "buildkite/*"
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
from fnmatch import fnmatch
from itertools import islice

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

FAILING_CONCLUSIONS = {
    "FAILURE",
    "TIMED_OUT",
    "ACTION_REQUIRED",
    "STARTUP_FAILURE",
    "CANCELLED",
}
PENDING_STATES = {
    "PENDING",
    "EXPECTED",
    "QUEUED",
    "IN_PROGRESS",
    "WAITING",
    "REQUESTED",
}

STATE_DISPLAY: dict[str, tuple[str, str]] = {
    "passing": ("green", "pass"),
    "failing": ("red", "fail"),
    "pending": ("yellow", "pending"),
    "none": ("dim", "none"),
    "error": ("red", "error"),
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


@dataclass
class CheckInfo:
    name: str
    status: str = ""


@dataclass
class PRCIState:
    repo: str
    number: int
    title: str = ""
    author: str = ""
    url: str = ""
    created_at: str = ""
    updated_at: str = ""
    draft: bool = False
    head_commit: str = ""
    head_branch: str = ""
    head_repo: str = ""
    mergeable: str = ""
    review_decision: str = ""
    checks_state: str = "none"
    failing_checks: list[CheckInfo] = field(default_factory=list)
    pending_checks: list[CheckInfo] = field(default_factory=list)
    excluded_checks: list[CheckInfo] = field(default_factory=list)
    total_checks: int = 0
    considered_checks: int = 0
    error: str = ""

    @property
    def failing(self) -> bool:
        return self.checks_state == "failing"


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


def classify_args(args: list[str]) -> tuple[list[str], list[str]]:
    """Split positional arguments into PR URLs and repos."""
    pr_urls: list[str] = []
    repos: list[str] = []
    for arg in args:
        if parse_pr_url(arg):
            pr_urls.append(arg)
        elif "/" in arg and not arg.startswith("http"):
            repos.append(arg)
        else:
            print(f"Warning: unrecognized argument '{arg}', skipping", file=sys.stderr)
    return pr_urls, repos


def _search_prs(
    client: Github,
    query: str,
    limit: int,
    seen: set[tuple[str, int]],
) -> list[PRCIState]:
    """Run a search query and return my PRs not already in *seen*."""
    found: list[PRCIState] = []
    with timed("search_issues", query=query, limit=limit):
        try:
            results = client.search_issues(query)
            for issue in islice(results, limit):
                parts = issue.repository_url.rsplit("/", 2)
                repo_full = parts[-2] + "/" + parts[-1]
                if (repo_full, issue.number) in seen:
                    continue
                found.append(
                    PRCIState(
                        repo=repo_full,
                        number=issue.number,
                        title=issue.title,
                        author=issue.user.login if issue.user else "",
                        url=issue.html_url,
                    ),
                )
        except GithubException as ex:
            log.debug("search_failed", query=query, error=str(ex))
    return found


def discover_prs(
    client: Github,
    pr_urls: list[str],
    repos: list[str],
    limit: int,
    include_drafts: bool,
) -> list[PRCIState]:
    """Build the list of my open PRs from explicit URLs and/or search."""
    prs: list[PRCIState] = []
    seen: set[tuple[str, int]] = set()

    for url in pr_urls:
        parsed = parse_pr_url(url)
        if parsed:
            repo, number = parsed
            key = (repo, number)
            if key not in seen:
                seen.add(key)
                prs.append(PRCIState(repo=repo, number=number, url=url))

    should_search = len(repos) > 0 or len(pr_urls) == 0
    if should_search:
        filters = "" if include_drafts else " draft:false"
        for repo in repos:
            filters += f" repo:{repo}"
        query = f"is:pr is:open author:@me{filters}"
        with timed("search_issues", query=query):
            batch = _search_prs(client, query, limit, seen)
        for candidate in batch:
            key = (candidate.repo, candidate.number)
            if key in seen:
                continue
            seen.add(key)
            prs.append(candidate)
            if len(prs) >= limit:
                break

    log.debug("discovered_prs", count=len(prs), from_urls=len(pr_urls))
    return prs


GRAPHQL_PR_QUERY = """
query($owner:String!,$name:String!,$number:Int!){
  repository(owner:$owner,name:$name){
    pullRequest(number:$number){
      number
      title
      url
      isDraft
      mergeable
      reviewDecision
      createdAt
      updatedAt
      headRefOid
      headRefName
      headRepository{nameWithOwner}
      author{login}
      commits(last:1){nodes{commit{statusCheckRollup{
        state
        contexts(last:100){nodes{
          __typename
          ... on CheckRun{name conclusion status detailsUrl}
          ... on StatusContext{context state targetUrl}
        }}
      }}}}
    }
  }
}
"""


def _format_iso(value: str | None) -> str:
    """Normalize a GraphQL ISO-8601 timestamp (``Z`` suffix) to offset form."""
    if not value:
        return ""
    return value.replace("Z", "+00:00")


def _classify_context(node: dict) -> tuple[str, CheckInfo] | None:
    """Classify one statusCheckRollup context as passing/failing/pending."""
    if node.get("__typename") == "CheckRun":
        name = node.get("name") or ""
        status = (node.get("status") or "").upper()
        conclusion = (node.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            return "pending", CheckInfo(name=name, status=status.lower())
        if conclusion in FAILING_CONCLUSIONS:
            return "failing", CheckInfo(name=name, status=conclusion.lower())
        return "passing", CheckInfo(name=name, status=conclusion.lower() or "success")

    name = node.get("context") or "status"
    state = (node.get("state") or "").upper()
    if state in PENDING_STATES:
        return "pending", CheckInfo(name=name, status=state.lower())
    if state in ("ERROR", "FAILURE"):
        return "failing", CheckInfo(name=name, status=state.lower())
    return "passing", CheckInfo(name=name, status=state.lower() or "success")


def _matches_any(name: str, patterns: list[str]) -> bool:
    """Return True if check *name* matches any pattern.

    Matching is case-insensitive and supports shell-style globs (e.g.
    ``buildkite/*``) as well as exact names.
    """
    lowered = name.lower()
    return any(
        lowered == pattern.lower() or fnmatch(lowered, pattern.lower())
        for pattern in patterns
    )


def fetch_pr_data(
    client: Github,
    pr: PRCIState,
    exclude_checks: list[str] | None = None,
    include_checks: list[str] | None = None,
) -> None:
    """Populate *pr* from one GraphQL query.

    Checks matching *exclude_checks* (exact or glob, case-insensitive) are
    excluded from the CI status entirely, so an excluded failing check does not
    make the PR count as failing. When *include_checks* is given, every check
    that does not match it is excluded instead, so only the named checks count.
    """
    with timed("fetch_pr_data", repo=pr.repo, pr=pr.number):
        owner, name = pr.repo.split("/", 1)
        _headers, data = client.requester.graphql_query(
            GRAPHQL_PR_QUERY,
            {"owner": owner, "name": name, "number": pr.number},
        )
        pull = data["data"]["repository"]["pullRequest"]
        if pull is None:
            pr.error = "not found"
            return

        pr.title = pull["title"] or pr.title
        pr.url = pull["url"] or pr.url
        pr.author = (pull["author"] or {}).get("login", "")
        pr.draft = pull["isDraft"]
        pr.head_commit = pull["headRefOid"] or ""
        pr.head_branch = pull["headRefName"] or ""
        pr.head_repo = (pull["headRepository"] or {}).get("nameWithOwner") or pr.repo
        pr.mergeable = pull["mergeable"] or ""
        pr.review_decision = pull["reviewDecision"] or ""
        pr.created_at = _format_iso(pull["createdAt"])
        pr.updated_at = _format_iso(pull["updatedAt"])

        commits = pull["commits"]["nodes"]
        rollup = None
        if commits:
            rollup = commits[-1]["commit"].get("statusCheckRollup")

        if not rollup:
            pr.checks_state = "none"
            pr.total_checks = 0
            return

        exclude_patterns = exclude_checks or []
        include_patterns = include_checks or []
        latest: dict[str, tuple[str, CheckInfo]] = {}
        for node in rollup.get("contexts", {}).get("nodes", []):
            classified = _classify_context(node)
            if classified is None:
                continue
            kind, info = classified
            latest[info.name] = (kind, info)

        pr.total_checks = len(latest)
        failing: list[CheckInfo] = []
        pending: list[CheckInfo] = []
        excluded: list[CheckInfo] = []
        excluded_count = 0
        for kind, info in latest.values():
            is_excluded = _matches_any(info.name, exclude_patterns) or (
                include_patterns and not _matches_any(info.name, include_patterns)
            )
            if is_excluded:
                excluded_count += 1
                if kind in ("failing", "pending"):
                    excluded.append(info)
            elif kind == "failing":
                failing.append(info)
            elif kind == "pending":
                pending.append(info)
        pr.failing_checks = sorted(failing, key=lambda c: c.name)
        pr.pending_checks = sorted(pending, key=lambda c: c.name)
        pr.excluded_checks = sorted(excluded, key=lambda c: c.name)
        considered = pr.total_checks - excluded_count
        pr.considered_checks = considered

        if failing:
            pr.checks_state = "failing"
        elif pending:
            pr.checks_state = "pending"
        elif considered:
            pr.checks_state = "passing"
        elif excluded_count:
            # Every check was excluded, so there is nothing left to judge.
            pr.checks_state = "none"
        else:
            rollup_state = (rollup.get("state") or "").upper()
            if rollup_state in ("FAILURE", "ERROR"):
                pr.checks_state = "failing"
            elif rollup_state in PENDING_STATES:
                pr.checks_state = "pending"
            elif latest:
                pr.checks_state = "passing"
            else:
                pr.checks_state = "none"

    log.debug("fetched_pr_data", repo=pr.repo, pr=pr.number, ci=pr.checks_state)


def process_pr(
    token: str,
    pr: PRCIState,
    exclude_checks: list[str] | None = None,
    include_checks: list[str] | None = None,
) -> PRCIState:
    """Process a single PR, fetching and classifying its CI status."""
    with timed("process_pr", repo=pr.repo, pr=pr.number):
        client = create_client(token)
        try:
            fetch_pr_data(client, pr, exclude_checks, include_checks)
        except GithubException as ex:
            pr.error = str(ex)
            log.warning("pr_error", repo=pr.repo, pr=pr.number, error=str(ex))
    return pr


def _group_by_repo(prs: list[PRCIState]) -> list[tuple[str, list[PRCIState]]]:
    """Group PRs by repo, preserving order of first appearance."""
    groups: dict[str, list[PRCIState]] = {}
    order: list[str] = []
    for pr in prs:
        if pr.repo not in groups:
            groups[pr.repo] = []
            order.append(pr.repo)
        groups[pr.repo].append(pr)
    return [(repo, groups[repo]) for repo in order]


def _age_cell(created_at: str) -> str:
    """Return a compact age string (e.g. 3h, 2d) for a timestamp."""
    if not created_at:
        return "[dim]—[/dim]"
    seconds = (
        datetime.now(timezone.utc) - datetime.fromisoformat(created_at)
    ).total_seconds()
    style = "bold red" if seconds >= 86400 else "dim"
    if seconds < 3600:
        age = f"{int(seconds // 60)}m"
    elif seconds < 48 * 3600:
        age = f"{int(seconds // 3600)}h"
    else:
        age = f"{int(seconds // 86400)}d"
    return f"[{style}]{age}[/{style}]"


def _ci_cell(pr: PRCIState) -> str:
    """Return a colored CI status cell for *pr*."""
    if pr.error:
        return "[red]error[/red]"
    style, label = STATE_DISPLAY.get(pr.checks_state, ("dim", pr.checks_state))
    text = f"[{style}]{label}[/{style}]"
    if pr.checks_state == "failing" and pr.considered_checks:
        text += f" [red]({len(pr.failing_checks)}/{pr.considered_checks})[/red]"
    if pr.excluded_checks:
        text += f" [dim]({len(pr.excluded_checks)} excluded)[/dim]"
    return text


def _failing_cell(pr: PRCIState) -> str:
    """Return the list of failing check names, linked to their details when known."""
    if pr.error:
        return f"[red]{pr.error}[/red]"
    if not pr.failing_checks:
        if pr.pending_checks:
            return (
                "[yellow]"
                + ", ".join(c.name for c in pr.pending_checks)
                + " (pending)[/yellow]"
            )
        if pr.excluded_checks:
            return (
                "[dim]excluded: "
                + ", ".join(c.name for c in pr.excluded_checks)
                + "[/dim]"
            )
        return "[dim]—[/dim]"
    names = ", ".join(c.name for c in pr.failing_checks)
    return f"[red]{names}[/red]"


def build_summary_table(prs: list[PRCIState]) -> Group:
    """Build Rich tables grouped by repository, summarizing PR CI states."""
    tables: list[Table] = []
    for repo, repo_prs in _group_by_repo(prs):
        table = Table(title=repo, title_style="bold cyan", show_header=True)
        table.add_column("PR", style="blue", justify="right")
        table.add_column("Title")
        table.add_column("Age", justify="right")
        table.add_column("Draft", justify="center")
        table.add_column("Review", justify="center")
        table.add_column("CI", justify="center")
        table.add_column("Failing checks")

        for pr in repo_prs:
            table.add_row(
                _pr_cell(pr),
                pr.title,
                _age_cell(pr.created_at),
                "[dim]draft[/dim]" if pr.draft else "[dim]—[/dim]",
                pr.review_decision.lower() if pr.review_decision else "[dim]—[/dim]",
                _ci_cell(pr),
                _failing_cell(pr),
            )
        tables.append(table)
    return Group(*tables)


def _pr_cell(pr: PRCIState) -> str:
    """Return the PR number cell as a hyperlink to the GitHub pull request."""
    url = pr.url or f"https://github.com/{pr.repo}/pull/{pr.number}"
    return f"[link={url}]#{pr.number}[/link]"


def format_dispatch_commands(prs: list[PRCIState]) -> str:
    """Return ``/handle-pr-ci`` commands for failing PRs, one per line."""
    lines = [
        f"/handle-pr-ci {pr.number} {pr.repo}"
        for pr in prs
        if pr.failing and not pr.error
    ]
    return "\n".join(lines)


def format_json(prs: list[PRCIState]) -> str:
    """Return a JSON representation of all PR CI states."""
    return json.dumps([asdict(pr) for pr in prs], indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List your open pull requests and their combined CI status, and "
            "emit /handle-pr-ci commands for PRs with failing checks."
        ),
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help=(
            "PR URLs (https://github.com/owner/repo/pull/N) and/or repos "
            "(owner/repo). With no arguments, searches all of your open PRs."
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
        help="Output results as JSON instead of a table.",
    )
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help="Output only /handle-pr-ci commands for PRs with failing checks.",
    )
    parser.add_argument(
        "--only-failing",
        action="store_true",
        help="Show only PRs whose checks are failing.",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Include draft PRs (excluded by default).",
    )
    parser.add_argument(
        "--exclude-check",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Name of a check to exclude when computing CI status. Repeatable, "
            "and accepts shell-style globs (e.g. 'buildkite/*'). Matching is "
            "case-insensitive. An excluded failing check does not make the PR "
            "count as failing."
        ),
    )
    parser.add_argument(
        "--include-check",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Name of a check to include, excluding every other check. The "
            "inverse of --exclude-check. Repeatable, accepts shell-style globs, "
            "and case-insensitive. Combining it with --exclude-check narrows "
            "further (a check must match --include-check and not match "
            "--exclude-check)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output for PRs with passing or pending checks.",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS.keys(),
        default="warning",
        help="Logging verbosity (default: warning). Use 'debug' for API timings.",
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
    pr_urls, repos = classify_args(args.targets)
    prs = discover_prs(
        client,
        pr_urls,
        repos,
        args.limit,
        include_drafts=args.draft,
    )

    if not prs:
        print("No open PRs found.")
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
            f"Fetching CI status (0/{len(prs)})",
            total=len(prs),
        )
        futures = {
            executor.submit(
                process_pr, token, pr, args.exclude_check, args.include_check
            ): pr
            for pr in prs
        }
        for future in as_completed(futures):
            future.result()
            progress.advance(task)
            completed = progress.tasks[task].completed
            progress.update(
                task,
                description=f"Fetching CI status ({completed}/{len(prs)})",
            )

    prs.sort(key=lambda pr: (not pr.failing, -(pr.number)))

    if args.only_failing or args.quiet:
        prs = [pr for pr in prs if pr.failing or pr.error]

    log.info(
        "done",
        total=len(prs),
        failing=sum(1 for p in prs if p.failing),
        pending=sum(1 for p in prs if p.checks_state == "pending"),
        passing=sum(1 for p in prs if p.checks_state == "passing"),
        errors=sum(1 for p in prs if p.error),
    )

    if args.json:
        print(format_json(prs))
    elif args.dispatch:
        commands = format_dispatch_commands(prs)
        if commands:
            print(commands)
        else:
            print(f"processed {len(prs)} PRs, no failing checks to dispatch")
    else:
        console.print(build_summary_table(prs))

    return 0


if __name__ == "__main__":
    sys.exit(main())
