#!/usr/bin/env bash
# Pull Tuple call captures (transcripts) from the local Tuple app into
# NOTES_DIR/transcripts as markdown, tracked in transcripts/tuple-manifest.json.
#
# Default tuple binary: override with TUPLE_BIN=/path/to/tuple
# Default notes dir: NOTES_DIR from .env, override with NOTES_DIR=/path/to/notes

set -euo pipefail
# Transcripts carry private conversation and participant names; nothing this
# script writes should be readable by other users.
umask 077

TUPLE_BIN="${TUPLE_BIN:-tuple}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

usage() {
  cat <<'USAGE'
Usage: tuple-pull-transcripts.sh [options]

Options:
  --call <id>        only this call (repeatable, accepts short id prefixes)
  --after <date>     only calls starting on or after this date (YYYY-MM-DD)
  --before <date>    only calls starting on or before this date (YYYY-MM-DD)
  --exclude <cats>   capture categories to leave out: transcript, events, content
                     (repeatable; default is everything the tool exports)
  --force            re-export calls already in the manifest (reuses their filename)
  --dry-run          list what would be pulled without writing anything
  -h, --help         show this help
USAGE
}

command -v "$TUPLE_BIN" >/dev/null || {
  echo "error: tuple not found: $TUPLE_BIN" >&2
  echo "Set TUPLE_BIN to the tuple binary path, or install the Tuple CLI." >&2
  exit 1
}

command -v jq >/dev/null || {
  echo "error: jq is required" >&2
  exit 1
}

CALLS=()
AFTER=""
BEFORE=""
EXCLUDES=()
FORCE=0
DRY_RUN=0

while (($# > 0)); do
  case "$1" in
    --call)
      CALLS+=("${2:?--call needs a call id}")
      shift 2
      ;;
    --after)
      AFTER="${2:?--after needs a date}"
      shift 2
      ;;
    --before)
      BEFORE="${2:?--before needs a date}"
      shift 2
      ;;
    --exclude)
      EXCLUDES+=("${2:?--exclude needs a category}")
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

NOTES_DIR="${NOTES_DIR:-$(./scripts/get-env NOTES_DIR)}"
TRANSCRIPTS_DIR="${NOTES_DIR%/}/transcripts"
MANIFEST="${TRANSCRIPTS_DIR}/tuple-manifest.json"

if [[ -f "$MANIFEST" ]]; then
  manifest_json="$(cat "$MANIFEST")"
else
  manifest_json='{"files":{}}'
fi

list_args=(capture list --limit -1 --format json)
[[ -n "$AFTER" ]] && list_args+=(--after "$AFTER")
[[ -n "$BEFORE" ]] && list_args+=(--before "$BEFORE")

if ! calls_json="$("$TUPLE_BIN" "${list_args[@]}" 2>&1)"; then
  echo "error: could not list Tuple calls:" >&2
  echo "$calls_json" >&2
  echo "Check that the Tuple desktop app is running (try: $TUPLE_BIN state), that --after/--before use YYYY-MM-DD, and that TUPLE_HOST and --env point at the right app." >&2
  exit 1
fi

if ((${#CALLS[@]} > 0)); then
  prefixes="$(IFS=,; echo "${CALLS[*]}")"
  filtered="$(echo "$calls_json" | jq --arg p "$prefixes" '
    ($p | split(",")) as $prefixes
    | map(select(.call_id as $id | any($prefixes[]; . as $pre | $id | startswith($pre))))
  ')"
  if [[ "$(echo "$filtered" | jq 'length')" == "0" ]]; then
    echo "error: no stored call matches --call $prefixes" >&2
    exit 1
  fi
  calls_json="$filtered"
fi

total_found="$(echo "$calls_json" | jq 'length')"

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g'
}

# Tuple timestamps are UTC (RFC3339); filenames follow local wall-clock time so
# a call lands on the day it happened for the reader.
local_time() {
  local iso="$1" fmt="$2" epoch
  epoch="$(printf '%s' "$iso" | jq -Rr 'sub("\\.[0-9]+";"") | fromdateiso8601')"
  if date -r "$epoch" +%Y >/dev/null 2>&1; then
    date -r "$epoch" "$fmt"
  else
    date -d "@$epoch" "$fmt"
  fi
}

declare -a to_pull=()
declare -a skip_reasons=()
skipped_manifest=0
skipped_active=0
skipped_empty=0

while IFS= read -r call; do
  cid="$(echo "$call" | jq -r '.call_id')"
  ended="$(echo "$call" | jq -r '.ended_at // empty')"
  segments="$(echo "$call" | jq -r '.segments // 0')"

  if ((FORCE == 0)) && echo "$manifest_json" | jq -e --arg id "$cid" '.files | has($id)' >/dev/null 2>&1; then
    skipped_manifest=$((skipped_manifest + 1))
    continue
  fi
  if [[ -z "$ended" ]]; then
    skipped_active=$((skipped_active + 1))
    skip_reasons+=("in progress, pulled on a later run: $cid")
    continue
  fi
  if ((segments == 0)); then
    skipped_empty=$((skipped_empty + 1))
    skip_reasons+=("no recorded segments: $cid")
    continue
  fi
  to_pull+=("$call")
done < <(echo "$calls_json" | jq -c '.[]')

declare -A used_names=()
declare -A call_fname=()

for call in "${to_pull[@]}"; do
  cid="$(echo "$call" | jq -r '.call_id')"
  title="$(echo "$call" | jq -r '.title // empty')"
  started="$(echo "$call" | jq -r '.started_at')"

  existing="$(echo "$manifest_json" | jq -r --arg id "$cid" '.files[$id].localFile // empty')"
  if [[ -n "$existing" ]]; then
    call_fname["$cid"]="$existing"
    continue
  fi

  if [[ -n "$title" ]]; then
    label="$title"
  else
    label="$(echo "$call" | jq -r '[(.participants // [])[].full_name] | join(" ")')"
  fi
  slug="$(slugify "$label")"
  [[ -z "$slug" ]] && slug="call-${cid:0:8}"
  # Bound the slug so a long title still fits in a filename.
  slug="${slug:0:80}"
  slug="${slug%-}"

  date_part="$(local_time "$started" "+%Y-%m-%d")"
  time_part="$(local_time "$started" "+%H-%M-%Z" | tr '[:upper:]' '[:lower:]')"
  stem="${date_part}-${slug}-${time_part}-tuple-transcript"
  fname="${stem}.md"
  n=1
  while [[ -e "${TRANSCRIPTS_DIR}/${fname}" || -n "${used_names[$fname]:-}" ]]; do
    n=$((n + 1))
    fname="${stem}-${n}.md"
  done
  used_names["$fname"]=1
  call_fname["$cid"]="$fname"
done

export_args=()
for e in ${EXCLUDES[@]+"${EXCLUDES[@]}"}; do
  export_args+=(--exclude "$e")
done

if ((DRY_RUN == 1)); then
  echo "Dry run, nothing written."
  if ((${#to_pull[@]} > 0)); then
    echo "Would pull ${#to_pull[@]} call(s):"
    for call in "${to_pull[@]}"; do
      cid="$(echo "$call" | jq -r '.call_id')"
      echo "    - ${call_fname[$cid]}  (${cid:0:8})"
    done
  fi
  echo "Already in manifest: $skipped_manifest"
  echo "In progress: $skipped_active"
  echo "Empty: $skipped_empty"
  if ((${#skip_reasons[@]} > 0)); then
    echo "Not pulled:"
    for r in "${skip_reasons[@]}"; do
      echo "    - $r"
    done
  fi
  exit 0
fi

mkdir -p "$TRANSCRIPTS_DIR"

write_manifest() {
  echo "$manifest_json" | jq '.' >"${MANIFEST}.tmp"
  mv "${MANIFEST}.tmp" "$MANIFEST"
}

new_count=0
fail_count=0
declare -a new_files=()

if ((${#to_pull[@]} > 0)); then
  echo "Pulling ${#to_pull[@]} call(s)..."
fi

for call in "${to_pull[@]}"; do
  cid="$(echo "$call" | jq -r '.call_id')"
  fname="${call_fname[$cid]}"
  outpath="${TRANSCRIPTS_DIR}/${fname}"
  title="$(echo "$call" | jq -r '.title // empty')"

  if ! export_output="$("$TUPLE_BIN" capture export "$outpath" --call "$cid" --as markdown ${export_args[@]+"${export_args[@]}"} 2>&1)"; then
    echo "FAILED: $cid" >&2
    echo "  $export_output" >&2
    fail_count=$((fail_count + 1))
    continue
  fi
  if [[ ! -s "$outpath" ]]; then
    echo "FAILED: $cid (empty export)" >&2
    rm -f "$outpath"
    fail_count=$((fail_count + 1))
    continue
  fi

  if [[ -z "$title" ]]; then
    title="$(echo "$call" | jq -r '[(.participants // [])[].full_name] | join(", ")')"
  fi

  manifest_json="$(echo "$manifest_json" | jq --arg id "$cid" \
    --arg name "$title" \
    --arg local "$fname" \
    --arg started "$(echo "$call" | jq -r '.started_at')" \
    --arg ended "$(echo "$call" | jq -r '.ended_at')" \
    --arg downloaded "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")" \
    --argjson segments "$(echo "$call" | jq -r '.segments')" \
    --argjson participants "$(echo "$call" | jq -c '[(.participants // [])[].full_name]')" \
    '.files[$id] = {
      name: $name,
      localFile: $local,
      startedAt: $started,
      endedAt: $ended,
      segments: $segments,
      participants: $participants,
      downloadedAt: $downloaded
    }')"

  # Persist after each call so an interrupted run does not re-export and
  # duplicate what it already wrote.
  write_manifest

  new_files+=("$fname")
  new_count=$((new_count + 1))
done

total_tracked="$(echo "$manifest_json" | jq '.files | length')"

echo ""
echo "Summary:"
echo "  New transcripts pulled: $new_count"
echo "  Failed pulls: $fail_count"
echo "  Skipped (already in manifest): $skipped_manifest"
echo "  Skipped (call in progress): $skipped_active"
echo "  Skipped (no recorded segments): $skipped_empty"
echo "  Total stored calls matched: $total_found"
echo "  Total tuple transcripts tracked: $total_tracked"
if ((${#new_files[@]} > 0)); then
  echo "  New files:"
  for f in "${new_files[@]}"; do
    echo "    - $f"
  done
fi
if ((${#skip_reasons[@]} > 0)); then
  echo "  Not pulled:"
  for r in "${skip_reasons[@]}"; do
    echo "    - $r"
  done
fi
