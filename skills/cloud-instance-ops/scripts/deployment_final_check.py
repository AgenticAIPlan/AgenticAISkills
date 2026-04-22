#!/usr/bin/env python3
"""Final acceptance checks for deployed services."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def probe(url: str, timeout: int) -> tuple[bool, int | None, str]:
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(256)
            return True, resp.status, body.decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return False, e.code, str(e)
    except Exception as e:
        return False, None, repr(e)


def main() -> int:
    parser = argparse.ArgumentParser(description='Deployment final acceptance check')
    parser.add_argument('--url', required=True)
    parser.add_argument('--repeat', type=int, default=2)
    parser.add_argument('--expect-status', type=int, default=200)
    parser.add_argument('--artifact')
    parser.add_argument('--artifact-kind', choices=['audio', 'image', 'text', 'generic'], default='generic')
    parser.add_argument('--min-artifact-size', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()

    evidence = {'url': args.url, 'probes': [], 'artifact': None}

    for i in range(args.repeat):
        ok, status, detail = probe(args.url, args.timeout)
        evidence['probes'].append({'attempt': i + 1, 'ok': ok, 'status': status, 'detail': detail[:200]})
        if not ok or status != args.expect_status:
            print(json.dumps({
                'status': 'blocked',
                'reason': f'HTTP probe failed on attempt {i + 1}.',
                'next_step': 'Inspect service logs, verify the intended service owns the port, and retry the original request.',
                'evidence': evidence,
            }, ensure_ascii=False, indent=2))
            return 0
        time.sleep(1)

    if args.artifact:
        path = Path(args.artifact).expanduser()
        artifact = {'path': str(path), 'exists': path.exists(), 'kind': args.artifact_kind}
        evidence['artifact'] = artifact
        if not path.exists():
            print(json.dumps({
                'status': 'blocked',
                'reason': 'Artifact path was provided but the file does not exist.',
                'next_step': 'Verify the output path and rerun the original example request.',
                'evidence': evidence,
            }, ensure_ascii=False, indent=2))
            return 0
        artifact['size_bytes'] = path.stat().st_size
        if artifact['size_bytes'] < args.min_artifact_size:
            print(json.dumps({
                'status': 'blocked',
                'reason': 'Artifact exists but is smaller than the configured minimum size.',
                'next_step': 'Inspect the generated artifact and confirm the service really produced the expected output.',
                'evidence': evidence,
            }, ensure_ascii=False, indent=2))
            return 0

    print(json.dumps({
        'status': 'ok',
        'reason': 'Service probes succeeded and the optional artifact check passed.',
        'next_step': 'If the task provided a raw curl example, rerun that exact request before final sign-off.',
        'evidence': evidence,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
