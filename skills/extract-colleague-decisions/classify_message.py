#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Classify a Slack message as decision-bearing (and which bucket) or chatter.

Asks a single Jev Choice question over HTTP against a configurable endpoint. The
categories mirror the extract-colleague-decisions skill:
the four decision buckets the report is built from (Decided, Deferred, Open,
Committed) plus the two reactions recorded on a decision (support, opposition),
and a fallthrough (chatter) so the caller can discard noise instead of guessing.

The judgement is still the agent's; this is an optional accelerator that turns
the "is this worth reading as a decision?" call into one API round-trip.

Usage:
    export JEV_ENDPOINT=... JEV_TOKEN=...
    ./classify_message.py "Let's go with option B"
    echo "sounds good" | ./classify_message.py
    ./classify_message.py --json "I'll send the PR today"
    ./classify_message.py --thread-file thread.txt --author "Alice" "Endorse"
    ./classify_message.py --author "Bob" --decision-author "Alice" "recommend against"

The endpoint and token come from outside: pass --endpoint/--token, or set
JEV_ENDPOINT and JEV_TOKEN. The script never shells out and has no host baked in.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ENV_ENDPOINT = "JEV_ENDPOINT"
ENV_TOKEN = "JEV_TOKEN"
DEFAULT_MODEL = "jev-latest"

# Maps a choice to the report label in step 6 of SKILL.md, so a caller can go
# straight from a classification to the line it writes.
BUCKETS = {
    "decision_made": "Decided",
    "decision_deferred": "Deferred",
    "open_question": "Open",
    "commitment": "Committed",
    "support": "Supported by",
    "opposition": "Opposed by",
    "chatter": None,
}

# The judgment. Each option restates the skill's definition of the bucket, when a
# neighboring bucket is the right answer instead, and a few examples, so the
# model can separate the frequently-confused cases (a counter-proposal is
# opposition, not a new decision; an answered question is not open).
QUESTION = {
    "classification": {
        "type": "choice",
        "instructions": (
            "Classify the message in state['message'] for a daily "
            "colleague-decisions digest. If state contains 'thread', use it as "
            "context, but classify the message itself. state['author'] is who "
            "wrote the message; state['decision_author'], when present, is whose "
            "decision the message reacts to, so a support/opposition choice must "
            "exclude the author's own decision."
        ),
        "criteria": {
            "decision_made": {
                "what": (
                    "States an intent or choice, names a trade-off and picks a "
                    "side, grants an approval or authorization, or records a "
                    "constraint or non-goal. Something is now settled as a result."
                ),
                "not_for": (
                    "Endorsing or rejecting someone else's decision (that is "
                    "support or opposition); pushing a choice to later "
                    "(decision_deferred); or an unanswered question (open_question)."
                ),
                "examples": [
                    "Let's do X",
                    "I'll go with B",
                    "We're dropping Y",
                    "A over B because ...",
                    "You can proceed",
                    "I approve",
                    "Go ahead",
                    "This must not be managed by us",
                ],
            },
            "decision_deferred": {
                "what": (
                    "Explicitly pushes a decision to a follow-up, the next sprint, "
                    "or 'later' without settling it now."
                ),
                "not_for": (
                    "A settled choice (decision_made) or an unresolved question "
                    "(open_question)."
                ),
                "examples": [
                    "Let's revisit this next sprint",
                    "I'll defer to the RFC",
                    "We can decide after the migration lands",
                ],
            },
            "open_question": {
                "what": (
                    "Opens a concrete, unresolved question that affects the work "
                    "and has no substantive answer in the thread yet."
                ),
                "not_for": (
                    "Idle curiosity, logistics questions, or a question already "
                    "answered in the thread."
                ),
                "examples": [
                    "Should we keep the old endpoint during the migration?",
                    "Who owns the rollout of this flag?",
                ],
            },
            "commitment": {
                "what": (
                    "Commits someone to an action: who will do what, even loosely, "
                    "including self-assignments."
                ),
                "not_for": (
                    "A decision about what to do (decision_made) with no owner "
                    "taking it on."
                ),
                "examples": [
                    "I'll take a look",
                    "I'll send the PR today",
                    "Alice will draft the runbook",
                ],
            },
            "support": {
                "what": (
                    "An endorsement, approval, or seconding of another person's "
                    "decision. The report records this as 'Supported by'."
                ),
                "not_for": (
                    "The author's own decision (decision_made); an objection or "
                    "counter-proposal (opposition)."
                ),
                "examples": [
                    "Endorse",
                    "I'm in favor of this",
                    "You can proceed",
                    "Go ahead",
                    "+1 on this one",
                ],
            },
            "opposition": {
                "what": (
                    "A rejection, objection, or pushback against another person's "
                    "decision. The report records this as 'Opposed by'."
                ),
                "not_for": (
                    "A counter-proposal offered in place of the decision is still "
                    "opposition: record the person as an opponent of the decision "
                    "they pushed back on, not as a new decision."
                ),
                "examples": [
                    "I disagree",
                    "I'm not in favor",
                    "Recommend against",
                    "Too broad",
                    "Should not do this",
                    "-1",
                ],
            },
            "chatter": {
                "what": (
                    "Greetings, thanks, reactions-as-words, jokes, pure "
                    "acknowledgements, logistics, or questions that got no "
                    "substantive answer. Nothing decision-bearing."
                ),
                "examples": [
                    "Sounds good",
                    "lol",
                    "Thanks!",
                    "Cancel today's 1:1",
                    "thumbs up",
                ],
            },
        },
    }
}


def resolve_endpoint(cli_value: str | None) -> str:
    """Return the endpoint from --endpoint or $JEV_ENDPOINT."""
    endpoint = cli_value or os.environ.get(ENV_ENDPOINT)
    if not endpoint:
        sys.exit(
            f"no endpoint: pass --endpoint or set ${ENV_ENDPOINT} "
            "(the full endpoint URL)."
        )
    return endpoint


def resolve_token(cli_value: str | None) -> str:
    """Return the token from --token or $JEV_TOKEN."""
    token = cli_value or os.environ.get(ENV_TOKEN)
    if not token:
        sys.exit(f"no token: pass --token or set ${ENV_TOKEN}.")
    return token


def build_state(
    message: str,
    thread: str | None,
    author: str | None,
    decision_author: str | None,
    colleagues: str | None,
) -> dict:
    state: dict = {"message": message}
    if thread:
        state["thread"] = thread
    if author:
        state["author"] = author
    if decision_author:
        state["decision_author"] = decision_author
    if colleagues:
        state["colleagues"] = colleagues
    return state


def classify(state: dict, endpoint: str, model: str, token: str) -> dict:
    payload = {
        "model": model,
        "state": state,
        "questions": QUESTION,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "classify-message/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        sys.exit(f"Jev request failed ({exc.code}): {exc.read().decode()}")
    except urllib.error.URLError as exc:
        sys.exit(f"Jev request failed: {exc.reason}")


def render(result: dict) -> str:
    answer = result["answers"]["classification"]
    choice = answer["choice"]
    bucket = BUCKETS.get(choice)
    lines = [
        f"classification: {choice}",
        f"bucket:         {bucket if bucket is not None else '(chatter, ignore)'}",
        f"confidence:     {answer['confidence']:.2f}",
        "probabilities:",
    ]
    for option, probability in sorted(
        answer["probabilities"].items(), key=lambda item: item[1], reverse=True
    ):
        lines.append(f"  {option:<20} {probability:.2f}")
    usage = result.get("usage", {})
    lines.append(f"model:          {result.get('model', '?')}")
    lines.append(
        f"tokens:         in={usage.get('input_tokens')} out={usage.get('output_tokens')}"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Message text. Reads stdin when omitted and no --file is given.",
    )
    parser.add_argument("--file", help="Read the message from a file instead of argv.")
    parser.add_argument(
        "--thread",
        help="Full thread text for context; the classified message is still the one given.",
    )
    parser.add_argument(
        "--thread-file", help="Read the thread context from a file instead of --thread."
    )
    parser.add_argument(
        "--author", help="Who wrote the message (used to exclude self-support)."
    )
    parser.add_argument(
        "--decision-author",
        help="Whose decision the message reacts to, when judging support/opposition.",
    )
    parser.add_argument(
        "--colleagues",
        help="Comma-separated colleague handles/names, for context.",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Classifier endpoint URL. Defaults to $JEV_ENDPOINT.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Bearer token. Defaults to $JEV_TOKEN.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Jev model name.")
    parser.add_argument(
        "--json", action="store_true", help="Print the raw JSON response."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Exit non-zero when confidence is below this value (default: 0.5).",
    )
    args = parser.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as handle:
            message = handle.read().strip()
    elif args.text:
        message = " ".join(args.text).strip()
    else:
        message = sys.stdin.read().strip()

    if not message:
        parser.error("no message text provided")

    thread = args.thread
    if args.thread_file:
        with open(args.thread_file, encoding="utf-8") as handle:
            thread = handle.read().strip()

    state = build_state(
        message, thread, args.author, args.decision_author, args.colleagues
    )
    endpoint = resolve_endpoint(args.endpoint)
    token = resolve_token(args.token)
    result = classify(state, endpoint, args.model, token)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))

    answer = result["answers"]["classification"]
    if answer["choice"] == "chatter" or answer["confidence"] < args.threshold:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
