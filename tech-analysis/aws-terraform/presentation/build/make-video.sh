#!/usr/bin/env bash
# Build per-section MP4 clips, then concat into final presentation.mp4.
# - Short sections (<=1080 tall): pad to 1080 centered, dark bg
# - Tall sections (>1080):       vertical pan over the section duration
set -euo pipefail

cd "$(dirname "$0")"

CLIP_DIR="./clips"
mkdir -p "$CLIP_DIR"

W=1920
H=1080
FPS=30
BG="#0d1117"

shopt -s nullglob

# Build per-section clips
> concat.list
for img in screenshots/section-*.png; do
  base=$(basename "$img" .png)
  idx=${base#section-}
  aud="audio/section-$idx.m4a"
  dur=$(cat "audio/section-$idx.dur")
  out="$CLIP_DIR/section-$idx.mp4"

  height=$(sips -g pixelHeight "$img" | awk '/pixelHeight/ {print $2}')

  if [ "$height" -le "$H" ]; then
    echo "[$idx] padding (h=$height <= $H)  dur=${dur}s"
    vf="pad=${W}:${H}:0:(${H}-ih)/2:color=${BG},fps=${FPS},format=yuv420p"
  else
    pan_max=$((height - H))
    # Hold top 1s, pan over (dur-2)s, hold bottom 1s
    pan_t="if(lt(t,1),0,if(gt(t,${dur}-1),${pan_max},${pan_max}*(t-1)/(${dur}-2)))"
    echo "[$idx] panning (h=$height > $H, pan_max=$pan_max)  dur=${dur}s"
    vf="crop=${W}:${H}:0:'${pan_t}',fps=${FPS},format=yuv420p"
  fi

  ffmpeg -y -loglevel error \
    -loop 1 -i "$img" \
    -i "$aud" \
    -t "$dur" \
    -vf "$vf" \
    -c:v libx264 -preset medium -crf 20 \
    -c:a aac -b:a 192k \
    -shortest \
    "$out"

  echo "file '$out'" >> concat.list
done

# Concat all clips
echo ""
echo "→ concatenating clips..."
ffmpeg -y -loglevel error \
  -f concat -safe 0 -i concat.list \
  -c:v libx264 -preset medium -crf 20 \
  -c:a aac -b:a 192k \
  ../presentation.mp4

# Get final duration & size
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ../presentation.mp4)
size=$(du -h ../presentation.mp4 | awk '{print $1}')
echo ""
echo "✅ done. ../presentation.mp4  duration=${dur}s  size=${size}"
