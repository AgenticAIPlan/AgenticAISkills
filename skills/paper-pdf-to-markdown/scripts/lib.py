# Copyright (c) 2025 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
PaddleOCR document parsing library.

Simple document parsing API wrapper for PaddleOCR.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300
API_GUIDE_URL = "https://paddleocr.com"
FILE_TYPE_PDF = 0
FILE_TYPE_IMAGE = 1
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


def _get_env(key: str, *fallback_keys: str) -> str:
    """Get an environment variable with optional fallback keys."""
    value = os.getenv(key, "").strip()
    if value:
        return value
    for fallback in fallback_keys:
        value = os.getenv(fallback, "").strip()
        if value:
            logger.debug("Using fallback env var: %s", fallback)
            return value
    return ""


def get_config() -> tuple[str, str]:
    """
    Get API URL and token from environment.

    Returns:
        tuple of (api_url, token)

    Raises:
        ValueError: If not configured
    """
    api_url = _get_env("PADDLEOCR_DOC_PARSING_API_URL")
    token = _get_env("PADDLEOCR_ACCESS_TOKEN")

    if not api_url:
        raise ValueError(
            f"PADDLEOCR_DOC_PARSING_API_URL not configured. Get your API at: {API_GUIDE_URL}"
        )
    if not token:
        raise ValueError(
            f"PADDLEOCR_ACCESS_TOKEN not configured. Get your API at: {API_GUIDE_URL}"
        )

    if not api_url.startswith(("http://", "https://")):
        api_url = f"https://{api_url}"
    api_path = urlparse(api_url).path.rstrip("/")
    if not api_path.endswith("/layout-parsing"):
        raise ValueError(
            "PADDLEOCR_DOC_PARSING_API_URL must be a full endpoint ending with "
            "/layout-parsing. "
            "Example: https://your-service.paddleocr.com/layout-parsing"
        )

    return api_url, token


def _detect_file_type(path_or_url: str) -> int:
    """Detect file type: 0=PDF, 1=Image."""
    path = path_or_url.lower()
    if path.startswith(("http://", "https://")):
        path = unquote(urlparse(path).path)

    if path.endswith(".pdf"):
        return FILE_TYPE_PDF
    if path.endswith(IMAGE_EXTENSIONS):
        return FILE_TYPE_IMAGE
    raise ValueError(f"Unsupported file format: {path_or_url}")


def _load_file_as_base64(file_path: str) -> str:
    """Load a local file and encode it as base64."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _make_api_request(api_url: str, token: str, params: dict) -> dict:
    """
    Make a PaddleOCR document parsing API request.

    Args:
        api_url: API endpoint URL
        token: Access token
        params: Request parameters

    Returns:
        API response dict

    Raises:
        RuntimeError: On API errors
    """
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "Client-Platform": "official-skill",
    }

    timeout = float(os.getenv("PADDLEOCR_DOC_PARSING_TIMEOUT", str(DEFAULT_TIMEOUT)))

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(api_url, json=params, headers=headers)
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"API request timed out after {timeout}s") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"API request failed: {exc}") from exc

    if response.status_code != 200:
        error_detail = ""
        try:
            error_body = response.json()
            if isinstance(error_body, dict):
                error_detail = str(error_body.get("errorMsg", "")).strip()
        except Exception:
            pass

        if not error_detail:
            error_detail = (response.text[:200] or "No response body").strip()

        if response.status_code == 403:
            raise RuntimeError(f"Authentication failed (403): {error_detail}")
        if response.status_code == 429:
            raise RuntimeError(f"API rate limit exceeded (429): {error_detail}")
        if response.status_code >= 500:
            raise RuntimeError(
                f"API service error ({response.status_code}): {error_detail}"
            )
        raise RuntimeError(f"API error ({response.status_code}): {error_detail}")

    try:
        result = response.json()
    except Exception as exc:
        raise RuntimeError(f"Invalid JSON response: {response.text[:200]}") from exc

    if result.get("errorCode", 0) != 0:
        raise RuntimeError(f"API error: {result.get('errorMsg', 'Unknown error')}")

    return result


def parse_document(
    file_path: Optional[str] = None,
    file_url: Optional[str] = None,
    file_type: Optional[int] = None,
    **options,
) -> dict[str, Any]:
    """
    Parse a document with PaddleOCR.

    Args:
        file_path: Local file path
        file_url: URL to file
        file_type: Optional file type override (0=PDF, 1=Image)
        **options: Additional API options

    Returns:
        {
            "ok": True,
            "text": "extracted text...",
            "result": { raw API result },
            "error": None,
        }
        or on error:
        {
            "ok": False,
            "text": "",
            "result": None,
            "error": {"code": "...", "message": "..."},
        }
    """
    if not file_path and not file_url:
        return _error("INPUT_ERROR", "file_path or file_url required")
    if file_type is not None and file_type not in (FILE_TYPE_PDF, FILE_TYPE_IMAGE):
        return _error("INPUT_ERROR", "file_type must be 0 (PDF) or 1 (Image)")

    try:
        api_url, token = get_config()
    except ValueError as exc:
        return _error("CONFIG_ERROR", str(exc))

    try:
        resolved_file_type: Optional[int] = None
        if file_url:
            params = {"file": file_url}
            resolved_file_type = file_type
        else:
            resolved_file_type = (
                file_type if file_type is not None else _detect_file_type(file_path)
            )
            params = {"file": _load_file_as_base64(file_path)}

        params.update(options)
        if resolved_file_type is not None:
            params["fileType"] = resolved_file_type
        elif file_url:
            params.pop("fileType", None)
    except (ValueError, FileNotFoundError) as exc:
        return _error("INPUT_ERROR", str(exc))

    try:
        result = _make_api_request(api_url, token, params)
    except RuntimeError as exc:
        return _error("API_ERROR", str(exc))

    try:
        text = _extract_text(result)
    except ValueError as exc:
        return _error("API_ERROR", str(exc))

    return {
        "ok": True,
        "text": text,
        "result": result,
        "error": None,
    }


def _extract_text(result: dict[str, Any]) -> str:
    """Extract text from the document parsing result."""
    if not isinstance(result, dict):
        raise ValueError(
            "Invalid response schema: top-level response must be an object"
        )

    raw_result = result.get("result")
    if not isinstance(raw_result, dict):
        raise ValueError("Invalid response schema: missing result object")

    pages = raw_result.get("layoutParsingResults")
    if not isinstance(pages, list):
        raise ValueError(
            "Invalid response schema: result.layoutParsingResults must be an array"
        )

    texts = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(
                f"Invalid response schema: result.layoutParsingResults[{index}] must be an object"
            )

        markdown = page.get("markdown")
        if not isinstance(markdown, dict):
            raise ValueError(
                f"Invalid response schema: result.layoutParsingResults[{index}].markdown must be an object"
            )

        text = markdown.get("text")
        if not isinstance(text, str):
            raise ValueError(
                f"Invalid response schema: result.layoutParsingResults[{index}].markdown.text must be a string"
            )
        texts.append(text)

    return "\n\n".join(texts)


def _error(code: str, message: str) -> dict[str, Any]:
    """Create a normalized error response."""
    return {
        "ok": False,
        "text": "",
        "result": None,
        "error": {"code": code, "message": message},
    }
