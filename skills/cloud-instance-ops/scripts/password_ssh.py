#!/usr/bin/env python3
"""Reusable password-based SSH wrapper for cloud-instance-ops."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


class PromptError(RuntimeError):
    """Raised when secure prompting fails."""


CODEX_THREAD_ENV = "CODEX_THREAD_ID"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an SSH command using a securely prompted password without persisting secrets to the repo")
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--password-file")
    parser.add_argument("--password-env")
    parser.add_argument("--prompt-password", action="store_true")
    parser.add_argument("--prompt-mode", choices=("auto", "gui", "tty"), default="auto")
    parser.add_argument("--prompt-title", default="Cloud Instance Password")
    parser.add_argument("--prompt-text", default="请输入 SSH 密码")
    parser.add_argument("--reuse-session", action="store_true")
    parser.add_argument("--no-reuse-session", action="store_true")
    parser.add_argument("--ensure-session", action="store_true")
    parser.add_argument("--session-root")
    parser.add_argument("--session-name")
    parser.add_argument("--session-namespace")
    parser.add_argument("--close-session", action="store_true")
    parser.add_argument("--check-session", action="store_true")
    parser.add_argument("--session-status-json", action="store_true")
    parser.add_argument("--remote-command", default="true")
    parser.add_argument("--connect-timeout", type=int, default=10)
    parser.add_argument("--strict-host-key-checking", choices=("yes", "no", "accept-new"), default="accept-new")
    parser.add_argument("--known-hosts-file")
    parser.add_argument("--batch-json", action="store_true", help="Emit structured JSON instead of raw remote stdout/stderr passthrough")
    return parser.parse_args()


def resolve_password(args: argparse.Namespace) -> str:
    if args.password_file:
        return Path(args.password_file).expanduser().read_text(encoding="utf-8").strip()

    if args.password_env:
        value = os.getenv(args.password_env)
        if value:
            return value
        raise SystemExit(f"password env var '{args.password_env}' is not visible to the current process")

    if args.prompt_password:
        return prompt_for_password(args.prompt_mode, args.prompt_title, args.prompt_text)

    raise SystemExit("one of --prompt-password, --password-file, or --password-env is required")


def prompt_for_password(mode: str, title: str, text: str) -> str:
    if mode == "gui":
        return prompt_password_gui(title, text)
    if mode == "tty":
        return prompt_password_tty(title, text)

    gui_error: PromptError | None = None
    try:
        return prompt_password_gui(title, text)
    except PromptError as exc:
        gui_error = exc

    try:
        return prompt_password_tty(title, text)
    except PromptError as tty_error:
        raise PromptError(f"{gui_error}; fallback tty prompt failed: {tty_error}") from tty_error


def prompt_password_gui(title: str, text: str) -> str:
    osascript = shutil.which("osascript")
    if not osascript:
        raise PromptError("GUI prompt is unavailable because osascript was not found")

    command = [
        osascript,
        "-e",
        f'display dialog "{escape_applescript(text)}" default answer "" with hidden answer buttons {{"Cancel", "OK"}} default button "OK" with title "{escape_applescript(title)}"',
        "-e",
        "text returned of result",
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise PromptError(f"GUI prompt failed or was cancelled: {stderr or 'unknown error'}")
    value = completed.stdout.strip()
    if not value:
        raise PromptError("GUI prompt returned an empty password")
    return value


def prompt_password_tty(title: str, text: str) -> str:
    if not sys.stdin.isatty():
        raise PromptError("TTY prompt is unavailable because stdin is not interactive")

    prompt = f"[{title}] {text}: "
    try:
        value = getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt) as exc:
        raise PromptError("TTY prompt failed or was cancelled") from exc
    if not value:
        raise PromptError("TTY prompt returned an empty password")
    return value


def escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def tcl_list_literal(parts: list[str]) -> str:
    return " ".join("{" + part.replace("\\", "\\\\").replace("}", "\\}") + "}" for part in parts)


def build_expect_script(password: str, ssh_command: list[str]) -> str:
    escaped_password = password.replace("\\", "\\\\").replace('"', '\\"')
    cmd_literal = tcl_list_literal(ssh_command)
    return f'''set timeout -1
set pass "{escaped_password}"
set cmd [list {cmd_literal}]
eval spawn $cmd
expect {{
  -re {{[Pp]assword:}} {{ send "$pass\\r"; exp_continue }}
  eof
}}
'''


def redact_secret(text: str, secret: str | None) -> str:
    if not text or not secret:
        return text
    return text.replace(secret, "[REDACTED]")


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


def classify_command_failure(exit_code: int, stdout: str, stderr: str) -> tuple[str, str]:
    text = f"{stdout}\n{stderr}".lower()
    if exit_code == 0:
        return "ok", "SSH command succeeded via existing session."
    if any(token in text for token in ("master session", "control socket", "mux_client_request_session")):
        return "blocked", "Existing SSH master session could not be reused."
    return "blocked", "Remote command failed after session bootstrap."


def default_session_root() -> Path:
    return Path("/tmp/cloud-instance-ops-sessions")


def resolve_session_namespace(args: argparse.Namespace) -> tuple[str, str]:
    if args.session_namespace:
        return args.session_namespace, "explicit"
    thread_id = os.getenv(CODEX_THREAD_ENV)
    if thread_id:
        return thread_id, CODEX_THREAD_ENV
    return "local-shell", "fallback"


def session_key(args: argparse.Namespace, namespace: str) -> str:
    target_key = args.session_name or f"{args.user}@{args.host}:{args.port}"
    return f"{namespace}::{target_key}"


def session_paths(args: argparse.Namespace) -> tuple[Path, Path, str, str, str]:
    root = Path(args.session_root).expanduser() if args.session_root else default_session_root()
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    namespace, namespace_source = resolve_session_namespace(args)
    key = session_key(args, namespace)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return root / f"{digest}.sock", root / f"{digest}.json", key, namespace, namespace_source


def target(args: argparse.Namespace) -> str:
    return f"{args.user}@{args.host}"


def base_ssh_command(args: argparse.Namespace, socket_path: Path | None = None) -> list[str]:
    command = [
        "ssh",
        "-o",
        f"StrictHostKeyChecking={args.strict_host_key_checking}",
        "-o",
        f"ConnectTimeout={args.connect_timeout}",
        "-p",
        str(args.port),
    ]
    if socket_path is not None:
        command.extend(
            [
                "-o",
                "ControlMaster=auto",
                "-o",
                "ControlPersist=yes",
                "-o",
                f"ControlPath={socket_path}",
            ]
        )
    if args.known_hosts_file:
        command.extend(["-o", f"UserKnownHostsFile={Path(args.known_hosts_file).expanduser()}"])
    return command


def check_master_session(args: argparse.Namespace, socket_path: Path) -> tuple[bool, str, str, str]:
    if not socket_path.exists():
        return False, "missing", "", ""
    command = base_ssh_command(args, socket_path) + ["-O", "check", target(args)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode == 0:
        return True, "active", completed.stdout, completed.stderr
    return False, "stale", completed.stdout, completed.stderr


def write_session_metadata(meta_path: Path, args: argparse.Namespace, socket_path: Path, key: str, namespace: str, namespace_source: str) -> None:
    old_created = None
    if meta_path.exists():
        try:
            old_created = json.loads(meta_path.read_text(encoding="utf-8")).get("created_at")
        except Exception:
            old_created = None
    now = time.time()
    payload = {
        "session_name": key,
        "thread_scope": "current_thread",
        "thread_id": namespace,
        "thread_id_source": namespace_source,
        "user": args.user,
        "host": args.host,
        "port": args.port,
        "socket_path": str(socket_path),
        "created_at": old_created or now,
        "last_used_at": now,
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(meta_path, 0o600)


def touch_session_metadata(meta_path: Path, args: argparse.Namespace, socket_path: Path, key: str, namespace: str, namespace_source: str) -> None:
    write_session_metadata(meta_path, args, socket_path, key, namespace, namespace_source)


def cleanup_session_files(socket_path: Path, meta_path: Path) -> None:
    socket_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)


def emit_session_status(status: str, reason: str, key: str, socket_path: Path, meta_path: Path, namespace: str, namespace_source: str) -> int:
    payload = {
        "status": status,
        "reason": reason,
        "session": {
            "session_name": key,
            "thread_scope": "current_thread",
            "thread_id": namespace,
            "thread_id_source": namespace_source,
            "socket_path": str(socket_path),
            "metadata_path": str(meta_path),
            "socket_exists": socket_path.exists(),
            "metadata_exists": meta_path.exists(),
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def run_expect_ssh(password: str, ssh_command: list[str]) -> subprocess.CompletedProcess[str]:
    script_text = build_expect_script(password, ssh_command)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".exp") as handle:
        handle.write(script_text)
        script_path = handle.name
    os.chmod(script_path, 0o600)
    try:
        return subprocess.run(["expect", script_path], capture_output=True, text=True)
    finally:
        Path(script_path).unlink(missing_ok=True)


def run_and_redact(password: str | None, command: list[str], use_expect: bool) -> tuple[subprocess.CompletedProcess[str], str, str]:
    completed = run_expect_ssh(password or "", command) if use_expect else subprocess.run(command, capture_output=True, text=True)
    safe_stdout = redact_secret(completed.stdout, password)
    safe_stderr = redact_secret(completed.stderr, password)
    return completed, safe_stdout, safe_stderr


def emit_blocked_json(reason: str) -> int:
    print(
        json.dumps(
            {
                "status": "blocked",
                "reason": reason,
                "evidence": {
                    "command": None,
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def bootstrap_session(args: argparse.Namespace, socket_path: Path, meta_path: Path, key: str, namespace: str, namespace_source: str, password: str) -> tuple[bool, dict[str, object]]:
    bootstrap_command = base_ssh_command(args, socket_path) + [target(args), "true"]
    completed, safe_stdout, safe_stderr = run_and_redact(password, bootstrap_command, use_expect=True)
    if completed.returncode != 0:
        status, reason = classify(completed.returncode, safe_stdout, safe_stderr)
        cleanup_session_files(socket_path, meta_path)
        return False, {
            "status": status,
            "reason": reason,
            "phase": "bootstrap",
            "evidence": {
                "command": shlex.join(bootstrap_command),
                "exit_code": completed.returncode,
                "stdout": safe_stdout.strip(),
                "stderr": safe_stderr.strip(),
            },
        }

    active, state, check_stdout, check_stderr = check_master_session(args, socket_path)
    if not active:
        cleanup_session_files(socket_path, meta_path)
        return False, {
            "status": "blocked",
            "reason": f"SSH master session bootstrap did not become active ({state}).",
            "phase": "bootstrap",
            "evidence": {
                "command": shlex.join(bootstrap_command),
                "exit_code": completed.returncode,
                "stdout": redact_secret(check_stdout, password).strip(),
                "stderr": redact_secret(check_stderr, password).strip(),
            },
        }

    write_session_metadata(meta_path, args, socket_path, key, namespace, namespace_source)
    return True, {
        "status": "ok",
        "reason": "SSH master session bootstrapped successfully.",
        "phase": "bootstrap",
        "evidence": {
            "command": shlex.join(bootstrap_command),
            "exit_code": 0,
            "stdout": safe_stdout.strip(),
            "stderr": safe_stderr.strip(),
        },
    }


def main() -> int:
    args = parse_args()

    if shutil.which("expect") is None:
        raise SystemExit("expect is required but was not found in PATH")
    if shutil.which("ssh") is None:
        raise SystemExit("ssh is required but was not found in PATH")

    auto_reuse = not args.no_reuse_session
    socket_path, meta_path, key, namespace, namespace_source = session_paths(args)

    if args.check_session:
        active, state, _, _ = check_master_session(args, socket_path)
        if args.session_status_json or args.batch_json:
            return emit_session_status("ok" if active else "blocked", "master session active" if active else f"master session {state}", key, socket_path, meta_path, namespace, namespace_source)
        print("active" if active else state)
        return 0 if active else 1

    if args.close_session:
        active, _, _, _ = check_master_session(args, socket_path)
        if active:
            close_command = base_ssh_command(args, socket_path) + ["-O", "exit", target(args)]
            subprocess.run(close_command, capture_output=True, text=True)
        cleanup_session_files(socket_path, meta_path)
        if args.batch_json:
            return emit_session_status("ok", "master session closed", key, socket_path, meta_path, namespace, namespace_source)
        print(f"closed session {key}")
        return 0

    active_session = False
    if auto_reuse:
        active_session, state, _, _ = check_master_session(args, socket_path)
        if not active_session and state == "stale":
            cleanup_session_files(socket_path, meta_path)

    if auto_reuse and not active_session:
        try:
            password = resolve_password(args)
        except (PromptError, OSError, SystemExit) as exc:
            if args.batch_json:
                return emit_blocked_json(str(exc))
            if isinstance(exc, SystemExit):
                raise
            print(str(exc), file=sys.stderr)
            return 2
        boot_ok, boot_result = bootstrap_session(args, socket_path, meta_path, key, namespace, namespace_source, password)
        if not boot_ok:
            if args.batch_json:
                print(json.dumps(boot_result, ensure_ascii=False, indent=2))
                return 0
            print(boot_result["reason"], file=sys.stderr)
            stderr = boot_result["evidence"].get("stderr")
            if stderr:
                print(stderr, file=sys.stderr)
            return 1
        active_session = True
        if args.ensure_session:
            if args.batch_json:
                print(json.dumps(boot_result, ensure_ascii=False, indent=2))
            else:
                print(f"session ready: {key}")
            return 0

    if args.ensure_session:
        if args.batch_json:
            return emit_session_status("ok", "master session active", key, socket_path, meta_path, namespace, namespace_source)
        print(f"session ready: {key}")
        return 0

    if auto_reuse and not active_session:
        reason = "No active session for this thread. Bootstrap with --prompt-password or --ensure-session first."
        if args.batch_json:
            return emit_blocked_json(reason)
        print(reason, file=sys.stderr)
        return 2

    use_expect = not auto_reuse
    password: str | None = None
    if use_expect:
        try:
            password = resolve_password(args)
        except (PromptError, OSError, SystemExit) as exc:
            if args.batch_json:
                return emit_blocked_json(str(exc))
            if isinstance(exc, SystemExit):
                raise
            print(str(exc), file=sys.stderr)
            return 2

    ssh_command = base_ssh_command(args, socket_path if auto_reuse else None) + [target(args), args.remote_command]
    completed, safe_stdout, safe_stderr = run_and_redact(password, ssh_command, use_expect=use_expect)

    if auto_reuse:
        if completed.returncode == 0:
            touch_session_metadata(meta_path, args, socket_path, key, namespace, namespace_source)
        else:
            active, _, _, _ = check_master_session(args, socket_path)
            if not active:
                cleanup_session_files(socket_path, meta_path)

    if not args.batch_json:
        sys.stdout.write(safe_stdout)
        sys.stderr.write(safe_stderr)
        return completed.returncode

    status, reason = (classify(completed.returncode, safe_stdout, safe_stderr) if use_expect else classify_command_failure(completed.returncode, safe_stdout, safe_stderr))
    result = {
        "status": status,
        "reason": reason,
        "phase": "command",
        "evidence": {
            "command": shlex.join(ssh_command),
            "exit_code": completed.returncode,
            "stdout": safe_stdout.strip(),
            "stderr": safe_stderr.strip(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
