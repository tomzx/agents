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

Discovers PRs needing review, checks staleness of validate-pr / verify-pr /
review-pr comment markers against each PR's HEAD commit, and outputs which
review steps need to be dispatched.

All GitHub access goes through PyGithub (token from GITHUB_TOKEN env var
or ``gh auth token`` as fallback).

Usage:
    scripts/review_requested_prs.py [pr-url ... | owner/repo ...]
        [--limit N] [--json] [--dispatch] [--quiet] [--log-level LEVEL]

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
from itertools import islice
from pathlib import Path

import structlog
from github import Auth, Github
from github.GithubException import GithubException
from rich.console import Console
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


MARKER_PATTERNS: dict[str, re.Pattern[str]] = {
    "validate-pr": re.compile(r"<!-- validate-pr:([a-f0-9]+) -->"),
    "verify-pr": re.compile(r"<!-- verify-pr:([a-f0-9]+) -->"),
    "review-pr": re.compile(r"<!-- review-pr:([a-f0-9]+) -->"),
}

STEP_TO_FIELD: dict[str, str] = {
    "validate-pr": "validate_commit",
    "verify-pr": "verify_commit",
    "review-pr": "review_commit",
}


@dataclass
class PRReviewState:
    repo: str
    number: int
    title: str = ""
    head_commit: str = ""
    validate_commit: str = ""
    verify_commit: str = ""
    review_commit: str = ""
    stale_steps: list[str] = field(default_factory=list)
    skipped: bool = False
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


def classify_args(args: list[str]) -> tuple[list[str], list[str]]:
    """Split positional arguments into PR URLs and repo identifiers."""
    pr_urls: list[str] = []
    repos: list[str] = []
    for arg in args:
        if parse_pr_url(arg):
            pr_urls.append(arg)
        elif is_repo_arg(arg):
            repos.append(arg)
        else:
            print(f"Warning: unrecognized argument '{arg}', skipping", file=sys.stderr)
    return pr_urls, repos


def discover_prs(
    client: Github,
    pr_urls: list[str],
    repos: list[str],
    limit: int,
) -> list[PRReviewState]:
    """Build the list of target PRs from explicit URLs and/or repo search."""
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

    should_search = len(repos) > 0 or len(pr_urls) == 0
    if should_search:
        query = "is:pr is:open review-requested:@me"
        for repo in repos:
            query += f" repo:{repo}"

        with timed("search_issues", query=query, limit=limit):
            results = client.search_issues(query)
            for issue in islice(results, limit):
                repo_full = (
                    issue.repository_url.rsplit("/", 2)[-2]
                    + "/"
                    + issue.repository_url.rsplit("/", 2)[-1]
                )
                key = (repo_full, issue.number)
                if key not in seen:
                    seen.add(key)
                    prs.append(
                        PRReviewState(
                            repo=repo_full,
                            number=issue.number,
                            title=issue.title,
                        ),
                    )

    log.debug(
        "discovered_prs",
        count=len(prs),
        from_urls=len(pr_urls),
        from_search=len(prs) - len(pr_urls),
    )
    return prs


def fetch_head_commit(client: Github, pr: PRReviewState) -> None:
    """Populate *pr.head_commit* via the GitHub API."""
    with timed("fetch_head_commit", repo=pr.repo, pr=pr.number):
        repo = client.get_repo(pr.repo)
        pull = repo.get_pull(pr.number)
        pr.head_commit = pull.head.sha
    log.debug("head_commit", repo=pr.repo, pr=pr.number, sha=pr.head_commit[:8])


SDLC_REVIEW_DIR = Path.home() / ".sdlc"


def check_markers(client: Github, pr: PRReviewState) -> None:
    """Scan PR comments and local .sdlc files for review-skill markers.

    GitHub comments are returned oldest-first by the API, so we overwrite on
    each match, leaving the most recent marker SHA in the field. We also scan
    local report files at ~/.sdlc/<owner>/<repo>/pull-requests/<pr>/ for
    markers when posting to GitHub is disabled or markers are only local.
    """
    with timed("check_markers", repo=pr.repo, pr=pr.number):
        repo = client.get_repo(pr.repo)
        issue = repo.get_issue(pr.number)

        comment_count = 0
        for comment in issue.get_comments():
            comment_count += 1
            for step, pattern in MARKER_PATTERNS.items():
                field_name = STEP_TO_FIELD[step]
                match = pattern.search(comment.body or "")
                if match:
                    setattr(pr, field_name, match.group(1))

        local_dir = SDLC_REVIEW_DIR / pr.repo / "pull-requests" / str(pr.number)
        if local_dir.is_dir():
            for step, pattern in MARKER_PATTERNS.items():
                field_name = STEP_TO_FIELD[step]
                if getattr(pr, field_name):
                    continue
                for md_file in local_dir.glob(f"{step}.*.md"):
                    text = md_file.read_text(errors="replace")
                    match = pattern.search(text)
                    if match:
                        setattr(pr, field_name, match.group(1))
                        break

    log.debug(
        "markers_checked",
        repo=pr.repo,
        pr=pr.number,
        comments=comment_count,
        validate_commit=pr.validate_commit[:8] or "none",
        verify_commit=pr.verify_commit[:8] or "none",
        review_commit=pr.review_commit[:8] or "none",
    )


def determine_stale_steps(pr: PRReviewState) -> list[str]:
    """Return the ordered list of review steps that are stale for *pr*."""
    head = pr.head_commit
    if not head:
        return []

    if (
        pr.validate_commit == head
        and pr.verify_commit == head
        and pr.review_commit == head
    ):
        return []

    if pr.validate_commit != head:
        return ["validate-pr", "verify-pr", "review-pr"]

    if pr.verify_commit != head:
        return ["verify-pr", "review-pr"]

    if pr.review_commit != head:
        return ["review-pr"]

    return []


def build_summary_table(prs: list[PRReviewState]) -> Table:
    """Build a Rich table summarizing PR review states."""
    table = Table(title="Review Requested PRs")
    table.add_column("Repository", style="cyan")
    table.add_column("PR", style="blue", justify="right")
    table.add_column("Steps to run", style="yellow")
    table.add_column("Status")

    for pr in prs:
        if pr.error:
            steps = "—"
            status = f"[red]Error: {pr.error}[/red]"
        elif not pr.stale_steps:
            steps = "—"
            status = "[green]Skipped (all up to date)[/green]"
        else:
            steps = ", ".join(pr.stale_steps)
            status = "[bold yellow]Needs review[/bold yellow]"
        table.add_row(pr.repo, f"#{pr.number}", steps, status)
    return table


def format_dispatch_commands(prs: list[PRReviewState]) -> str:
    """Return dispatch commands (one per line) for PRs needing work."""
    commands: list[str] = []
    for pr in prs:
        for step in pr.stale_steps:
            commands.append(f"/{step} {pr.number} {pr.repo}")
    return "\n".join(commands)


def format_json(prs: list[PRReviewState]) -> str:
    """Return a JSON representation of all PR review states."""
    return json.dumps([asdict(pr) for pr in prs], indent=2)


def process_pr(token: str, pr: PRReviewState) -> PRReviewState:
    """Process a single PR: fetch HEAD commit, check markers, determine stale steps.

    Creates its own GitHub client for thread safety.
    """
    with timed("process_pr", repo=pr.repo, pr=pr.number):
        client = create_client(token)
        try:
            fetch_head_commit(client, pr)
            check_markers(client, pr)
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
            "(validate-pr, verify-pr, review-pr) are stale."
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
        "--quiet",
        action="store_true",
        help="Suppress output for PRs that are fully up to date.",
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
    pr_urls, repos = classify_args(args.targets)
    prs = discover_prs(client, pr_urls, repos, args.limit)

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
        task = progress.add_task("Processing PRs...", total=len(prs))
        futures = {executor.submit(process_pr, token, pr): pr for pr in prs}
        for future in as_completed(futures):
            future.result()
            progress.advance(task)

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
        console.print(build_summary_table(prs))

    return 0


if __name__ == "__main__":
    sys.exit(main())
