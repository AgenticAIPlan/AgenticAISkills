#!/usr/bin/env python3
"""Lightweight URL audit helper for org-research.

The script extracts Markdown and bare URLs from input files, checks basic HTTP
status and page title, then writes a Markdown audit table. It intentionally does
not decide whether a page supports a specific fact; the reviewer must still
check page relevance against the atomic evidence table.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BARE_URL_RE = re.compile(r"(?<!\]\()https?://[^\s<>)|]+")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass
class LinkResult:
    label: str
    url: str
    status: str
    title: str
    final_url: str
    note: str
    elapsed_ms: int


def extract_links(text: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    for match in MARKDOWN_LINK_RE.finditer(text):
        label = match.group(1).strip() or match.group(2).strip()
        url = match.group(2).strip()
        if url not in seen:
            seen.add(url)
            links.append((label, url))

    for match in BARE_URL_RE.finditer(text):
        url = match.group(0).rstrip(".,;，。；")
        if url not in seen:
            seen.add(url)
            links.append((url, url))

    return links


def load_links(inputs: Iterable[str], urls: Iterable[str]) -> list[tuple[str, str]]:
    collected: list[tuple[str, str]] = []
    seen: set[str] = set()

    for raw_url in urls:
        url = raw_url.strip()
        if url and url not in seen:
            seen.add(url)
            collected.append((url, url))

    for item in inputs:
        path = Path(item)
        text = path.read_text(encoding="utf-8")
        for label, url in extract_links(text):
            if url not in seen:
                seen.add(url)
                collected.append((label, url))

    return collected


def read_title(data: bytes, content_type: str) -> str:
    if "html" not in content_type.lower():
        return ""
    snippet = data[:200_000].decode("utf-8", errors="replace")
    match = TITLE_RE.search(snippet)
    if not match:
        return ""
    return " ".join(html.unescape(match.group(1)).split())


def audit_url(label: str, url: str, timeout: float, user_agent: str) -> LinkResult:
    headers = {"User-Agent": user_agent}
    request = urllib.request.Request(url, headers=headers, method="GET")
    start = time.monotonic()

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(200_000)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            status = str(response.status)
            content_type = response.headers.get("Content-Type", "")
            title = read_title(data, content_type)
            final_url = response.geturl()
            note = "Redirected" if final_url != url else ""
            return LinkResult(label, url, status, title, final_url, note, elapsed_ms)
    except urllib.error.HTTPError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        title = ""
        try:
            title = read_title(exc.read(80_000), exc.headers.get("Content-Type", ""))
        except Exception:
            title = ""
        return LinkResult(label, url, str(exc.code), title, url, exc.reason or "", elapsed_ms)
    except urllib.error.URLError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        reason = str(exc.reason) if getattr(exc, "reason", None) else str(exc)
        status = "Timeout" if "timed out" in reason.lower() else "Other"
        if "Name or service not known" in reason or "getaddrinfo failed" in reason:
            status = "DNS Failed"
        return LinkResult(label, url, status, "", url, reason, elapsed_ms)
    except TimeoutError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return LinkResult(label, url, "Timeout", "", url, str(exc), elapsed_ms)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(results: list[LinkResult]) -> str:
    lines = [
        "| 来源标题 | URL | 链接状态 | 页面标题 | 最终URL | 页面相关性 | 备注 | 响应耗时ms |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in results:
        link = f"[{escape_cell(item.label)}]({item.url})"
        final_url = f"[最终页面]({item.final_url})" if item.final_url and item.final_url != item.url else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_cell(item.label),
                    link,
                    escape_cell(item.status),
                    escape_cell(item.title),
                    final_url,
                    "待人工复核",
                    escape_cell(item.note),
                    str(item.elapsed_ms),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit URLs for org-research evidence tables.")
    parser.add_argument("--input", action="append", default=[], help="Markdown file to scan. Can be repeated.")
    parser.add_argument("--url", action="append", default=[], help="URL to audit directly. Can be repeated.")
    parser.add_argument("--output", default="", help="Write Markdown audit table to this file.")
    parser.add_argument("--timeout", type=float, default=12.0, help="Per URL timeout in seconds.")
    parser.add_argument("--user-agent", default="org-research-link-audit/1.0")
    parser.add_argument("--fail-on-bad", action="store_true", help="Exit 1 if any URL is not HTTP 200.")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args()
    links = load_links(args.input, args.url)
    if not links:
        print("No URLs found. Provide --input or --url.", file=sys.stderr)
        return 2

    results = [audit_url(label, url, args.timeout, args.user_agent) for label, url in links]
    output = render_markdown(results)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    if args.fail_on_bad and any(item.status != "200" for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
