#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "PyGithub",
#     "rich",
#     "structlog",
# ]
# ///
"""Deterministic orchestrator for the triage-pr-feedback skill.

Discovers open pull requests you authored that have unresolved reviewer
feedback awaiting a response, determines which feedback items have not yet
been analyzed, and computes the path where the analysis agent should write
its recommendation file.

State is file-based and idempotent: a feedback item is considered "analyzed"
once its recommendation file exists under

    $HOME/.sdlc/{owner}/{repo}/pull-requests/{PR}/feedback/{feedback-id}.md

so re-running the script (for example on a 15-minute schedule) only ever
reports genuinely new feedback. Pass ``--reanalyze`` to ignore existing files.

All GitHub access goes through PyGithub (token from GITHUB_TOKEN env var
or ``gh auth token`` as fallback).

Usage:
    scripts/triage_pr_feedback.py [pr-url ... | owner/repo ... | owner ...]
        [--limit N] [--json] [--dispatch] [--quiet] [--reanalyze]
        [--include-resolved] [--include-drafts] [--exclude-author LOGIN ...]
        [--log-level LEVEL] [--workers N]

Examples:
    # All open PRs you authored
    scripts/triage_pr_feedback.py

    # Specific repos only
    scripts/triage_pr_feedback.py acme/api acme/web-app

    # One PR by URL
    scripts/triage_pr_feedback.py https://github.com/acme/api/pull/42

    # Machine-readable JSON (used by the skill)
    scripts/triage_pr_feedback.py --json

    # One dispatch line per PR with new feedback
    scripts/triage_pr_feedback.py --dispatch
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

DEFAULT_EXCLUDED_AUTHORS = [
    "dependabot[bot]",
    "renovate[bot]",
    "github-actions[bot]",
    "codecov[bot]",
]

# Review bots post a "review summary" conversation comment alongside their
# inline comments (e.g. a status card linking to their dashboard). That comment
# is not actionable feedback, so skip it; the inline threads carry the substance.
SUMMARY_MARKER = re.compile(r"<!--\s*[\w-]*review-status\s*-->")


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
    (e.g. rate limited), since orgs are the more common case.
    """
    with timed("resolve_owner", owner=owner):
        try:
            client.get_organization(owner)
            return "org"
        except GithubException:
            return "user"


@dataclass
class FeedbackItem:
    """One piece of reviewer feedback awaiting a response."""

    id: str
    kind: str
    author: str = ""
    created_at: str = ""
    body: str = ""
    url: str = ""
    path: str = ""
    line: int = 0
    thread_id: str = ""
    is_resolved: bool = False
    is_outdated: bool = False
    analysis_path: str = ""
    analyzed: bool = False
    analysis_head: str = ""
    decision: str = ""
    error: str = ""


@dataclass
class PRFeedbackState:
    """All feedback state for a single pull request."""

    repo: str
    number: int
    title: str = ""
    author: str = ""
    url: str = ""
    draft: bool = False
    created_at: str = ""
    head_commit: str = ""
    head_repo: str = ""
    head_branch: str = ""
    base_ref: str = ""
    base_commit: str = ""
    feedback: list[FeedbackItem] = field(default_factory=list)
    skipped: bool = False
    skipped_reason: str = ""
    error: str = ""

    @property
    def new_feedback(self) -> list[FeedbackItem]:
        """Feedback items with no recommendation file yet."""
        return [item for item in self.feedback if not item.analyzed]

    @property
    def pending_decision(self) -> list[FeedbackItem]:
        """Analyzed feedback items the user has not decided on yet."""
        return [item for item in self.feedback if item.analyzed and not item.decision]


def _search_prs(
    client: Github,
    query: str,
    limit: int,
    seen: set[tuple[str, int]],
) -> list[PRFeedbackState]:
    """Run a search query and return PRs not already in *seen*.

    Does not mutate *seen*, so the caller can merge batches in priority order.
    Silently skips queries that fail (e.g. an owner valid as an org but not
    as a user).
    """
    found: list[PRFeedbackState] = []
    with timed("search_issues", query=query, limit=limit):
        try:
            results = client.search_issues(query)
            for issue in islice(results, limit):
                parts = issue.repository_url.rsplit("/", 2)
                repo_full = f"{parts[-2]}/{parts[-1]}"
                if (repo_full, issue.number) in seen:
                    continue
                found.append(
                    PRFeedbackState(
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
) -> list[PRFeedbackState]:
    """Build the list of target PRs from explicit URLs and/or search.

    Default discovery searches open PRs authored by the current user. The
    search runs across all repos unless scoped by *repos* or *owners*.
    """
    prs: list[PRFeedbackState] = []
    seen: set[tuple[str, int]] = set()

    for url in pr_urls:
        parsed = parse_pr_url(url)
        if parsed:
            repo, number = parsed
            key = (repo, number)
            if key not in seen:
                seen.add(key)
                prs.append(PRFeedbackState(repo=repo, number=number))

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

        query = f"is:pr is:open author:@me sort:updated-desc{filters}"
        with timed("search_issues_total", query=query):
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
      headRefOid
      headRefName
      headRepository{nameWithOwner}
      baseRefName
      baseRefOid
      isDraft
      url
      title
      author{login}
      createdAt
      reviewThreads(first:100){
        nodes{
          id
          isResolved
          isOutdated
          path
          line
          comments(first:100){
            nodes{ id databaseId body createdAt url path line author{login} }
          }
        }
      }
      reviews(last:100){
        nodes{ id databaseId state body submittedAt url author{login} }
      }
      comments(last:100){
        nodes{ id databaseId body createdAt url author{login} }
      }
    }
  }
}
"""


def _format_iso(value: str | None) -> str:
    """Normalize a GraphQL ISO-8601 timestamp (``Z`` suffix) to offset form."""
    if not value:
        return ""
    return value.replace("Z", "+00:00")


def _node_id(prefix: str, node: dict) -> str:
    """Build a stable, filename-safe id for a GraphQL node."""
    database_id = node.get("databaseId")
    if database_id:
        return f"{prefix}-{database_id}"
    raw = str(node.get("id") or "")
    return f"{prefix}-{re.sub(r'[^A-Za-z0-9_-]', '', raw)}"


def _login(node: dict | None) -> str:
    """Return the login of the author embedded in a GraphQL node."""
    if not node:
        return ""
    return (node.get("author") or {}).get("login", "")


def _body(node: dict) -> str:
    """Return the body text of a GraphQL node."""
    return (node.get("body") or "").strip()


def _feedback_dir(pr: PRFeedbackState) -> Path:
    """Return the directory holding a PR's feedback analysis files."""
    return (
        Path.home() / ".sdlc" / pr.repo / "pull-requests" / str(pr.number) / "feedback"
    )


FRONTMATTER_FIELD = re.compile(r"^(\w+):\s*(.*)$")


def _read_analysis(path: Path) -> tuple[bool, str, str]:
    """Read (exists, head_commit, decision) from a recommendation file."""
    if not path.is_file():
        return False, "", ""
    head = ""
    decision = ""
    for line in path.read_text(errors="replace").splitlines():
        match = FRONTMATTER_FIELD.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip().strip("\"'")
        if key == "head_commit":
            head = value
        elif key == "decision":
            decision = value
    return True, head, decision


def extract_feedback(
    pr: PRFeedbackState,
    pull: dict,
    exclude_authors: list[str],
    include_resolved: bool,
    reanalyze: bool,
) -> list[FeedbackItem]:
    """Extract unresolved, non-author feedback items from a GraphQL PR payload."""
    me = pr.author
    excluded = set(exclude_authors)
    items: list[FeedbackItem] = []

    for thread in pull["reviewThreads"]["nodes"]:
        if thread.get("isResolved") and not include_resolved:
            continue
        comments = thread["comments"]["nodes"]
        if not comments:
            continue
        if _login(comments[-1]) == me:
            # The author replied last; the ball is in the reviewer's court.
            continue
        candidate = None
        for comment in comments:
            if _login(comment) != me:
                candidate = comment
        if not candidate:
            continue
        author = _login(candidate)
        if author in excluded or not _body(candidate):
            continue
        items.append(
            FeedbackItem(
                id=_node_id("comment", candidate),
                kind="review-comment",
                author=author,
                created_at=_format_iso(candidate.get("createdAt")),
                body=candidate.get("body") or "",
                url=candidate.get("url") or "",
                path=candidate.get("path") or thread.get("path") or "",
                line=candidate.get("line") or thread.get("line") or 0,
                thread_id=thread.get("id") or "",
                is_resolved=bool(thread.get("isResolved")),
                is_outdated=bool(thread.get("isOutdated")),
            ),
        )

    latest_review: dict[str, dict] = {}
    for review in pull["reviews"]["nodes"]:
        author = _login(review)
        if author and author != me:
            latest_review[author] = review
    for review in latest_review.values():
        if review.get("state") not in ("CHANGES_REQUESTED", "COMMENTED"):
            continue
        if _login(review) in excluded or not _body(review):
            continue
        items.append(
            FeedbackItem(
                id=_node_id("review", review),
                kind="review",
                author=_login(review),
                created_at=_format_iso(review.get("submittedAt")),
                body=review.get("body") or "",
                url=review.get("url") or "",
            ),
        )

    comments = pull["comments"]["nodes"]
    last_author_index = -1
    for index, comment in enumerate(comments):
        if _login(comment) == me:
            last_author_index = index
    for index, comment in enumerate(comments):
        if index <= last_author_index:
            continue
        author = _login(comment)
        if author == me or author in excluded or not _body(comment):
            continue
        if SUMMARY_MARKER.search(comment.get("body") or ""):
            continue
        items.append(
            FeedbackItem(
                id=_node_id("conversation", comment),
                kind="issue-comment",
                author=author,
                created_at=_format_iso(comment.get("createdAt")),
                body=comment.get("body") or "",
                url=comment.get("url") or "",
            ),
        )

    feedback_dir = _feedback_dir(pr)
    for item in items:
        analysis_path = feedback_dir / f"{item.id}.md"
        item.analysis_path = str(analysis_path)
        analyzed, head, decision = _read_analysis(analysis_path)
        item.analyzed = analyzed and not reanalyze
        item.analysis_head = head
        item.decision = decision
    return items


def fetch_pr_feedback(
    client: Github,
    pr: PRFeedbackState,
    exclude_authors: list[str],
    include_resolved: bool,
    reanalyze: bool,
) -> None:
    """Populate *pr* with head data and its unresolved feedback items."""
    with timed("fetch_pr_feedback", repo=pr.repo, pr=pr.number):
        owner, name = pr.repo.split("/", 1)
        _headers, data = client.requester.graphql_query(
            GRAPHQL_PR_QUERY,
            {"owner": owner, "name": name, "number": pr.number},
        )
        pull = data["data"]["repository"]["pullRequest"]

        pr.head_commit = pull["headRefOid"]
        pr.head_repo = (pull["headRepository"] or {}).get("nameWithOwner") or pr.repo
        pr.head_branch = pull["headRefName"] or ""
        pr.base_ref = pull["baseRefName"] or ""
        pr.base_commit = pull["baseRefOid"] or ""
        pr.draft = pull["isDraft"]
        pr.url = pull["url"] or f"https://github.com/{pr.repo}/pull/{pr.number}"
        pr.title = pull["title"] or ""
        pr.author = _login(pull) or pr.author
        pr.created_at = _format_iso(pull["createdAt"])

        pr.feedback = extract_feedback(
            pr,
            pull,
            exclude_authors=exclude_authors,
            include_resolved=include_resolved,
            reanalyze=reanalyze,
        )

    log.debug(
        "fetched_pr_feedback",
        repo=pr.repo,
        pr=pr.number,
        sha=pr.head_commit[:8],
        total=len(pr.feedback),
        new=len(pr.new_feedback),
    )


def process_pr(
    token: str,
    pr: PRFeedbackState,
    exclude_authors: list[str],
    include_resolved: bool,
    include_drafts: bool,
    reanalyze: bool,
) -> PRFeedbackState:
    """Process one PR: fetch feedback and mark new items. Thread-safe."""
    with timed("process_pr", repo=pr.repo, pr=pr.number):
        client = create_client(token)
        try:
            fetch_pr_feedback(
                client,
                pr,
                exclude_authors=exclude_authors,
                include_resolved=include_resolved,
                reanalyze=reanalyze,
            )
            if pr.draft and not include_drafts:
                pr.skipped = True
                pr.skipped_reason = "draft"
                return pr
            if not pr.new_feedback:
                pr.skipped = True
                pr.skipped_reason = "no_new_feedback"
        except GithubException as ex:
            pr.error = str(ex)
            log.warning("pr_error", repo=pr.repo, pr=pr.number, error=str(ex))
    return pr


def _age_cell(iso: str) -> str:
    """Return a compact age string (e.g. 3h, 2d) for a timestamp."""
    if not iso:
        return "[dim]—[/dim]"
    seconds = (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds()
    style = "bold red" if seconds >= 86400 else "dim"
    if seconds < 3600:
        age = f"{int(seconds // 60)}m"
    elif seconds < 48 * 3600:
        age = f"{int(seconds // 3600)}h"
    else:
        age = f"{int(seconds // 86400)}d"
    return f"[{style}]{age}[/{style}]"


def _pr_cell(pr: PRFeedbackState) -> str:
    """Return the PR number cell as a hyperlink to the GitHub pull request."""
    url = pr.url or f"https://github.com/{pr.repo}/pull/{pr.number}"
    label = f"#{pr.number}{' [dim](draft)[/dim]' if pr.draft else ''}"
    return f"[link={url}]{label}[/link]"


def build_summary_table(prs: list[PRFeedbackState]) -> Group:
    """Build Rich tables grouped by repository, summarizing feedback state."""
    tables: list[Table] = []
    for repo, repo_prs in _group_by_repo(prs):
        table = Table(title=repo, title_style="bold cyan", show_header=True)
        table.add_column("PR", style="blue", justify="right")
        table.add_column("Title", max_width=40)
        table.add_column("Head", justify="center")
        table.add_column("New", justify="right")
        table.add_column("Pending", justify="right")
        table.add_column("Latest")
        table.add_column("Status")

        for pr in repo_prs:
            if pr.error:
                status = f"[red]Error: {pr.error}[/red]"
            elif pr.new_feedback:
                status = "[bold yellow]New feedback[/bold yellow]"
            elif pr.pending_decision:
                status = "[cyan]Awaiting decision[/cyan]"
            else:
                status = "[green]No feedback[/green]"
            latest = max(
                (item.created_at for item in pr.feedback if item.created_at),
                default="",
            )
            table.add_row(
                _pr_cell(pr),
                pr.title or "[dim]—[/dim]",
                f"[blue]{pr.head_commit[:8]}[/blue]"
                if pr.head_commit
                else "[dim]—[/dim]",
                f"[bold yellow]{len(pr.new_feedback)}[/bold yellow]"
                if pr.new_feedback
                else "[dim]0[/dim]",
                str(len(pr.pending_decision))
                if pr.pending_decision
                else "[dim]0[/dim]",
                _age_cell(latest),
                status,
            )
        tables.append(table)
    return Group(*tables)


def _group_by_repo(
    prs: list[PRFeedbackState],
) -> list[tuple[str, list[PRFeedbackState]]]:
    """Group PRs by repo, preserving order of first appearance."""
    groups: dict[str, list[PRFeedbackState]] = {}
    order: list[str] = []
    for pr in prs:
        if pr.repo not in groups:
            groups[pr.repo] = []
            order.append(pr.repo)
        groups[pr.repo].append(pr)
    return [(repo, groups[repo]) for repo in order]


def format_dispatch(prs: list[PRFeedbackState]) -> str:
    """Return one dispatch line per PR that has new feedback.

    Each line names the repo/PR and the ids of the items needing analysis:
    ``owner/repo#42 <id1>,<id2>``. Lines are separated by newlines.
    """
    lines: list[str] = []
    for pr in prs:
        new = pr.new_feedback
        if not new:
            continue
        ids = ",".join(item.id for item in new)
        lines.append(f"{pr.repo}#{pr.number} {ids}")
    return "\n".join(lines)


def format_json(prs: list[PRFeedbackState]) -> str:
    """Return a JSON representation of all PR feedback state."""
    payload = []
    for pr in prs:
        data = asdict(pr)
        data["new_feedback"] = [asdict(item) for item in pr.new_feedback]
        data["pending_decision"] = [asdict(item) for item in pr.pending_decision]
        payload.append(data)
    return json.dumps(payload, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover your open PRs with unresolved reviewer feedback and "
            "report which feedback items have not yet been analyzed."
        ),
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help=(
            "PR URLs (https://github.com/owner/repo/pull/N) and/or repos "
            "(owner/repo) and/or owners. With no arguments, searches all "
            "open PRs you authored."
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
        help="Output results as JSON instead of a table (used by the skill).",
    )
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help="Output one 'owner/repo#N id1,id2' line per PR with new feedback.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress PRs that have no new feedback.",
    )
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        help="Ignore existing recommendation files and treat all feedback as new.",
    )
    parser.add_argument(
        "--include-resolved",
        action="store_true",
        help="Include resolved review threads (excluded by default).",
    )
    parser.add_argument(
        "--exclude-drafts",
        action="store_true",
        help="Skip draft PRs (included by default).",
    )
    parser.add_argument(
        "--exclude-author",
        nargs="*",
        default=DEFAULT_EXCLUDED_AUTHORS,
        metavar="LOGIN",
        help=(
            "Reviewer logins to ignore. Defaults to common bots: "
            + ", ".join(DEFAULT_EXCLUDED_AUTHORS)
            + "."
        ),
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS.keys(),
        default="warning",
        help="Logging verbosity (default: warning). Use 'debug' for timings.",
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
        include_drafts=not args.exclude_drafts,
    )

    if not prs:
        print("No PRs found.")
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
            executor.submit(
                process_pr,
                token,
                pr,
                args.exclude_author,
                args.include_resolved,
                not args.exclude_drafts,
                args.reanalyze,
            ): pr
            for pr in prs
        }
        for future in as_completed(futures):
            future.result()
            progress.advance(task)
            completed = progress.tasks[task].completed
            progress.update(
                task,
                description=f"Processing PRs ({completed}/{len(prs)})",
            )

    prs.sort(key=lambda pr: pr.number, reverse=True)

    if args.quiet:
        prs = [pr for pr in prs if pr.new_feedback or pr.error]

    log.info(
        "done",
        total=len(prs),
        with_new_feedback=sum(1 for p in prs if p.new_feedback),
        new_items=sum(len(p.new_feedback) for p in prs),
        errors=sum(1 for p in prs if p.error),
    )

    if args.json:
        print(format_json(prs))
    elif args.dispatch:
        dispatch = format_dispatch(prs)
        if dispatch:
            print(dispatch)
        else:
            print(f"processed {len(prs)} PRs, no new feedback")
    else:
        console.print(build_summary_table(prs))

    return 0


if __name__ == "__main__":
    sys.exit(main())
