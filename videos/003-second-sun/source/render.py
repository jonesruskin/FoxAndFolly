"""SECOND SUN — renderer.

    python render.py stills 20 150 185            # style frames -> build/stills/
    python render.py animatic                     # low-res full timeline -> build/animatic.mp4
    python render.py shots [S03 S19 ...]          # per-shot segments -> build/shots/Sxx.mp4
    python render.py assemble                     # concat shots -> build/picture.mp4

Every shot renders to its own lossless-quality segment, so any single shot can
be re-rendered and re-assembled without touching the rest of the film.
"""
import argparse
import importlib
import math
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared"))

import timeline as TL  # noqa: E402
from foxfolly.anim import smoothstep  # noqa: E402
from foxfolly.text import TextCache, composite  # noqa: E402
from frame import Frame, finish, to_uint8  # noqa: E402

BUILD = os.path.join(HERE, "..", "build")
FPS = TL.FPS
W, H = TL.W, TL.H
SHOT_MODULES = ["shots_open", "shots_act1", "shots_act2", "shots_act3", "shots_act4", "shots_epilogue"]
_REG = None
_TEXT = TextCache()


def registry():
    global _REG
    if _REG is None:
        _REG = {}
        for m in SHOT_MODULES:
            try:
                mod = importlib.import_module(m)
            except ModuleNotFoundError as e:
                if e.name != m:
                    raise
                continue
            _REG.update(getattr(mod, "SHOTS", {}))
    return _REG


def draw_cards(img, t):
    s = img.shape[1] / W
    for (a, b, txt, style) in TL.CARDS:
        if not (a - 0.1 <= t <= b + 0.1):
            continue
        k = smoothstep(a, a + TL.CARD_FADE, t) * (1 - smoothstep(b - TL.CARD_FADE, b, t))
        if k <= 0:
            continue
        if style == "small":
            spr = _TEXT.get(txt, size=int(40 * s), face="CormorantGaramond-Regular.ttf", color=(0.86, 0.84, 0.80),
                            glow_alpha=0.0, shadow_alpha=0.4, letter_spacing=3.0 * s)
            composite(img, spr, img.shape[1] / 2, img.shape[0] * 0.5, k)
        elif style == "card":
            spr = _TEXT.get(txt, size=int(52 * s), color=(0.95, 0.92, 0.86), glow_alpha=0.12,
                            shadow_alpha=0.7, max_width=int(1500 * s), line_gap=1.45)
            composite(img, spr, img.shape[1] / 2, img.shape[0] * 0.80, k)
        elif style == "title":
            spr = _TEXT.get(txt, size=int(120 * s), face="CormorantGaramond-Medium.ttf", color=(0.97, 0.93, 0.86),
                            glow_alpha=0.25, shadow_alpha=0.3, letter_spacing=24 * s)
            composite(img, spr, img.shape[1] / 2, img.shape[0] * 0.47, k)
            sub = _TEXT.get(TL.SUBTITLE, size=int(48 * s), color=(0.90, 0.86, 0.80), glow_alpha=0.0,
                            shadow_alpha=0.3, letter_spacing=1.5 * s)
            composite(img, sub, img.shape[1] / 2, img.shape[0] * 0.58, k * smoothstep(a + 0.6, a + 1.8, t))
    return img


def render_frame(t, scale=1.0, frame_idx=None):
    if frame_idx is None:
        frame_idx = int(round(t * FPS))
    sid, u, dur = TL.shot_at(t)
    F = Frame(t, scale)
    fn = registry().get(sid)
    if fn is None:
        F.post = {"grade": "cold_open"}
        _missing(F, sid, u)
    else:
        fn(F, u, dur, t)
    img = F.snapshot()
    img = finish(img, F.post, frame_idx, t)
    img = draw_cards(img, t)
    return to_uint8(img, frame_idx, grain=F.post.get("grain", 0.02))


def _missing(F, sid, u):
    import skia
    F.cv.clear(skia.Color4f(0.05, 0.05, 0.06, 1))
    font = skia.Font(None, 60)
    F.cv.drawString(f"{sid}  (not built)", 80, 140, font, skia.Paint(Color4f=skia.Color4f(0.8, 0.3, 0.3, 1)))


# ------------------------------------------------------------------ CLI
_SCALE = 1.0


def _work(i):
    return render_frame(i / FPS, _SCALE, i).tobytes()


def encode(frames, out, scale, crf=10, preset="medium"):
    w, h = int(W * scale), int(H * scale)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import multiprocessing as mp
    t0 = time.time()
    global _SCALE
    _SCALE = scale
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(_work, frames, chunksize=2)):
            ff.stdin.write(buf)
    ff.stdin.close()
    ff.wait()
    return time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["stills", "animatic", "shots", "assemble"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    if a.mode == "stills":
        import cv2
        out = os.path.join(BUILD, "stills")
        os.makedirs(out, exist_ok=True)
        for x in a.args:
            t = float(x)
            t0 = time.time()
            fr = render_frame(t, a.scale)
            fn = os.path.join(out, f"s_{t:07.2f}.png")
            cv2.imwrite(fn, fr[..., ::-1])
            print(fn, f"{time.time() - t0:.2f}s", flush=True)
    elif a.mode == "animatic":
        sc = a.scale if a.scale != 1.0 else 0.25
        frames = range(0, int(TL.DURATION * FPS))
        raw = os.path.join(BUILD, "animatic_raw.mp4")
        dt = encode(frames, raw, sc, crf=23, preset="veryfast")
        mixp = os.path.join(BUILD, "mix.wav")
        if os.path.exists(mixp):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-i", mixp, "-c:v", "copy", "-c:a", "aac",
                            "-b:a", "192k", "-shortest", os.path.join(BUILD, "animatic.mp4")], check=True)
        print(f"animatic in {dt:.0f}s")
    elif a.mode == "shots":
        os.makedirs(os.path.join(BUILD, "shots"), exist_ok=True)
        want = a.args or [s[0] for s in TL.SHOTS]
        for sid, s0, s1, name in TL.SHOTS:
            if sid not in want:
                continue
            f0, f1 = int(round(s0 * FPS)), int(round(s1 * FPS))
            dt = encode(range(f0, f1), os.path.join(BUILD, "shots", f"{sid}.mp4"), a.scale, crf=8)
            print(f"{sid} {f1 - f0} frames in {dt:.0f}s ({dt / max(1, f1 - f0):.2f}s/f)", flush=True)
    elif a.mode == "assemble":
        lst = os.path.join(BUILD, "shots", "list.txt")
        with open(lst, "w") as f:
            for sid, *_ in TL.SHOTS:
                f.write(f"file '{sid}.mp4'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", os.path.join(BUILD, "picture_lossless.mp4")], check=True)
        print("assembled")


if __name__ == "__main__":
    main()
