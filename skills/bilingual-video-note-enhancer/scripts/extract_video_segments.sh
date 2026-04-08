#!/bin/zsh
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 <youtube_url> <start_seconds> <duration_seconds> <output_mp4>" >&2
  exit 1
fi

youtube_url="$1"
start_seconds="$2"
duration_seconds="$3"
output_mp4="$4"
end_seconds=$(python3 - <<'PY' "$start_seconds" "$duration_seconds"
import sys
start = float(sys.argv[1])
duration = float(sys.argv[2])
print(start + duration)
PY
)

yt-dlp --force-overwrites --downloader ffmpeg -f 232 \
  --download-sections "*${start_seconds}-${end_seconds}" \
  -o "${output_mp4}" \
  "${youtube_url}"
