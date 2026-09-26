"""SECOND SUN — mix and master.

music (hall) + sound design (outdoor space) -> -14 LUFS integrated, <= -1 dBTP,
with the film's silences kept truly silent (225.0–230.0 s is digital zero).
    python mix.py -> build/SECOND_SUN_score.wav (score only, 24-bit)
                     build/mix.wav (full film mix, 24-bit)
"""
import os
import subprocess
import sys

import numpy as np
import pyloudnorm as pyln
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared"))
from foxfolly.audio import automation, convolve_reverb, db, limiter, reverb_ir, true_peak  # noqa: E402

import timeline as TL  # noqa: E402

SR = 48000
BUILD = os.path.join(HERE, "..", "build")
N = int(TL.DURATION * SR)


def fit(x):
    x = x[:N]
    if len(x) < N:
        x = np.r_[x, np.zeros((N - len(x), 2), np.float32)]
    return x


def master(x, target=-14.0, ceiling=-1.6):
    meter = pyln.Meter(SR)
    for _ in range(3):
        x = x * db(target - meter.integrated_loudness(x))
        x = limiter(x, ceiling_db=ceiling)
    return x, meter.integrated_loudness(x), true_peak(x)


def write24(path, x):
    tmp = path + ".f32.wav"
    wavfile.write(tmp, SR, x.astype(np.float32))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "pcm_s24le", path], check=True)
    os.remove(tmp)


def silence_windows(x):
    x[int(225.0 * SR):int(230.0 * SR)] = 0.0       # hard cut to white = hard cut to digital silence
    return x


def main():
    music = fit(np.load(os.path.join(BUILD, "music_dry.npy")))
    sfx = fit(np.load(os.path.join(BUILD, "sfx_dry.npy")))
    hall = reverb_ir(3.6, decay=1.4, seed=5)
    space = reverb_ir(1.4, decay=0.7, seed=9, predelay=0.012)
    music = music * 0.75 + convolve_reverb(music, hall) * 0.42
    from scipy import signal as sg
    sfx = sg.sosfilt(sg.butter(4, 11000, "low", fs=SR, output="sos"), sfx, axis=0).astype(np.float32)
    sfx = sfx * 0.9 + convolve_reverb(sfx, space) * 0.14
    # stem automation (dB): music leads; sound design carries the Hunter and the end of the world
    m_auto = automation([(0, 0), (83, 0), (97.0, -2), (101, 0), (136, 0), (173, 0), (180, 0), (191.8, 0),
                         (199, 1), (215, 0), (225, 0), (309, 0)], N)
    s_auto = automation([(0, -6), (17, -5), (83, -4), (97.3, -2), (101, 0), (123, -3), (136, -5), (173, -4),
                         (180, -3), (191.5, 0), (199, -1), (215, -3), (225, -8), (309, -8)], N)
    music = music * m_auto[:, None]
    sfx = sfx * s_auto[:, None] * 0.55
    # section gains (dB) shaping the whole film's dynamic arc (applied to both stems)
    sec = automation([(0, 0), (17.3, -1), (28.3, -1.5), (37.3, -4), (49.3, -0.5), (59.3, -3), (72.3, -1.5),
                      (83.3, -0.5), (90.3, 3), (97.2, 3), (101.3, 0), (110.3, -2.5), (123.3, -2.5), (130.3, 0),
                      (136.3, 6), (145.3, -1), (160.3, -0.5), (172.8, -0.5), (173.4, -7), (179.7, -7), (180.2, -1),
                      (191.3, 1), (199.3, -1.8), (215.3, 0), (225, 0), (254.3, -2.5), (261.3, -1), (291.3, -1.5),
                      (309, -1.5)], N)
    music = music * sec[:, None]
    sfx = sfx * sec[:, None]
    full = silence_windows(music + sfx)
    score = silence_windows(music.copy())
    # gentle fades at the very start and end
    fi, fo = int(0.5 * SR), int(0.6 * SR)
    for x in (full, score):
        x[:fi] *= np.linspace(0, 1, fi)[:, None]
        x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    full, lu, tp = master(full)
    full = silence_windows(full)
    score_m, lu2, tp2 = master(score)
    score_m = silence_windows(score_m)
    write24(os.path.join(BUILD, "mix.wav"), full)
    write24(os.path.join(BUILD, "SECOND_SUN_score.wav"), score_m)
    print(f"mix: {lu:.2f} LUFS, TP {tp:.2f} dBTP | score: {lu2:.2f} LUFS, TP {tp2:.2f} dBTP")


if __name__ == "__main__":
    main()
