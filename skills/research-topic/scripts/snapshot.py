#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "trafilatura>=1.12",
#     "structlog",
# ]
# ///
"""Snapshot a single URL: archive the raw HTML, optionally download images, and
convert to clean markdown via a trafilatura-first cascade.

The script owns every deterministic decision the skill used to encode inline:
the browser user-agent, the raw-HTML archive, the wget image pipeline and its
link rewriting, the converter cascade (trafilatura -> html2markdown -> pandoc),
and the meta.json record of what was used.

Usage:
  snapshot.py URL \\
      --output-dir research/<topic>/snapshots/<source-slug> \\
      [--slug <source-slug>] [--with-images] \\
      [--user-agent UA] [--timeout 60]

Outputs (under --output-dir):
  raw.html      exact bytes served (canonical archive)
  content.md    converted markdown (clean text, image links local when --with-images)
  media/        wget mirror of page requisites (only with --with-images)
  meta.json     url, fetched_at, http_status, converter, images, metadata

Run directly (shebang hands it to `uv run --script`, which installs the PEP 723
dependencies into an ephemeral environment on first use).
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import structlog
import trafilatura

log = structlog.get_logger()

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def slugify_url(url: str) -> str:
    """Deterministic ASCII slug for a URL: domain + path, non-alnum -> '-'."""
    parsed = urlparse(url)
    base = f"{parsed.netloc}{parsed.path}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return (slug or "source")[:60]


def fetch_html(url: str, ua: str, timeout: int) -> tuple[bytes, str, str, str]:
    """Fetch a URL with a browser UA. Returns (body_bytes, text, final_url, status).

    Follows redirects, captures the HTTP status even on error responses, and
    transparently decodes gzip. The byte body is the canonical archive.
    """
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            final_url = resp.geturl()
            status = str(resp.getcode())
            headers = resp.headers
    except urllib.error.HTTPError as e:
        body = e.read()
        final_url = getattr(e, "url", url)
        status = str(e.code)
        headers = e.headers
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error fetching {url}: {e.reason}") from e

    if (headers.get("Content-Encoding") or "").lower() == "gzip":
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    charset = headers.get_content_charset() or "utf-8"
    text = body.decode(charset, errors="replace")
    return body, text, final_url, status


def find_downloaded_html(media_dir: Path) -> Path | None:
    """Locate the wget-rewritten HTML under the media mirror.

    wget with -E -k writes the converted page as <name>.html and keeps the
    pre-conversion original as <name>.orig (from -K). We want the converted one.
    """
    candidates = [p for p in media_dir.rglob("*.html")]
    converted = [p for p in candidates if not p.name.endswith(".orig")]
    if not converted:
        return None
    converted.sort(key=lambda p: p.stat().st_size, reverse=True)
    return converted[0]


def download_with_images(
    url: str, media_dir: Path, ua: str, timeout: int
) -> tuple[Path | None, int]:
    """Mirror the page with wget so images download and img src rewrites to local.

    Returns (path-to-rewritten-html, image-file-count). Falls back to (None, 0)
    if wget is unavailable or fails, leaving the caller to convert raw.html.
    """
    if not shutil.which("wget"):
        log.warning("wget.not_found", msg="skipping image download; wget not installed")
        return None, 0

    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "wget",
        "--directory-prefix", str(media_dir),
        "-E",      # save html with .html extension
        "-H",      # span hosts (images often on a CDN / upload.* host)
        "-k",      # convert links to local after download
        "-K",      # keep backup of pre-conversion original (so we can find converted)
        "-p",      # page requisites: images, css, js
        f"--timeout={timeout}",
        f"--user-agent={ua}",
        "--no-check-certificate",
        "--quiet",
        "--no-verbose",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # wget returns non-zero if any requisite fails to fetch; the page itself is
    # usually still mirrored, so do not abort on a non-zero exit code.
    if proc.returncode not in (0, 8):
        log.warning("wget.failed", returncode=proc.returncode, stderr=proc.stderr.strip()[:500])

    rewritten = find_downloaded_html(media_dir)
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}
    image_count = sum(1 for p in media_dir.rglob("*") if p.suffix.lower() in image_exts)
    log.info("wget.done", rewritten=str(rewritten), images=image_count, rc=proc.returncode)
    return rewritten, image_count


def run_trafilatura(text: str, with_images: bool) -> tuple[str, dict]:
    """Primary converter. Returns (markdown, metadata) or ("", {}) on no output.

    Uses the library API directly (the CLI's --input-file flag is broken in
    trafilatura 2.1.0). `extract` returns the markdown string; a second json
    pass harvests title/author/date.
    """
    try:
        md = trafilatura.extract(
            text,
            output_format="markdown",
            include_links=True,
            include_images=with_images,
            include_tables=True,
        )
    except Exception as e:  # trafilatura can raise on malformed input
        log.warning("trafilatura.error", error=str(e))
        return "", {}

    if not md or not md.strip():
        return "", {}

    meta: dict[str, str] = {}
    try:
        js = trafilatura.extract(text, output_format="json", with_metadata=True)
        if js:
            d = json.loads(js)
            meta = {
                "title": d.get("title") or "",
                "author": d.get("author") or "",
                "date": d.get("date") or "",
                "hostname": d.get("source-hostname") or d.get("hostname") or "",
                "sitename": d.get("source") or "",
            }
    except Exception:
        pass
    return md, meta


def run_html2markdown(source_html: Path, domain: str) -> str:
    """First fallback. Pure converter: keeps nav/footer, but respects local img src."""
    if not shutil.which("html2markdown"):
        return ""
    proc = subprocess.run(
        [
            "html2markdown",
            "--plugin-strikethrough",
            "--plugin-table",
            f"--domain={domain}",
            "--input", str(source_html),
        ],
        capture_output=True,
        text=True,
    )
    return proc.stdout


def run_pandoc(source_html: Path) -> str:
    """Last resort. Pure converter."""
    if not shutil.which("pandoc"):
        return ""
    proc = subprocess.run(
        [
            "pandoc", "-f", "html", "-t", "markdown",
            "--wrap=none", "--strip-comments",
            str(source_html),
        ],
        capture_output=True,
        text=True,
    )
    return proc.stdout


def convert(text: str, source_html: Path, domain: str, with_images: bool) -> tuple[str, str, dict]:
    """Try trafilatura, then html2markdown, then pandoc. Return (md, converter, meta)."""
    md, meta = run_trafilatura(text, with_images)
    if md.strip():
        log.info("converter.selected", converter="trafilatura")
        return md, "trafilatura", meta

    md = run_html2markdown(source_html, domain)
    if md.strip():
        log.info("converter.selected", converter="html2markdown")
        return md, "html2markdown", {}

    md = run_pandoc(source_html)
    if md.strip():
        log.info("converter.selected", converter="pandoc")
        return md, "pandoc", {}

    log.warning("converter.none", msg="all converters produced empty output")
    return "", "failed", {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="URL to snapshot")
    parser.add_argument("--output-dir", required=True, help="directory to write outputs into")
    parser.add_argument("--slug", default=None, help="source slug (default: derived from URL)")
    parser.add_argument("--with-images", action="store_true", help="download images via wget and rewrite img src to local")
    parser.add_argument("--user-agent", default=DEFAULT_UA, help="User-Agent header for all fetches")
    parser.add_argument("--timeout", type=int, default=60, help="per-request timeout in seconds")
    args = parser.parse_args(argv)

    slug = args.slug or slugify_url(args.url)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    domain = urlparse(args.url).netloc

    # 1. Archive the exact served bytes.
    try:
        body, text, final_url, status = fetch_html(args.url, args.user_agent, args.timeout)
    except RuntimeError as e:
        log.error("fetch.failed", url=args.url, error=str(e))
        (out_dir / "raw.html").write_bytes(b"")
        _write_meta(out_dir, url=args.url, final_url=args.url, slug=slug, status="error", converter="failed")
        return 2
    (out_dir / "raw.html").write_bytes(body)
    log.info("fetch.done", url=args.url, status=status, bytes=len(body))

    # 2. Optionally mirror images; the rewritten HTML becomes the conversion source.
    source_html = out_dir / "raw.html"
    source_text = text
    images_downloaded = 0
    if args.with_images:
        rewritten, images_downloaded = download_with_images(
            args.url, out_dir / "media", args.user_agent, args.timeout
        )
        if rewritten is not None:
            source_html = rewritten
            source_text = rewritten.read_text(encoding="utf-8", errors="replace")

    # 3. Convert via the cascade.
    md, converter, meta = convert(source_text, source_html, domain, args.with_images)
    if md:
        (out_dir / "content.md").write_text(md, encoding="utf-8")

    # 4. Record provenance.
    _write_meta(
        out_dir,
        url=args.url,
        final_url=final_url,
        slug=slug,
        status=status,
        converter=converter,
        with_images=args.with_images,
        images_downloaded=images_downloaded,
        source_html=str(source_html.relative_to(out_dir)) if source_html.is_relative_to(out_dir) else str(source_html),
        extra=meta,
    )

    log.info("snapshot.complete", converter=converter, md_bytes=len(md.encode("utf-8")))
    print(f"{args.url}\t{converter}\t{status}\t{len(md)} bytes\t{images_downloaded} images")
    return 0 if converter != "failed" else 1


def _write_meta(
    out_dir: Path,
    *,
    url: str,
    final_url: str,
    slug: str,
    status: str,
    converter: str,
    with_images: bool = False,
    images_downloaded: int = 0,
    source_html: str = "raw.html",
    extra: dict | None = None,
) -> None:
    payload = {
        "url": url,
        "final_url": final_url,
        "source_slug": slug,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "http_status": status,
        "converter": converter,
        "with_images": with_images,
        "images_downloaded": images_downloaded,
        "source_html": source_html,
        **(extra or {}),
    }
    (out_dir / "meta.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
