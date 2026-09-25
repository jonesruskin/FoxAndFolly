#!/usr/bin/env python3
"""One-command build for "Facing East".

    python build.py              # music + video + mux + subtitles + thumbnail -> output/
    python build.py --skip-video # reuse build/video.mp4 (e.g. after a music tweak)
    python build.py --qa         # also extract QA frames + loudness report into build/qa/

Intermediate files go to build/ (git-ignored); deliverables go to output/ (Git LFS).
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "output")
sys.path.insert(0, SRC)
import story  # noqa: E402

THUMB_TIME = 196.0  # dawn: Hesper lit gold, bees arriving, no narration on screen


def run(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.run(cmd, check=True, **kw)


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(path):
    """Cue times = the span each line is at least half-visible on screen."""
    with open(path, "w", encoding="utf-8") as f:
        for i, (s, e, txt) in enumerate(story.LINES, 1):
            f.write(f"{i}\n{srt_time(s + story.FADE / 2)} --> {srt_time(e - story.FADE / 2)}\n{txt}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-video", action="store_true")
    ap.add_argument("--skip-music", action="store_true")
    ap.add_argument("--qa", action="store_true")
    a = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    problems = story.check()
    if problems:
        sys.exit("timeline problems: " + "; ".join(problems))

    if not a.skip_music:
        run([sys.executable, os.path.join(SRC, "music.py")])
    if not a.skip_video:
        run([sys.executable, os.path.join(SRC, "render.py"), "video"])

    final = os.path.join(OUT, "final_video.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-i", os.path.join(BUILD, "video.mp4"), "-i", os.path.join(BUILD, "music.wav"),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2",
         "-metadata", f"title={story.TITLE}", "-metadata", "artist=Fox & Folly",
         "-movflags", "+faststart", final])
    shutil.copyfile(os.path.join(BUILD, "music.wav"), os.path.join(OUT, "music.wav"))
    write_srt(os.path.join(OUT, "subtitles.en.srt"))
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{THUMB_TIME}", "-i", final,
         "-frames:v", "1", "-vf", "scale=1280:720:flags=lanczos",
         os.path.join(OUT, "thumbnail_frame.png")])
    shutil.copyfile(os.path.join(HERE, "script.md"), os.path.join(OUT, "script.md"))
    shutil.copyfile(os.path.join(HERE, "production_notes.md"),
                    os.path.join(OUT, "production_notes.md"))
    if a.qa:
        run([sys.executable, os.path.join(SRC, "qa.py")])
    print("done ->", OUT)


if __name__ == "__main__":
    main()
