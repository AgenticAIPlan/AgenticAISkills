#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 7:
        print(
            "usage: update_frame_map.py <map_json> <target> <selected_time> "
            "<window_start> <frame_number> <extract_time>",
            file=sys.stderr,
        )
        return 1

    map_path = Path(sys.argv[1])
    target = sys.argv[2]
    selected_time = float(sys.argv[3])
    window_start = float(sys.argv[4])
    frame_number = int(sys.argv[5])
    extract_time = float(sys.argv[6])

    if map_path.exists():
        data = json.loads(map_path.read_text())
    else:
        data = []

    updated = False
    for row in data:
        if row.get("target") == target:
            row.update(
                {
                    "selected_time": selected_time,
                    "window_start": window_start,
                    "frame_number": frame_number,
                    "extract_time": extract_time,
                }
            )
            updated = True
            break

    if not updated:
        data.append(
            {
                "index": len(data) + 1,
                "target": target,
                "selected_time": selected_time,
                "window_start": window_start,
                "frame_number": frame_number,
                "extract_time": extract_time,
            }
        )

    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
