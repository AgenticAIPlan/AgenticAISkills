#!/usr/bin/env python3
"""Local preflight checks for cloud instance operations."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
from pathlib import Path
from typing import Dict, List, Tuple

MUTATING_ACTIONS = {"restart", "deploy", "cloud-op", "transfer"}
SUPPORTED_CLOUDS = {"generic", "aws", "aliyun"}
SUPPORTED_ACTIONS = {
    "connect",
    "transfer",
    "inspect",
    "logs",
    "restart",
    "deploy",
    "instance-check",
    "cloud-op",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight checks for cloud-instance-ops")
    parser.add_argument("--cloud", required=True, choices=sorted(SUPPORTED_CLOUDS))
    parser.add_argument("--action", required=True, choices=sorted(SUPPORTED_ACTIONS))
    parser.add_argument("--host")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--user")
    parser.add_argument("--identity-file")
    parser.add_argument("--ssh-config")
    parser.add_argument("--jump-host")
    parser.add_argument("--profile")
    parser.add_argument("--region")
    parser.add_argument("--restrictions", default="")
    parser.add_argument("--check-port", action="store_true")
    parser.add_argument("--timeout", type=float, default=3.0)
    return parser.parse_args()


def required_binaries(cloud: str, action: str) -> List[str]:
    binaries = []
    if action in {"connect", "inspect", "logs", "restart", "deploy", "transfer"}:
        binaries.append("ssh")
    if action in {"transfer", "deploy"}:
        binaries.append("scp")
    if cloud == "aws" and action in {"instance-check", "cloud-op"}:
        binaries.append("aws")
    if cloud == "aliyun" and action in {"instance-check", "cloud-op"}:
        binaries.append("aliyun")
    return binaries


def file_status(path_str: str | None) -> Tuple[bool, str | None]:
    if not path_str:
        return True, None
    path = Path(path_str).expanduser()
    return path.exists(), str(path)


def parse_aws_profiles() -> List[str]:
    profiles = set()
    for path_str in ("~/.aws/config", "~/.aws/credentials"):
        path = Path(path_str).expanduser()
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            raw = line.strip()
            if raw.startswith("[") and raw.endswith("]"):
                section = raw[1:-1].strip()
                if section.startswith("profile "):
                    section = section[len("profile ") :].strip()
                if section:
                    profiles.add(section)
    return sorted(profiles)


def parse_aliyun_profiles() -> List[str]:
    candidates = [Path("~/.aliyun/config.json").expanduser(), Path("~/.aliyun/config.yaml").expanduser()]
    names = set()
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        names.update(re.findall(r'"name"\s*:\s*"([^"]+)"', text))
        names.update(re.findall(r"name\s*:\s*([A-Za-z0-9._-]+)", text))
    return sorted(names)


def check_port(host: str, port: int, timeout: float) -> Tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "open"
    except OSError as exc:
        return False, str(exc)


def classify_restrictions(restrictions: List[str], action: str, jump_host: str | None) -> Tuple[str | None, str | None, str | None]:
    restriction_set = {item.lower() for item in restrictions}

    if restriction_set & {"mfa", "sso", "approval", "captcha"}:
        trigger = sorted(restriction_set & {"mfa", "sso", "approval", "captcha"})[0]
        return (
            "needs_user",
            f"The workflow requires an interactive {trigger} step.",
            f"Complete the required {trigger} step, then rerun the operation.",
        )

    if "read-only" in restriction_set and action in MUTATING_ACTIONS:
        return (
            "denied",
            "The current access level is read-only for a mutating action.",
            "Ask for the minimum write permission required for this action, then retry.",
        )

    if restriction_set & {"allowlist", "ip-allowlist", "private-only", "vpn"}:
        if jump_host:
            return None, None, None
        return (
            "blocked",
            "The target appears to require an allowlisted path, VPN, or private-network access.",
            "Connect through the approved bastion/VPN or ask for the current machine to be allowlisted.",
        )

    if "bastion" in restriction_set and not jump_host:
        return (
            "blocked",
            "A bastion or jump host is required but was not provided.",
            "Provide the approved bastion/jump host and rerun preflight.",
        )

    return None, None, None


def main() -> int:
    args = parse_args()
    evidence: Dict[str, object] = {
        "cloud": args.cloud,
        "action": args.action,
        "paths": {},
        "binaries": {},
        "credentials": {},
        "network": {},
        "restrictions": [item for item in args.restrictions.split(",") if item],
    }

    for binary in required_binaries(args.cloud, args.action):
        evidence["binaries"][binary] = shutil.which(binary) is not None

    missing_binaries = [name for name, ok in evidence["binaries"].items() if not ok]
    if missing_binaries:
        result = {
            "status": "unsupported",
            "reason": f"Missing required local binaries: {', '.join(sorted(missing_binaries))}.",
            "next_step": f"Install {', '.join(sorted(missing_binaries))} locally and rerun preflight.",
            "evidence": evidence,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    for label, candidate in (("identity_file", args.identity_file), ("ssh_config", args.ssh_config)):
        ok, normalized = file_status(candidate)
        if normalized:
            evidence["paths"][label] = {"path": normalized, "exists": ok}
            if not ok:
                result = {
                    "status": "blocked",
                    "reason": f"Referenced file does not exist: {normalized}.",
                    "next_step": f"Provide a valid {label.replace('_', ' ')} path and rerun preflight.",
                    "evidence": evidence,
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0

    if args.action in {"connect", "inspect", "logs", "restart", "deploy", "transfer"} and not args.host:
        result = {
            "status": "blocked",
            "reason": "A target host is required for SSH-based operations.",
            "next_step": "Provide the host or IP address and rerun preflight.",
            "evidence": evidence,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    restrictions = [item.strip() for item in args.restrictions.split(",") if item.strip()]
    status, reason, next_step = classify_restrictions(restrictions, args.action, args.jump_host)
    if status:
        result = {"status": status, "reason": reason, "next_step": next_step, "evidence": evidence}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cloud == "aws":
        aws_profiles = parse_aws_profiles()
        aws_env = [name for name in ("AWS_PROFILE", "AWS_ACCESS_KEY_ID", "AWS_SESSION_TOKEN") if os.getenv(name)]
        evidence["credentials"]["aws_profiles"] = aws_profiles
        evidence["credentials"]["aws_env"] = aws_env
        if args.profile and args.profile not in aws_profiles and os.getenv("AWS_PROFILE") != args.profile:
            result = {
                "status": "needs_user",
                "reason": f"AWS profile '{args.profile}' was not found in local config or active environment.",
                "next_step": "Run the approved AWS login/profile setup flow, then retry.",
                "evidence": evidence,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not aws_profiles and not aws_env:
            result = {
                "status": "needs_user",
                "reason": "No obvious AWS credential source was found locally.",
                "next_step": "Activate an AWS profile or export approved AWS credentials, then rerun preflight.",
                "evidence": evidence,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

    if args.cloud == "aliyun":
        aliyun_profiles = parse_aliyun_profiles()
        aliyun_env = [
            name
            for name in (
                "ALIBABA_CLOUD_ACCESS_KEY_ID",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
                "ALICLOUD_PROFILE",
                "ALIYUN_PROFILE",
            )
            if os.getenv(name)
        ]
        evidence["credentials"]["aliyun_profiles"] = aliyun_profiles
        evidence["credentials"]["aliyun_env"] = aliyun_env
        if args.profile and args.profile not in aliyun_profiles and os.getenv("ALICLOUD_PROFILE") != args.profile and os.getenv("ALIYUN_PROFILE") != args.profile:
            result = {
                "status": "needs_user",
                "reason": f"Aliyun profile '{args.profile}' was not found in local config or active environment.",
                "next_step": "Run the approved Aliyun login/profile setup flow, then retry.",
                "evidence": evidence,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not aliyun_profiles and not aliyun_env:
            result = {
                "status": "needs_user",
                "reason": "No obvious Aliyun credential source was found locally.",
                "next_step": "Activate an Aliyun profile or export approved credentials, then rerun preflight.",
                "evidence": evidence,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

    if args.check_port and args.host:
        ok, details = check_port(args.host, args.port, args.timeout)
        evidence["network"][f"{args.host}:{args.port}"] = "open" if ok else details
        if not ok:
            result = {
                "status": "blocked",
                "reason": f"Target port {args.port} on {args.host} is not reachable from the current machine.",
                "next_step": "Use the approved bastion/VPN path or verify that the host and port are reachable from here.",
                "evidence": evidence,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

    if args.jump_host and args.check_port:
        ok, details = check_port(args.jump_host, args.port, args.timeout)
        evidence["network"][f"{args.jump_host}:{args.port}"] = "open" if ok else details
        if not ok:
            result = {
                "status": "blocked",
                "reason": f"Jump host port {args.port} on {args.jump_host} is not reachable from the current machine.",
                "next_step": "Verify the bastion hostname, network path, and allowlist/VPN requirements, then retry.",
                "evidence": evidence,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

    result = {
        "status": "ok",
        "reason": "Local preflight checks passed.",
        "next_step": "Proceed with the smallest read-only or requested command.",
        "evidence": evidence,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
