#!/usr/bin/env python3
"""Check whether an output artifact exists and looks reasonable."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def detect_kind(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    suffix = path.suffix.lower()
    if suffix in {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}:
        return 'audio'
    if suffix in {'.png', '.jpg', '.jpeg', '.webp'}:
        return 'image'
    if suffix in {'.txt', '.md', '.json'}:
        return 'text'
    return 'generic'


def main() -> int:
    parser = argparse.ArgumentParser(description='Artifact reasonableness check')
    parser.add_argument('--path', required=True)
    parser.add_argument('--kind', choices=['audio', 'image', 'text', 'generic'])
    parser.add_argument('--min-size', type=int, default=1)
    parser.add_argument('--max-size', type=int)
    args = parser.parse_args()

    path = Path(args.path).expanduser()
    evidence = {'path': str(path), 'exists': path.exists(), 'kind': detect_kind(path, args.kind)}

    if not path.exists():
        print(json.dumps({
            'status': 'blocked',
            'reason': f'Artifact does not exist: {path}.',
            'next_step': 'Verify the output path and rerun the generating request.',
            'evidence': evidence,
        }, ensure_ascii=False, indent=2))
        return 0

    size = path.stat().st_size
    evidence['size_bytes'] = size
    evidence['suffix'] = path.suffix.lower()

    if size < args.min_size:
        print(json.dumps({
            'status': 'blocked',
            'reason': f'Artifact exists but is smaller than expected ({size} bytes).',
            'next_step': 'Inspect the generating request and verify the artifact is complete.',
            'evidence': evidence,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.max_size and size > args.max_size:
        print(json.dumps({
            'status': 'blocked',
            'reason': f'Artifact exists but is larger than the configured upper bound ({size} bytes).',
            'next_step': 'Verify the artifact type and confirm the output is not malformed.',
            'evidence': evidence,
        }, ensure_ascii=False, indent=2))
        return 0

    if evidence['kind'] == 'text':
        try:
            preview = path.read_text(encoding='utf-8', errors='ignore')[:200]
        except Exception:
            preview = ''
        evidence['preview'] = preview
        if not preview.strip():
            print(json.dumps({
                'status': 'blocked',
                'reason': 'Text artifact exists but appears empty or whitespace-only.',
                'next_step': 'Verify the task really produced text and rerun the request if needed.',
                'evidence': evidence,
            }, ensure_ascii=False, indent=2))
            return 0

    print(json.dumps({
        'status': 'ok',
        'reason': 'Artifact exists and passed the configured basic checks.',
        'next_step': 'If this is a final acceptance path, also validate the original example request and repeat once.',
        'evidence': evidence,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
