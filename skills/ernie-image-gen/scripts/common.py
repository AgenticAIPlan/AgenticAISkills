from __future__ import annotations

import base64
import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import yaml


class ConfigError(ValueError):
    """Raised when the skill config is invalid."""


ALLOWED_MODES = {"openai_compatible", "native_generate"}
ALLOWED_RESPONSE_FORMATS = {"b64_json", "url"}
ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(?::-(.*?))?\}")


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        raise ConfigError(f"配置文件不存在: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ConfigError("配置文件顶层必须是对象映射。")

    expanded = _expand_env_placeholders(data)
    validated = validate_config(expanded, config_path=path)
    validated["_config_path"] = str(path)
    return validated


def _expand_env_string(value: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        env_name = match.group(1)
        default = match.group(2)
        return os.getenv(env_name, default if default is not None else "")

    return ENV_PATTERN.sub(replacer, value)


def _expand_env_placeholders(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _expand_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_placeholders(item) for item in value]
    if isinstance(value, str):
        return _expand_env_string(value)
    return value


def _resolve_artifact_dir(value: str, config_path: Optional[Path]) -> str:
    artifact_path = Path(value).expanduser()
    if not artifact_path.is_absolute():
        base_dir = config_path.parent if config_path is not None else Path.cwd()
        artifact_path = (base_dir / artifact_path).resolve()
    return str(artifact_path)


def validate_config(raw_config: dict[str, Any], *, config_path: Optional[Path] = None) -> dict[str, Any]:
    config = deepcopy(raw_config)

    required_top_level = [
        "mode",
        "base_url",
        "model",
        "openai_path",
        "native_path",
        "health_path",
        "model_dir",
        "defaults",
        "output",
    ]
    for field in required_top_level:
        if field not in config:
            raise ConfigError(f"缺少必填字段: {field}")

    mode = str(config["mode"]).strip()
    if mode not in ALLOWED_MODES:
        raise ConfigError(f"mode 不合法: {mode}，可选值: {sorted(ALLOWED_MODES)}")
    config["mode"] = mode

    for field in ["base_url", "model", "openai_path", "native_path", "health_path", "model_dir"]:
        value = str(config[field]).strip()
        if not value:
            raise ConfigError(f"字段不能为空: {field}")
        config[field] = value

    weight_tar_path = str(config.get("weight_tar_path", "") or "").strip()
    config["weight_tar_path"] = weight_tar_path

    auth_token_env = str(config.get("auth_token_env", "") or "").strip()
    config["auth_token_env"] = auth_token_env
    config["request_timeout_sec"] = int(config.get("request_timeout_sec", 180))
    if config["request_timeout_sec"] <= 0:
        raise ConfigError("request_timeout_sec 必须大于 0")

    defaults = config.get("defaults")
    if not isinstance(defaults, dict):
        raise ConfigError("defaults 必须是对象映射。")
    for field in ["width", "height", "num_inference_steps", "guidance_scale", "response_format"]:
        if field not in defaults:
            raise ConfigError(f"defaults 缺少必填字段: {field}")

    defaults["width"] = int(defaults["width"])
    defaults["height"] = int(defaults["height"])
    defaults["num_inference_steps"] = int(defaults["num_inference_steps"])
    defaults["guidance_scale"] = float(defaults["guidance_scale"])
    defaults["response_format"] = str(defaults["response_format"]).strip()

    if defaults["width"] <= 0 or defaults["height"] <= 0:
        raise ConfigError("defaults.width 和 defaults.height 必须大于 0")
    if defaults["num_inference_steps"] <= 0:
        raise ConfigError("defaults.num_inference_steps 必须大于 0")
    if defaults["response_format"] not in ALLOWED_RESPONSE_FORMATS:
        raise ConfigError(
            f"defaults.response_format 不合法: {defaults['response_format']}，可选值: {sorted(ALLOWED_RESPONSE_FORMATS)}"
        )

    output = config.get("output")
    if not isinstance(output, dict):
        raise ConfigError("output 必须是对象映射。")
    for field in ["artifact_dir", "save_metadata"]:
        if field not in output:
            raise ConfigError(f"output 缺少必填字段: {field}")

    output["artifact_dir"] = str(output["artifact_dir"]).strip()
    if not output["artifact_dir"]:
        raise ConfigError("output.artifact_dir 不能为空")
    output["artifact_dir"] = _resolve_artifact_dir(output["artifact_dir"], config_path)
    output["save_metadata"] = bool(output["save_metadata"])
    output["filename_prefix"] = str(output.get("filename_prefix", "ernie-image")).strip() or "ernie-image"

    config["defaults"] = defaults
    config["output"] = output
    return config


def build_effective_prompt(prompt: str, text_verbatim: Optional[list[str]] = None) -> str:
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("prompt 不能为空")
    if not text_verbatim:
        return cleaned_prompt

    cleaned_blocks = [block.strip() for block in text_verbatim if block and block.strip()]
    if not cleaned_blocks:
        return cleaned_prompt

    numbered = "\n".join(f"{idx}. {block}" for idx, block in enumerate(cleaned_blocks, start=1))
    return f"{cleaned_prompt}\n\n图中文字（逐字）：\n{numbered}"


def join_endpoint(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def resolve_auth_token(config: dict[str, Any]) -> Optional[str]:
    env_name = config.get("auth_token_env", "")
    if not env_name:
        return None
    token = os.getenv(env_name)
    if not token:
        raise ConfigError(f"环境变量未设置: {env_name}")
    return token


def build_headers(config: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = resolve_auth_token(config)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _http_json(
    method: str,
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    payload: Optional[dict[str, Any]] = None,
    timeout: int = 180,
) -> tuple[int, dict[str, Any]]:
    body = None
    request_headers = headers or {}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = Request(url, data=body, headers=request_headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
            return getattr(response, "status", 200), data
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} 请求失败: {url}\n{body_text}") from exc
    except URLError as exc:
        raise RuntimeError(f"请求失败: {url}\n{exc}") from exc


def _download_bytes(url: str, timeout: int = 180) -> bytes:
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.read()
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"下载图片失败: HTTP {exc.code} {url}\n{body_text}") from exc
    except URLError as exc:
        raise RuntimeError(f"下载图片失败: {url}\n{exc}") from exc


def check_health(config: dict[str, Any]) -> dict[str, Any]:
    url = join_endpoint(config["base_url"], config["health_path"])
    status_code, payload = _http_json(
        "GET",
        url,
        headers=build_headers(config),
        timeout=config["request_timeout_sec"],
    )
    if status_code != 200:
        raise RuntimeError(f"健康检查失败: HTTP {status_code}")

    status = str(payload.get("status", "")).strip().lower()
    if status in {"loading", "error"}:
        raise RuntimeError(f"服务未就绪: status={status}")
    return payload


def _decode_base64_image(data: str) -> bytes:
    payload = data.split(",", 1)[-1]
    return base64.b64decode(payload)


def _extract_image_from_openai_response(response: dict[str, Any], config: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    data_items = response.get("data") or response.get("images") or []
    if not data_items:
        raise RuntimeError("OpenAI 兼容响应缺少 data/images 字段。")

    first = data_items[0]
    if "b64_json" in first and first["b64_json"]:
        return _decode_base64_image(first["b64_json"]), {"delivery": "b64_json"}

    if "url" in first and first["url"]:
        raw_url = first["url"]
        download_url = raw_url if raw_url.startswith(("http://", "https://")) else join_endpoint(config["base_url"], raw_url)
        return _download_bytes(download_url, timeout=config["request_timeout_sec"]), {
            "delivery": "url",
            "download_url": download_url,
        }

    raise RuntimeError("OpenAI 兼容响应既没有 b64_json，也没有 url。")


def _extract_image_from_native_response(response: dict[str, Any], config: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if response.get("image_base64"):
        return _decode_base64_image(response["image_base64"]), {"delivery": "image_base64"}

    images = response.get("images") or response.get("data") or []
    if images:
        first = images[0]
        if isinstance(first, dict):
            if first.get("b64_json"):
                return _decode_base64_image(first["b64_json"]), {"delivery": "b64_json"}
            if first.get("url"):
                raw_url = first["url"]
                download_url = raw_url if raw_url.startswith(("http://", "https://")) else join_endpoint(config["base_url"], raw_url)
                return _download_bytes(download_url, timeout=config["request_timeout_sec"]), {
                    "delivery": "url",
                    "download_url": download_url,
                }

    if response.get("output_path"):
        output_path = Path(response["output_path"])
        if output_path.exists():
            return output_path.read_bytes(), {"delivery": "output_path", "source_path": str(output_path)}

    raise RuntimeError("原生响应中未找到可保存的图片数据。")


def build_generation_request(
    config: dict[str, Any],
    prompt: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    num_inference_steps: Optional[int] = None,
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    response_format: Optional[str] = None,
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    defaults = config["defaults"]
    effective_width = int(width or defaults["width"])
    effective_height = int(height or defaults["height"])
    effective_steps = int(num_inference_steps or defaults["num_inference_steps"])
    effective_guidance = float(
        defaults["guidance_scale"] if guidance_scale is None else guidance_scale
    )
    effective_response_format = str(response_format or defaults["response_format"])

    if effective_response_format not in ALLOWED_RESPONSE_FORMATS:
        raise ConfigError(f"response_format 不合法: {effective_response_format}")

    summary = {
        "width": effective_width,
        "height": effective_height,
        "num_inference_steps": effective_steps,
        "guidance_scale": effective_guidance,
        "seed": seed,
        "response_format": effective_response_format,
    }

    if config["mode"] == "openai_compatible":
        url = join_endpoint(config["base_url"], config["openai_path"])
        payload = {
            "model": config["model"],
            "prompt": prompt,
            "n": 1,
            "size": f"{effective_width}x{effective_height}",
            "response_format": effective_response_format,
            "guidance_scale": effective_guidance,
            "num_inference_steps": effective_steps,
        }
        if seed is not None:
            payload["seed"] = int(seed)
        return "POST", url, payload, summary

    url = join_endpoint(config["base_url"], config["native_path"])
    payload = {
        "prompt": prompt,
        "width": effective_width,
        "height": effective_height,
        "num_inference_steps": effective_steps,
        "guidance_scale": effective_guidance,
        "return_base64": True,
    }
    if seed is not None:
        payload["seed"] = int(seed)
    return "POST", url, payload, summary


def _sanitize_prefix(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return cleaned or "ernie-image"


def _write_artifacts(
    config: dict[str, Any],
    image_bytes: bytes,
    metadata: dict[str, Any],
) -> tuple[Path, Optional[Path]]:
    output_cfg = config["output"]
    artifact_dir = Path(output_cfg["artifact_dir"]).expanduser()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = _sanitize_prefix(output_cfg.get("filename_prefix", "ernie-image"))
    stem = f"{prefix}-{timestamp}"

    image_path = artifact_dir / f"{stem}.png"
    image_path.write_bytes(image_bytes)

    metadata_path = None
    if output_cfg.get("save_metadata", True):
        metadata_path = artifact_dir / f"{stem}.json"
        with metadata_path.open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)

    return image_path, metadata_path


def generate_image(
    config: dict[str, Any],
    prompt: str,
    *,
    text_verbatim: Optional[list[str]] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    num_inference_steps: Optional[int] = None,
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    response_format: Optional[str] = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    health_payload = None
    if not skip_health_check:
        health_payload = check_health(config)

    effective_prompt = build_effective_prompt(prompt, text_verbatim)
    method, url, payload, summary = build_generation_request(
        config,
        effective_prompt,
        width=width,
        height=height,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        seed=seed,
        response_format=response_format,
    )

    status_code, response = _http_json(
        method,
        url,
        headers=build_headers(config),
        payload=payload,
        timeout=config["request_timeout_sec"],
    )
    if status_code != 200:
        raise RuntimeError(f"生成失败: HTTP {status_code}")

    if config["mode"] == "openai_compatible":
        image_bytes, delivery = _extract_image_from_openai_response(response, config)
    else:
        image_bytes, delivery = _extract_image_from_native_response(response, config)

    response_summary = {
        "delivery": delivery["delivery"],
        "created": response.get("created"),
        "elapsed_sec": response.get("elapsed_sec"),
        "seed": response.get("seed", summary.get("seed")),
    }
    if "download_url" in delivery:
        response_summary["download_url"] = delivery["download_url"]
    if "source_path" in delivery:
        response_summary["source_path"] = delivery["source_path"]

    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": config["mode"],
        "model": config["model"],
        "prompt": prompt,
        "effective_prompt": effective_prompt,
        "text_verbatim": text_verbatim or [],
        "request_payload": payload,
        "response_summary": response_summary,
        "seed": response.get("seed", summary.get("seed")),
        "width": summary["width"],
        "height": summary["height"],
        "num_inference_steps": summary["num_inference_steps"],
        "guidance_scale": summary["guidance_scale"],
        "response_format": summary["response_format"],
        "health_payload": health_payload,
        "config_path": config.get("_config_path"),
        "model_dir": config["model_dir"],
        "weight_tar_path": config.get("weight_tar_path") or None,
    }

    image_path, metadata_path = _write_artifacts(config, image_bytes, metadata)
    metadata["output_file"] = str(image_path.resolve())
    if metadata_path:
        metadata["metadata_file"] = str(metadata_path.resolve())
        with metadata_path.open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)

    return {
        "image_path": str(image_path.resolve()),
        "metadata_path": str(metadata_path.resolve()) if metadata_path else None,
        "metadata": metadata,
    }
