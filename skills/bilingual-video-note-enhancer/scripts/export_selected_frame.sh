#!/bin/zsh
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: $0 <input_mp4> <offset_seconds_in_clip> <output_png>" >&2
  exit 1
fi

input_mp4="$1"
offset_seconds="$2"
output_png="$3"

ffmpeg -y -ss "${offset_seconds}" -i "${input_mp4}" -frames:v 1 "${output_png}"
