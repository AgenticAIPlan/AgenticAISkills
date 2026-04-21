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
        description="Convert one or more PDFs into Markdown plus same-stem image directories."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--file-path", help="Absolute or relative PDF path"
    )
    input_group.add_argument(
        "--input-dir", help="Directory containing PDFs to convert"
    )
    input_group.add_argument(
        "--file-list", help="Text file with one PDF path per line"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan --input-dir for PDFs",
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
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue batch processing after a PDF fails",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve input PDFs and print planned outputs without calling OCR",
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


def resolve_input_dir(input_dir: str, recursive: bool) -> list[Path]:
    root = Path(input_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Input directory not found: {root}")
    if not root.is_dir():
        raise ValueError(f"Input path is not a directory: {root}")

    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdf_paths = sorted(
        (path.resolve() for path in root.glob(pattern) if path.is_file()),
        key=lambda path: str(path).lower(),
    )
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {root}")
    return pdf_paths


def resolve_file_list(file_list: str) -> list[Path]:
    list_path = Path(file_list).expanduser().resolve()
    if not list_path.exists():
        raise FileNotFoundError(f"File list not found: {list_path}")
    if not list_path.is_file():
        raise ValueError(f"File list path is not a file: {list_path}")

    pdf_paths: list[Path] = []
    for line_number, raw_line in enumerate(
        list_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        candidate = Path(line).expanduser()
        if not candidate.is_absolute():
            candidate = list_path.parent / candidate
        try:
            pdf_paths.append(resolve_pdf_path(str(candidate)))
        except Exception as exc:
            raise ValueError(f"Invalid PDF path on line {line_number}: {exc}") from exc

    if not pdf_paths:
        raise ValueError(f"No PDF paths found in file list: {list_path}")
    return dedupe_paths(pdf_paths)


def dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return deduped


def collect_pdf_paths(args: argparse.Namespace) -> list[Path]:
    if args.file_path:
        if args.recursive:
            raise ValueError("--recursive can only be used with --input-dir")
        return [resolve_pdf_path(args.file_path)]
    if args.input_dir:
        return dedupe_paths(resolve_input_dir(args.input_dir, args.recursive))
    if args.file_list:
        if args.recursive:
            raise ValueError("--recursive can only be used with --input-dir")
        return resolve_file_list(args.file_list)
    raise ValueError("One input mode is required")


def configured_timeout_limit(max_seconds: int) -> float:
    raw_timeout = os.getenv("PADDLEOCR_DOC_PARSING_TIMEOUT", "").strip()
    timeout = float(max_seconds)
    if raw_timeout:
        try:
            timeout = min(timeout, float(raw_timeout))
        except ValueError:
            timeout = float(max_seconds)
    return timeout


def set_timeout_budget(timeout_seconds: float) -> None:
    timeout = max(1.0, float(timeout_seconds))
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
            prefix=f".{pdf_path.stem}.batch-paper-pdf-to-markdown.", dir=str(pdf_path.parent)
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


def planned_output(pdf_path: Path) -> dict[str, Any]:
    markdown_path = pdf_path.with_suffix(".md")
    image_dir = pdf_path.parent / pdf_path.stem
    return {
        "source_pdf": str(pdf_path),
        "markdown_path": str(markdown_path),
        "image_dir": str(image_dir),
        "markdown_exists": markdown_path.exists(),
        "image_dir_exists": image_dir.exists(),
    }


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


def convert_pdf(
    pdf_path: Path,
    *,
    force: bool,
    deadline: float,
    timeout_limit: float,
) -> dict[str, Any]:
    stage_dir: Path | None = None
    final_markdown_path = pdf_path.with_suffix(".md")
    final_image_dir = pdf_path.parent / pdf_path.stem

    try:
        ensure_outputs_available(final_markdown_path, final_image_dir, force)
        remaining = require_time(deadline, 1.0, f"starting OCR for {pdf_path}")
        set_timeout_budget(min(timeout_limit, remaining))

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
            raise RuntimeError(f"{code}: {message}")

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
            force,
        )

        return {
            "ok": True,
            "source_pdf": str(pdf_path),
            "markdown_path": str(final_markdown_path),
            "image_dir": str(final_image_dir),
            "image_count": image_count,
            "pages": len(pages),
        }
    finally:
        if stage_dir and stage_dir.exists():
            shutil.rmtree(stage_dir, ignore_errors=True)


def run_batch(args: argparse.Namespace, pdf_paths: list[Path]) -> dict[str, Any]:
    deadline = time.monotonic() + args.max_seconds
    timeout_limit = configured_timeout_limit(args.max_seconds)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for pdf_path in pdf_paths:
        try:
            results.append(
                convert_pdf(
                    pdf_path,
                    force=args.force,
                    deadline=deadline,
                    timeout_limit=timeout_limit,
                )
            )
        except Exception as exc:
            error = {
                "ok": False,
                "source_pdf": str(pdf_path),
                "error": str(exc),
            }
            errors.append(error)
            if not args.continue_on_error:
                print(str(exc), file=sys.stderr)
                break

    return {
        "ok": not errors,
        "mode": "single" if len(pdf_paths) == 1 else "batch",
        "dry_run": False,
        "total": len(pdf_paths),
        "succeeded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


def build_dry_run_summary(pdf_paths: list[Path]) -> dict[str, Any]:
    return {
        "ok": True,
        "mode": "single" if len(pdf_paths) == 1 else "batch",
        "dry_run": True,
        "total": len(pdf_paths),
        "succeeded": 0,
        "failed": 0,
        "planned_outputs": [planned_output(path) for path in pdf_paths],
        "results": [],
        "errors": [],
    }


def build_error_summary(message: str, *, dry_run: bool = False) -> dict[str, Any]:
    return {
        "ok": False,
        "mode": "input",
        "dry_run": dry_run,
        "total": 0,
        "succeeded": 0,
        "failed": 1,
        "results": [],
        "errors": [
            {
                "ok": False,
                "source_pdf": "",
                "error": message,
            }
        ],
    }


def main() -> int:
    args = parse_args()

    if args.max_seconds <= 0 or args.max_seconds > DEFAULT_MAX_SECONDS:
        message = f"--max-seconds must be between 1 and {DEFAULT_MAX_SECONDS}"
        print(
            json.dumps(
                build_error_summary(message, dry_run=args.dry_run),
                ensure_ascii=False,
                indent=2,
            )
        )
        print(message, file=sys.stderr)
        return 2

    try:
        pdf_paths = collect_pdf_paths(args)
        summary = build_dry_run_summary(pdf_paths) if args.dry_run else run_batch(args, pdf_paths)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["ok"] else 1
    except Exception as exc:
        summary = build_error_summary(str(exc), dry_run=bool(getattr(args, "dry_run", False)))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
