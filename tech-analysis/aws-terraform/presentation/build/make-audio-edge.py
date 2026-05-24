#!/usr/bin/env python3
"""Generate per-section Korean TTS audio using Edge TTS (SunHi neural voice).

Outputs:
  audio/section-NN.mp3 (neural Korean voice, ~24kHz)
  audio/section-NN.m4a (AAC converted via ffmpeg)
  audio/section-NN.dur (duration in seconds)
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import edge_tts

BUILD = Path(__file__).parent.resolve()
AUDIO = BUILD / "audio"
AUDIO.mkdir(exist_ok=True)

VOICE = "ko-KR-SunHiNeural"
# Speech tuning — slightly slower for clarity, small pitch lift for warmth
RATE = "-5%"   # slightly slower than default
PITCH = "+0Hz"
VOLUME = "+0%"


async def synth(text: str, out_mp3: Path) -> None:
    communicate = edge_tts.Communicate(
        text,
        voice=VOICE,
        rate=RATE,
        pitch=PITCH,
        volume=VOLUME,
    )
    await communicate.save(str(out_mp3))


def ffmpeg_to_m4a(mp3: Path, m4a: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(mp3),
            "-c:a", "aac", "-b:a", "192k",
            str(m4a),
        ],
        check=True,
    )


def duration_of(m4a: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(m4a),
        ]
    )
    return float(out.strip())


async def main() -> None:
    data = json.loads((BUILD / "narrations.json").read_text(encoding="utf-8"))
    for i, sec in enumerate(data["sections"], 1):
        idx = f"{i:02d}"
        mp3 = AUDIO / f"section-{idx}.mp3"
        m4a = AUDIO / f"section-{idx}.m4a"
        dur_file = AUDIO / f"section-{idx}.dur"

        # Remove old AIFF/m4a/dur to avoid confusion
        old_aiff = AUDIO / f"section-{idx}.aiff"
        if old_aiff.exists():
            old_aiff.unlink()

        print(f"[{idx}] synth ({VOICE})...", flush=True)
        await synth(sec["narration"], mp3)

        ffmpeg_to_m4a(mp3, m4a)
        dur = duration_of(m4a)
        dur_file.write_text(f"{dur}\n")
        print(f"[{idx}] duration={dur:.2f}s")

    print("done.")


if __name__ == "__main__":
    asyncio.run(main())
