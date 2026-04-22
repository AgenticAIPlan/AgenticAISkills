#!/usr/bin/env python3
"""Non-destructive SSH connectivity/auth probe."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path


def classify(exit_code: int, stdout: str, stderr: str) -> tuple[str, str, str]:
    text = f"{stdout}\n{stderr}".lower()
    if exit_code == 0:
        return "ok", "SSH probe succeeded.", "Proceed with the requested remote command."
    if any(token in text for token in ("mfa", "multi-factor", "verification code", "sso login", "approval")):
        return "needs_user", "SSH access requires an interactive login or approval step.", "Complete the required interactive access step, then retry."
    if any(token in text for token in ("permission denied", "publickey", "host key verification failed", "sign_and_send_pubkey")):
        return "blocked", "SSH authentication failed with the current key, agent, or known_hosts state.", "Provide the correct key/agent/known_hosts path or use the approved bastion flow, then retry."
    if any(token in text for token in ("operation timed out", "connection timed out", "no route to host", "connection refused", "could not resolve hostname")):
        return "blocked", "The current machine cannot reach the SSH endpoint.", "Verify host, port, bastion, VPN, or allowlist requirements, then retry."
    return "blocked", "SSH probe failed.", "Inspect stderr, fix the access path, and retry the probe."


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-destructive SSH probe")
    parser.add_argument("--host", required=True)
    parser.add_argument("--user")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--identity-file")
    parser.add_argument("--ssh-config")
    parser.add_argument("--jump-host")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--remote-command", default="true")
    args = parser.parse_args()

    target = f"{args.user}@{args.host}" if args.user else args.host
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={args.timeout}",
        "-p",
        str(args.port),
    ]

    if args.ssh_config:
        command.extend(["-F", str(Path(args.ssh_config).expanduser())])
    if args.identity_file:
        command.extend(["-i", str(Path(args.identity_file).expanduser())])
    if args.jump_host:
        command.extend(["-J", args.jump_host])

    command.extend([target, args.remote_command])

    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout + 2)
        status, reason, next_step = classify(completed.returncode, completed.stdout, completed.stderr)
        result = {
            "status": status,
            "reason": reason,
            "next_step": next_step,
            "evidence": {
                "command": shlex.join(command),
                "exit_code": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            },
        }
    except subprocess.TimeoutExpired:
        result = {
            "status": "blocked",
            "reason": "SSH probe timed out.",
            "next_step": "Verify host reachability, bastion/VPN path, and allowlist rules, then retry.",
            "evidence": {"command": shlex.join(command), "timeout_seconds": args.timeout + 2},
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
