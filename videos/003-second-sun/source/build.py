#!/usr/bin/env python3
"""SECOND SUN — one command builds the whole film.

    python build.py            # score + sound + mix + all shots + assemble + deliver -> ../second_sun/
    python build.py --shots S19 S22   # re-render only these shots, then re-assemble and re-deliver
    python build.py --audio-only      # rebuild score/SFX/mix and re-mux onto the existing picture
    python build.py --qc              # technical QC report (ffprobe, blackdetect, freezedetect, ebur128)

Deliverables (Git LFS for media), written to the top of second_sun/:
    second_sun/SECOND_SUN_final.mp4   1920x1080 24 fps H.264 High CRF 16 yuv420p, AAC 320k 48 kHz
    second_sun/SECOND_SUN_score.wav   48 kHz / 24-bit
    second_sun/SECOND_SUN_poster.png  S19 second-sunrise frame
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.abspath(os.path.join(HERE, ".."))      # .../second_sun
BUILD = os.path.join(VID, "build")                     # intermediates (git-ignored)
OUT = VID                                              # deliverables live at the top of second_sun/
sys.path.insert(0, HERE)
import timeline as TL  # noqa: E402

POSTER_T = 182.4


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def py(script, *args):
    run([sys.executable, os.path.join(HERE, script), *args])


def deliver():
    os.makedirs(OUT, exist_ok=True)
    final = os.path.join(OUT, "SECOND_SUN_final.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(BUILD, "picture_lossless.mp4"),
         "-i", os.path.join(BUILD, "mix.wav"), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-tune", "grain", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-t", f"{TL.DURATION}",
         "-metadata", "title=SECOND SUN", "-metadata", "artist=Fox & Folly", "-movflags", "+faststart", final])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(BUILD, "SECOND_SUN_score.wav"),
         "-c:a", "pcm_s24le", "-ar", "48000", os.path.join(OUT, "SECOND_SUN_score.wav")])
    run([sys.executable, os.path.join(HERE, "render.py"), "stills", f"{POSTER_T}"])
    import shutil
    shutil.copyfile(os.path.join(BUILD, "stills", f"s_{POSTER_T:07.2f}.png"), os.path.join(OUT, "SECOND_SUN_poster.png"))


def qc():
    final = os.path.join(OUT, "SECOND_SUN_final.mp4")
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,bit_rate,sample_rate,channels,duration",
                        "-show_entries", "format=duration,bit_rate", "-of", "default=nw=1", final],
                       capture_output=True, text=True).stdout
    print(r)
    bd = subprocess.run(["ffmpeg", "-i", final, "-vf", "blackdetect=d=0.2:pic_th=0.97:pix_th=0.05", "-an", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    print("black:", re.findall(r"black_start:(\S+) black_end:(\S+)", bd))
    fz = subprocess.run(["ffmpeg", "-i", final, "-vf", "freezedetect=n=0.0008:d=1.5", "-an", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    print("freeze:", re.findall(r"freeze_start: (\S+).*?freeze_end: (\S+)", fz, re.S))
    lo = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", final, "-map", "0:a", "-af", "ebur128=peak=true",
                         "-f", "null", "-"], capture_output=True, text=True).stderr
    print("loudness:", re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)[-1], "LUFS, TP",
          re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lo)[-1], "dBTP, LRA", re.findall(r"LRA:\s+([\d.]+) LU", lo)[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", nargs="*")
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    if a.qc:
        return qc()
    probs = TL.check()
    if probs:
        sys.exit("timeline problems: " + "; ".join(probs))
    py("music.py")
    py("sfx.py")
    py("mix.py")
    if not a.audio_only:
        py("render.py", "shots", *(a.shots or []))
        py("render.py", "assemble")
    deliver()
    qc()


if __name__ == "__main__":
    main()
