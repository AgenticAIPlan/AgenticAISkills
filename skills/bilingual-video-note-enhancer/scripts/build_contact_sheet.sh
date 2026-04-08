#!/bin/zsh
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 <input_mp4> <fps> <tile_cols>x<tile_rows> <output_png>" >&2
  exit 1
fi

input_mp4="$1"
fps="$2"
tile="$3"
output_png="$4"

ffmpeg -y -i "${input_mp4}" -vf "fps=${fps},tile=${tile}" "${output_png}"
