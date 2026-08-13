---
name: record-playwright
description: Record a web UI demonstration with Playwright, capturing screenshots at one or more viewports and optionally a video clip, then return the asset paths. Reusable recording primitive used by verify-pr and validate-implementation.
allowed-tools: Bash(npx:*, npm:*, node:*, uv:*, python:*, python3:*, curl:*, ~/.agents/scripts/get-env:*), Read, Write, Glob
argument-hint: "[<slug>] [url]"
---

# Record Web UI Demo (Playwright)

Drive a real browser with Playwright to capture visual proof of a web UI change: screenshots at one or more viewports (desktop, mobile, etc.) and, optionally, a short video clip. Returns the asset paths so they can be embedded inline in a GitHub PR or comment.

This is the recording primitive for web UI changes. For CLI changes, use `/record-asciinema`.

## Prerequisites

- Playwright available one of:
  - `npx playwright` (Node project with `@playwright/test`, or installed globally)
  - `uv run playwright` / `python -m playwright` (Python project with `playwright`)
- Chromium browser installed for Playwright (`npx playwright install chromium`, or `playwright install chromium`). The skill installs it if missing.
- A reachable target URL. Either the caller provides one that is already running, or provides a server command the skill starts and tears down.

## Inputs

| Input | Meaning | Default |
|-------|---------|---------|
| `$RECORD_SLUG` (`$1`) | Filename slug, e.g. `login-page` | `web-demo` |
| `$RECORD_URL` (`$2`) | URL to capture, e.g. `http://localhost:3000/login` | `http://localhost:3000` |
| `$RECORD_DIR` | Output directory | `/tmp/record-playwright` |
| `$RECORD_VIEWPORTS` | Space-separated `WxH` specs | `1280x720 375x812` (desktop + mobile) |
| `$RECORD_VIDEO` | Set to any value to also record a video clip | *(unset; screenshots only)* |
| `$RECORD_SCENARIO` | Prose describing clicks/nav to perform before capture | *(none; capture the URL as-is)* |
| `$RECORD_SERVER_CMD` | Command to start the dev server (skill manages its lifecycle) | *(none; assume URL is already up)* |

## Workflow

```
Inputs resolved (slug, url, viewports, scenario, server cmd?)
          |
          v
Server command provided?
   /            \
 Yes             No
  |               |
  v               v
Start server,   Verify URL is reachable
wait for port     (curl poll)
  |               |
  +-------+-------+
          |
          v
Playwright available? (npx | uv/python)
   /            \
 Yes             No
  |               |
  v               v
Write capture    Stop. Signal caller to
script from      fall back to a text
template +       description of the change
scenario
  |
  v
Run capture script (screenshots + optional video)
  |
  v
Tear down server (if started)
  |
  v
Return asset paths (PNGs per viewport + video)
```

## Steps

### 1. Resolve inputs

```bash
RECORD_SLUG="${1:-web-demo}"
RECORD_URL="${RECORD_URL:-http://localhost:3000}"
RECORD_DIR="${RECORD_DIR:-/tmp/record-playwright}"
RECORD_VIEWPORTS="${RECORD_VIEWPORTS:-1280x720 375x812}"
mkdir -p "$RECORD_DIR"
```

### 2. Start the dev server if a command was given

If `$RECORD_SERVER_CMD` is set, start it in the background and poll the URL until it responds:

```bash
if [ -n "$RECORD_SERVER_CMD" ]; then
  sh -c "$RECORD_SERVER_CMD" &
  SERVER_PID=$!
  for i in $(seq 1 60); do
    curl -sf "$RECORD_URL" >/dev/null 2>&1 && break
    sleep 1
  done
fi
```

If no server command is given, verify the URL is already reachable:

```bash
curl -sf "$RECORD_URL" >/dev/null 2>&1 || { echo "URL not reachable: $RECORD_URL"; exit 0; }
```

If unreachable and no server command was provided, stop and signal the caller. Do not error out.

### 3. Ensure Playwright is available

Detect the project's Playwright runtime:

```bash
if [ -f package.json ] && grep -q '"@playwright/test"' package.json 2>/dev/null; then
  PW="npx playwright"
elif command -v npx >/dev/null 2>&1; then
  PW="npx playwright"
elif command -v uv >/dev/null 2>&1 && [ -f pyproject.toml ]; then
  PW="uv run playwright"
elif command -v python3 >/dev/null 2>&1; then
  PW="python3 -m playwright"
else
  echo "Playwright not available"; exit 0
fi
```

Install Chromium if it is missing:

```bash
$PW install chromium >/dev/null 2>&1 || true
```

### 4. Write the capture script

Write a self-contained Playwright script to `$RECORD_DIR/capture-${RECORD_SLUG}.mjs` (Node) or `.py` (Python). Translate `$RECORD_SCENARIO` into concrete Playwright actions (clicks, navigation, form fills) before capture.

Node template (`capture.mjs`):

```javascript
import { chromium } from 'playwright';

const url = process.env.RECORD_URL;
const dir = process.env.RECORD_DIR;
const slug = process.env.RECORD_SLUG;
const viewports = process.env.RECORD_VIEWPORTS.split(' ');
const wantVideo = !!process.env.RECORD_VIDEO;

const browser = await chromium.launch();

for (const spec of viewports) {
  const [w, h] = spec.split('x').map(Number);
  const context = await browser.newContext({
    viewport: { width: w, height: h },
    recordVideo: wantVideo ? { dir } : undefined,
  });
  const page = await context.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });

  // >>> Translate $RECORD_SCENARIO into actions here, e.g.:
  // await page.click('#submit');
  // await page.waitForTimeout(500);

  await page.screenshot({ path: `${dir}/${slug}-${w}x${h}.png`, fullPage: true });
  await context.close();   // flushes the video if one was being recorded
}

await browser.close();
```

Python template (`capture.py`):

```python
import os
from playwright.sync_api import sync_playwright

url = os.environ["RECORD_URL"]
dir_ = os.environ["RECORD_DIR"]
slug = os.environ["RECORD_SLUG"]
viewports = os.environ["RECORD_VIEWPORTS"].split()
want_video = bool(os.environ.get("RECORD_VIDEO"))

with sync_playwright() as p:
    browser = p.chromium.launch()
    for spec in viewports:
        w, h = (int(x) for x in spec.split("x"))
        context = browser.new_context(
            viewport={"width": w, "height": h},
            record_video_dir=dir_ if want_video else None,
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")

        # >>> Translate $RECORD_SCENARIO into actions here.

        page.screenshot(path=f"{dir_}/{slug}-{w}x{h}.png", full_page=True)
        context.close()
    browser.close()
```

### 5. Run the capture script

```bash
export RECORD_URL RECORD_DIR RECORD_SLUG RECORD_VIEWPORTS RECORD_VIDEO
if [[ "$PW" == npx* ]]; then
  node "$RECORD_DIR/capture-${RECORD_SLUG}.mjs"
else
  $PW install-deps chromium >/dev/null 2>&1 || true
  python3 "$RECORD_DIR/capture-${RECORD_SLUG}.py"
fi
```

### 6. Tear down the server

```bash
if [ -n "$RECORD_SERVER_CMD" ] && [ -n "$SERVER_PID" ]; then
  kill "$SERVER_PID" 2>/dev/null || true
fi
```

### 7. Return the asset paths

Report the captured assets so the caller can upload and embed them:

- Screenshots: `$RECORD_DIR/${RECORD_SLUG}-<W>x<H>.png` (one per viewport)
- Video (if `$RECORD_VIDEO` set): `$RECORD_DIR/*.webm` (Playwright writes a timestamped name under `$RECORD_DIR`)

## Failure Modes

| Mode | Response |
|------|----------|
| **Playwright not available** | Stop cleanly; signal caller to fall back to a text description of the UI change |
| **Chromium not installed and install fails** | Stop cleanly; signal fallback |
| **URL not reachable and no server command** | Stop cleanly; signal caller to start the server first |
| **Server fails to come up within the poll window** | Stop, report the URL, signal fallback |
| **Capture script throws (selector not found, etc.)** | Re-run with a looser scenario or screenshot the error state; report what happened |
| **No screenshots produced** | Report the error; signal fallback to text |

## Example Usage

**Scenario 1: Static screenshots against a running dev server (called by verify-pr)**
```
/record-playwright login-form http://localhost:5173/login
```
Capture desktop (1280x720) and mobile (375x812) PNGs of the login page, return their paths.

**Scenario 2: Scenario-driven capture with a video**
```
RECORD_VIDEO=1 RECORD_SCENARIO="fill #email with test@example.com, click #submit, wait for .dashboard" \
/record-playwright onboarding http://localhost:3000/onboarding
```
Writes a capture script that performs the steps, takes a full-page screenshot per viewport, and records a video clip.

**Scenario 3: Start the server, capture, tear down (called by validate-implementation)**
```
RECORD_SERVER_CMD="npm run dev" RECORD_VIEWPORTS="1280x720" \
/record-playwright new-dashboard http://localhost:3000/dashboard
```
Starts `npm run dev`, waits for the port, captures, kills the server, returns the PNG.
