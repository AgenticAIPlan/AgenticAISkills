#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from lib import parse_document

DEFAULT_MAX_SECONDS = 300
HTML_IMG_SRC_PATTERN = re.compile(
    r"""(<img\b[^>]*\bsrc\s*=\s*)(["'])([^"']+)(\2)""",
    re.IGNORECASE,
)
MARKDOWN_IMG_PATTERN = re.compile(r"(!\[[^\]]*\]\()([^)]+)(\))")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF into Markdown plus a same-stem image directory."
    )
    parser.add_argument(
        "--file-path", required=True, help="Absolute or relative PDF path"
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=DEFAULT_MAX_SECONDS,
        help=f"Maximum total runtime in seconds (default: {DEFAULT_MAX_SECONDS})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Markdown and image directory",
    )
    return parser.parse_args()


def resolve_pdf_path(file_path: str) -> Path:
    pdf_path = Path(file_path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Only PDF input is supported: {pdf_path}")
    return pdf_path


def set_timeout_budget(max_seconds: int) -> None:
    raw_timeout = os.getenv("PADDLEOCR_DOC_PARSING_TIMEOUT", "").strip()
    timeout = float(max_seconds)
    if raw_timeout:
        try:
            timeout = min(timeout, float(raw_timeout))
        except ValueError:
            timeout = float(max_seconds)
    os.environ["PADDLEOCR_DOC_PARSING_TIMEOUT"] = str(timeout)


def remaining_seconds(deadline: float) -> float:
    return max(0.0, deadline - time.monotonic())


def require_time(deadline: float, minimum_seconds: float, step: str) -> float:
    remaining = remaining_seconds(deadline)
    if remaining < minimum_seconds:
        raise TimeoutError(f"Timed out before {step}. Remaining budget: {remaining:.2f}s")
    return remaining


def extract_pages(result: dict[str, Any]) -> list[dict[str, Any]]:
    raw_result = (result.get("result") or {}).get("result") or {}
    pages = raw_result.get("layoutParsingResults")
    if not isinstance(pages, list):
        raise ValueError("Invalid OCR result: missing result.result.layoutParsingResults")
    return pages


def collect_image_map(pages: list[dict[str, Any]]) -> dict[str, str]:
    image_map: dict[str, str] = {}
    for page in pages:
        markdown = page.get("markdown") or {}
        images = markdown.get("images") or {}
        if not isinstance(images, dict):
            continue
        for relative_path, url in images.items():
            if isinstance(relative_path, str) and isinstance(url, str):
                if relative_path and url:
                    image_map[relative_path] = url
    return image_map


def rewrite_image_paths(markdown_text: str, prefix: str) -> str:
    normalized_prefix = prefix.strip("/").replace("\\", "/")

    def html_replacer(match: re.Match[str]) -> str:
        src = match.group(3)
        if is_external_reference(src):
            return match.group(0)
        rewritten_src = rewrite_relative_reference(src, normalized_prefix)
        return f"{match.group(1)}{match.group(2)}{rewritten_src}{match.group(2)}"

    def markdown_replacer(match: re.Match[str]) -> str:
        src = match.group(2)
        if is_external_reference(src):
            return match.group(0)
        rewritten_src = rewrite_relative_reference(src, normalized_prefix)
        return f"{match.group(1)}{rewritten_src}{match.group(3)}"

    rewritten = HTML_IMG_SRC_PATTERN.sub(html_replacer, markdown_text)
    rewritten = MARKDOWN_IMG_PATTERN.sub(markdown_replacer, rewritten)
    return rewritten


def is_external_reference(src: str) -> bool:
    lowered = src.lower()
    return lowered.startswith(("http://", "https://", "data:", "/"))


def rewrite_relative_reference(src: str, prefix: str) -> str:
    normalized_src = src.replace("\\", "/")
    while normalized_src.startswith("./"):
        normalized_src = normalized_src[2:]
    while normalized_src.startswith("../"):
        normalized_src = normalized_src[3:]
    normalized_src = normalized_src.lstrip("/")
    return f"{prefix}/{normalized_src}"


def safe_target_path(root_dir: Path, relative_path: str) -> Path:
    root_resolved = root_dir.resolve()
    target = (root_dir / relative_path).resolve()
    target.relative_to(root_resolved)
    return target


def download_images(image_map: dict[str, str], image_root: Path, deadline: float) -> int:
    downloaded = 0
    with httpx.Client(follow_redirects=True) as client:
        for relative_path, url in sorted(image_map.items()):
            remaining = require_time(deadline, 1.0, f"downloading {relative_path}")
            target = safe_target_path(image_root, relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            response = client.get(url, timeout=min(remaining, 60.0))
            response.raise_for_status()
            target.write_bytes(response.content)
            downloaded += 1
    return downloaded


def prepare_stage_dir(pdf_path: Path) -> Path:
    return Path(
        tempfile.mkdtemp(
            prefix=f".{pdf_path.stem}.paper-pdf-to-markdown.", dir=str(pdf_path.parent)
        )
    )


def ensure_outputs_available(markdown_path: Path, image_dir: Path, force: bool) -> None:
    if force:
        return
    conflicts = []
    if markdown_path.exists():
        conflicts.append(str(markdown_path))
    if image_dir.exists():
        conflicts.append(str(image_dir))
    if conflicts:
        joined = ", ".join(conflicts)
        raise FileExistsError(f"Output already exists: {joined}. Rerun with --force to overwrite.")


def publish_outputs(
    stage_markdown_path: Path,
    final_markdown_path: Path,
    stage_image_dir: Path,
    final_image_dir: Path,
    force: bool,
) -> None:
    if force:
        if final_markdown_path.exists():
            final_markdown_path.unlink()
        if final_image_dir.exists():
            shutil.rmtree(final_image_dir)
    shutil.move(str(stage_markdown_path), str(final_markdown_path))
    shutil.move(str(stage_image_dir), str(final_image_dir))


def build_markdown(result: dict[str, Any], pdf_stem: str) -> tuple[str, int]:
    pages = extract_pages(result)
    page_markdowns: list[str] = []
    for index, page in enumerate(pages):
        markdown = page.get("markdown")
        if not isinstance(markdown, dict):
            raise ValueError(f"Invalid OCR result: page {index} markdown is missing")
        text = markdown.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Invalid OCR result: page {index} markdown.text is missing")
        page_markdowns.append(text)
    markdown_text = "\n\n".join(page_markdowns)
    if not markdown_text:
        raise ValueError("Invalid OCR result: concatenated page markdown is empty")
    image_map = collect_image_map(pages)
    rewritten = rewrite_image_paths(markdown_text, pdf_stem)
    return rewritten, len(image_map)


def main() -> int:
    args = parse_args()

    if args.max_seconds <= 0:
        print("--max-seconds must be greater than 0", file=sys.stderr)
        return 2

    stage_dir: Path | None = None
    try:
        pdf_path = resolve_pdf_path(args.file_path)
        deadline = time.monotonic() + args.max_seconds
        final_markdown_path = pdf_path.with_suffix(".md")
        final_image_dir = pdf_path.parent / pdf_path.stem
        ensure_outputs_available(final_markdown_path, final_image_dir, args.force)
        set_timeout_budget(args.max_seconds)

        require_time(deadline, 1.0, "starting OCR")
        result = parse_document(
            file_path=str(pdf_path),
            file_type=0,
            useDocUnwarping=False,
            useDocOrientationClassify=False,
            visualize=False,
        )
        if not result.get("ok"):
            error = result.get("error") or {}
            message = error.get("message") or "Unknown OCR error"
            code = error.get("code") or "UNKNOWN_ERROR"
            print(f"{code}: {message}", file=sys.stderr)
            return 1

        pages = extract_pages(result)
        image_map = collect_image_map(pages)
        markdown_text, _ = build_markdown(result, pdf_path.stem)

        stage_dir = prepare_stage_dir(pdf_path)
        stage_markdown_path = stage_dir / f"{pdf_path.stem}.md"
        stage_image_dir = stage_dir / pdf_path.stem
        stage_image_dir.mkdir(parents=True, exist_ok=True)
        stage_markdown_path.write_text(markdown_text, encoding="utf-8")

        image_count = download_images(image_map, stage_image_dir, deadline)
        publish_outputs(
            stage_markdown_path,
            final_markdown_path,
            stage_image_dir,
            final_image_dir,
            args.force,
        )

        summary = {
            "ok": True,
            "source_pdf": str(pdf_path),
            "markdown_path": str(final_markdown_path),
            "image_dir": str(final_image_dir),
            "image_count": image_count,
            "pages": len(pages),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if stage_dir and stage_dir.exists():
            shutil.rmtree(stage_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
