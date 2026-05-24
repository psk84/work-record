#!/usr/bin/env bash
# Generate per-section Korean TTS audio (Yuna) and convert to AAC.
set -euo pipefail

cd "$(dirname "$0")"

AUDIO_DIR="./audio"
mkdir -p "$AUDIO_DIR"

# Read narrations from JSON (using python for robust JSON parsing)
python3 - <<'PY' > narrations.list
import json, sys
data = json.load(open("narrations.json", encoding="utf-8"))
for i, s in enumerate(data["sections"], 1):
    print(f"{i:02d}\t{s['narration']}")
PY

while IFS=$'\t' read -r idx text; do
  aiff="$AUDIO_DIR/section-$idx.aiff"
  m4a="$AUDIO_DIR/section-$idx.m4a"
  txt="$AUDIO_DIR/section-$idx.txt"

  echo "[$idx] generating audio..."
  echo "$text" > "$txt"
  say -v Yuna -r 190 -o "$aiff" -f "$txt"

  # convert aiff → m4a (AAC) with ffmpeg
  ffmpeg -y -loglevel error -i "$aiff" -c:a aac -b:a 192k "$m4a"

  # measure duration in seconds (float)
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$m4a")
  echo "[$idx] duration: $dur s"
  echo "$dur" > "$AUDIO_DIR/section-$idx.dur"
done < narrations.list

rm narrations.list
echo "done."
