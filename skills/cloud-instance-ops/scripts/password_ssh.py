#!/usr/bin/env python3
"""Reusable password-based SSH wrapper for cloud-instance-ops."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an SSH command using a password without persisting secrets to the repo")
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--password")
    parser.add_argument("--password-file")
    parser.add_argument("--password-env")
    parser.add_argument("--remote-command", default="true")
    parser.add_argument("--connect-timeout", type=int, default=10)
    parser.add_argument("--strict-host-key-checking", choices=("yes", "no", "accept-new"), default="no")
    parser.add_argument("--known-hosts-file")
    parser.add_argument("--batch-json", action="store_true", help="Emit structured JSON instead of raw remote stdout/stderr passthrough")
    return parser.parse_args()


def resolve_password(args: argparse.Namespace) -> str:
    if args.password is not None:
        return args.password

    if args.password_file:
        return Path(args.password_file).expanduser().read_text(encoding="utf-8").strip()

    if args.password_env:
        value = os.getenv(args.password_env)
        if value:
            return value
        raise SystemExit(f"password env var '{args.password_env}' is not visible to the current process")

    raise SystemExit("one of --password, --password-file, or --password-env is required")


def build_expect_script(password: str, ssh_command: list[str]) -> str:
    quoted_command = " ".join(shlex.quote(part) for part in ssh_command)
    escaped_password = password.replace("\\", "\\\\").replace('"', '\\"')
    return f"""set timeout -1
set pass "{escaped_password}"
spawn {quoted_command}
expect {{
  -re {{[Pp]assword:}} {{ send "$pass\\r"; exp_continue }}
  eof
}}
"""


def classify(exit_code: int, stdout: str, stderr: str) -> tuple[str, str]:
    text = f"{stdout}\n{stderr}".lower()
    if exit_code == 0:
        return "ok", "Password SSH command succeeded."
    if "permission denied" in text:
        return "blocked", "Password SSH authentication failed."
    if any(token in text for token in ("connection refused", "connection timed out", "no route to host", "could not resolve hostname")):
        return "blocked", "The current machine cannot reach the SSH endpoint."
    if "host key verification failed" in text:
        return "blocked", "SSH host key verification failed."
    return "blocked", "Password SSH command failed."


def main() -> int:
    args = parse_args()

    if shutil.which("expect") is None:
        raise SystemExit("expect is required but was not found in PATH")
    if shutil.which("ssh") is None:
        raise SystemExit("ssh is required but was not found in PATH")

    password = resolve_password(args)

    ssh_command = [
        "ssh",
        "-o",
        f"StrictHostKeyChecking={args.strict_host_key_checking}",
        "-o",
        f"ConnectTimeout={args.connect_timeout}",
        "-p",
        str(args.port),
    ]
    if args.known_hosts_file:
        ssh_command.extend(["-o", f"UserKnownHostsFile={Path(args.known_hosts_file).expanduser()}"])
    ssh_command.extend([f"{args.user}@{args.host}", args.remote_command])

    script_text = build_expect_script(password, ssh_command)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".exp") as handle:
        handle.write(script_text)
        script_path = handle.name

    try:
        completed = subprocess.run(
            ["expect", script_path],
            capture_output=True,
            text=True,
        )
    finally:
        Path(script_path).unlink(missing_ok=True)

    if not args.batch_json:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        return completed.returncode

    status, reason = classify(completed.returncode, completed.stdout, completed.stderr)
    result = {
        "status": status,
        "reason": reason,
        "evidence": {
            "command": shlex.join(ssh_command),
            "exit_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
