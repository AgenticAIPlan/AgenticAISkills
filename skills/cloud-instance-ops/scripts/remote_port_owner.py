#!/usr/bin/env python3
"""Inspect which local process owns a listening port."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess


def run_cmd(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect which process owns a local port")
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()

    evidence = {'port': args.port, 'tool': None, 'matches': []}

    if shutil.which('ss'):
        cp = run_cmd(['ss', '-tulpn'])
        evidence['tool'] = 'ss'
        for line in cp.stdout.splitlines():
            if f':{args.port} ' in line or line.rstrip().endswith(f':{args.port}'):
                evidence['matches'].append(line.strip())
    elif shutil.which('lsof'):
        cp = run_cmd(['lsof', f'-i:{args.port}', '-nP'])
        evidence['tool'] = 'lsof'
        evidence['matches'] = [line.strip() for line in cp.stdout.splitlines()[1:]]
    else:
        print(json.dumps({
            'status': 'unsupported',
            'reason': 'Neither ss nor lsof is available locally.',
            'next_step': 'Install ss or lsof, then rerun the port owner check.',
            'evidence': evidence,
        }, ensure_ascii=False, indent=2))
        return 0

    if evidence['matches']:
        print(json.dumps({
            'status': 'ok',
            'reason': f'Found listeners for port {args.port}.',
            'next_step': 'Inspect the owning process before starting another service on the same port.',
            'evidence': evidence,
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            'status': 'ok',
            'reason': f'No listener was found on port {args.port}.',
            'next_step': 'The port appears free for the next task.',
            'evidence': evidence,
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
