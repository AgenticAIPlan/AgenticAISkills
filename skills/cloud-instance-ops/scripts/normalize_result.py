#!/usr/bin/env python3
"""Normalize command outcomes into the shared status contract."""

from __future__ import annotations

import argparse
import json
import sys


def normalize(exit_code: int, stdout: str, stderr: str) -> tuple[str, str, str]:
    text = f"{stdout}\n{stderr}".lower()

    if exit_code == 0:
        return "ok", "Command completed successfully.", "Proceed to the next requested step."

    if any(token in text for token in ("mfa", "multi-factor", "verification code", "sso login", "device code", "browser login", "approval", "captcha")):
        return "needs_user", "The command requires an interactive login, approval, or verification step.", "Complete the required interactive step, then rerun the command."

    if any(token in text for token in ("accessdenied", "unauthorizedoperation", "permission denied by policy", "forbidden", "not authorized", "ram")):
        return "denied", "The current identity is not authorized for this action.", "Request the minimum required permission or approval, then retry."

    if any(token in text for token in ("publickey", "permission denied", "host key verification failed", "expiredtoken", "token has expired", "session token", "connection timed out", "no route to host", "connection refused", "not in whitelist", "network is unreachable")):
        return "blocked", "The current environment cannot complete the command with the available network or credentials.", "Fix the access path, refresh credentials, or use the approved bastion/VPN flow, then retry."

    if any(token in text for token in ("command not found", "unknown option", "unknown command", "not supported")):
        return "unsupported", "The required local tooling or command shape is not supported in the current environment.", "Install the required tool or adjust the command to a supported form, then retry."

    return "blocked", "Command failed and needs investigation.", "Inspect stderr and the environment, then retry with the smallest reproducible command."


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize command outcomes")
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--stdout", default="")
    parser.add_argument("--stderr", default="")
    parser.add_argument("--command", default="")
    args = parser.parse_args()

    stdout = args.stdout
    stderr = args.stderr

    if not stdout and not stderr and not sys.stdin.isatty():
        stderr = sys.stdin.read()

    status, reason, next_step = normalize(args.exit_code, stdout, stderr)
    result = {
        "status": status,
        "reason": reason,
        "next_step": next_step,
        "evidence": {
            "command": args.command,
            "exit_code": args.exit_code,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
