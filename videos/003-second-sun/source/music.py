"""SECOND SUN — original score, composed to picture (all synthesised).

Leitmotifs
  TOGETHER  3/4 lullaby, D major: D5 C#5 A4 | B4 A4 F#4 | G4 F#4 E4 | D4
  OLD HORN  rising fifth D2 -> A2, solo cello sul tasto (+ closed-mouth hum colour)
  WISP      A5 -> D6 two-note call on celesta
  THE STAR  one pure glassy tone on G#5 (a tritone against D)

Cues are pinned to timeline.EV / DUET so swells land on picture.
    python music.py   -> build/score_stems.npz (music bus, pre-master)
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared"))

import instruments as I  # noqa: E402
import timeline as TL  # noqa: E402

SR = I.SR
EV = TL.EV
DUR = TL.DURATION


class Bus:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.L = np.zeros(self.n, np.float32)
        self.R = np.zeros(self.n, np.float32)

    def add(self, t, x, g=1.0, pan=0.0):
        i0 = int(round(t * SR))
        if i0 < 0:
            x, i0 = x[-i0:], 0
        m = min(len(x), self.n - i0)
        if m <= 0:
            return
        a = (pan + 1) * math.pi / 4
        self.L[i0:i0 + m] += x[:m] * g * math.cos(a)
        self.R[i0:i0 + m] += x[:m] * g * math.sin(a)

    def st(self):
        return np.stack([self.L, self.R], 1)


def human(t, k, amt=0.012, seed=0):
    """Humanised timing: small deterministic offsets."""
    r = math.sin(k * 12.9898 + seed * 78.233) * 43758.5453
    return t + (r - math.floor(r) - 0.5) * 2 * amt


# notes
D2, Ds, E2, F2, G2, A2, Bb2, B2 = 38, 39, 40, 41, 43, 45, 46, 47
C3, Cs3, D3, E3, F3, Fs3, G3, A3, Bb3, B3 = 48, 49, 50, 52, 53, 54, 55, 57, 58, 59
C4, Cs4, D4, E4, F4, Fs4, G4, Gs4, A4, Bb4, B4 = 60, 61, 62, 64, 65, 66, 67, 68, 69, 70, 71
C5, Cs5, D5, E5, F5, Fs5, G5, Gs5, A5, B5 = 72, 73, 74, 76, 77, 78, 79, 80, 81, 83
D6 = 86

CH = {"D": [D3, A3, D4, Fs4], "Dadd9": [D3, A3, E4, Fs4], "G": [G2, D3, G3, B3], "Bm": [B2, Fs3, B3, D4],
      "A": [A2, E3, A3, Cs4], "Em": [E2, B2, E3, G3], "D/F#": [Fs3, A3, D4], "Gmaj7": [G2, D3, Fs3, B3],
      "Dm": [D3, A3, D4, F4], "Bb": [Bb2, F3, Bb3, D4], "Gm": [G2, D3, G3, Bb3], "Asus": [A2, E3, A3, D4],
      "A7": [A2, E3, G3, Cs4]}

TOGETHER = [(0, D5, 1), (1, Cs5, 1), (2, A4, 1), (3, B4, 1), (4, A4, 1), (5, Fs4, 1), (6, G4, 1), (7, Fs4, 1),
            (8, E4, 1), (9, D4, 3)]
TOGETHER_B = [(12, Fs4, 1), (13, A4, 1), (14, D5, 1), (15, Cs5, 1.5), (16.5, D5, 3.5)]


def arpeggio(bus, t0, t1, chord, step, inst="harp", vel=0.35, pan=0.0, seed=0, up=True):
    k = 0
    tt = t0
    notes = chord + [c + 12 for c in chord[1:]]
    while tt < t1:
        m = notes[k % len(notes)] if up else notes[-1 - (k % len(notes))]
        x = I.harp(m, vel, 3.0, seed=seed + k) if inst == "harp" else I.piano(m, vel, 3.5, seed=seed + k)
        bus.add(human(tt, k, 0.01, seed), x, 1.0, pan + 0.3 * math.sin(k))
        tt += step
        k += 1


def build():
    mus = Bus(DUR + 4)
    # ---------------------------------------------------------------- M1 Deep Time (0–17)
    t = np.arange(int(17.5 * SR)) / SR
    drone = (np.sin(2 * np.pi * I.hz(26) * t) * 0.7 + np.sin(2 * np.pi * I.hz(33) * t) * 0.35)
    drone *= np.clip(t / 3.0, 0, 1) * np.clip((17.5 - t) / 1.5, 0, 1) * (1 + 0.15 * np.sin(2 * np.pi * t / 7))
    mus.add(0.0, drone.astype(np.float32), 0.08)
    mus.add(EV["star_tone"], I.glass_tone(Gs5, 8.5, 0.35, att=1.8, rel=3.0), 1.0, 0.25)

    # ---------------------------------------------------------------- M2 Last Morning (17–83), ~76 bpm
    beat = 60 / 76
    plan = [(17.0, "D"), (20.2, "Gmaj7"), (23.4, "D"), (26.5, "A"), (28.0, "D"), (31.2, "Bm"), (34.3, "G"),
            (37.0, "D"), (40.2, "A"), (41.2, "Gmaj7"), (44.2, "D"), (47.3, "A"), (49.0, "D"), (52.2, "G"),
            (55.3, "A"), (59.0, "D"), (62.2, "Bm"), (64.6, "G"), (67.0, "D"), (70.0, "A"), (72.0, "D"),
            (75.2, "G"), (78.4, "Bm"), (81.3, "G"), (82.6, "D")]
    for i, (tt, c) in enumerate(plan):
        te = plan[i + 1][0] if i + 1 < len(plan) else 85.0
        if 49.0 <= tt < 59.0:
            continue
        for j, m in enumerate(CH[c]):          # warm felt-piano chord, soft
            mus.add(human(tt, i * 7 + j, 0.02), I.piano(m, 0.32, min(5.0, te - tt + 1.5), felt=0.85, seed=i * 10 + j),
                    0.9, -0.2 + 0.13 * j)
        if not (41.2 <= tt < 44.2):
            arpeggio(mus, tt + beat, te, CH[c], beat / 2, "harp", 0.22, 0.35, seed=i * 31)
    mus.add(17.0, I.bowed(D2, 11, 0.35, att=2.5, rel=2.5, tasto=0.8, cello=True, seed=1), 1.0, -0.3)
    mus.add(EV["sun_crest"] - 0.3, I.strings([D4, A4, Fs5], 5.5, 0.18, att=1.8, rel=2.5, seed=3), 1.0, 0.0)
    # Wisp wakes: his motif; Old Horn revealed: hers
    mus.add(EV["wisp_wake_tuft"] + 0.25, I.celesta(A5, 0.45, 2.5), 1.0, 0.3)
    mus.add(EV["wisp_wake_tuft"] + 0.45, I.celesta(D6, 0.45, 3.0), 1.0, 0.3)
    mus.add(35.2, I.bowed(D2, 1.6, 0.5, att=0.4, rel=0.6, tasto=0.7, cello=True, seed=5), 1.0, -0.25)
    mus.add(36.6, I.bowed(A2, 3.0, 0.5, att=0.4, rel=1.5, tasto=0.7, cello=True, seed=6), 1.0, -0.25)
    mus.add(38.9, I.bowed(D2, 1.8, 0.55, att=0.5, rel=0.6, tasto=0.7, cello=True, seed=7), 1.0, -0.25)
    mus.add(40.5, I.bowed(A2, 3.4, 0.55, att=0.4, rel=1.8, tasto=0.7, cello=True, seed=8), 1.0, -0.25)
    mus.add(41.2, I.strings([A4, E5, A5], 3.2, 0.14, att=0.8, rel=1.2, tasto=0.9, seed=9), 1.0, 0.0)   # POV haze
    for k, tt in enumerate(np.arange(41.4, 44.0, 0.2)):
        mus.add(tt, I.harp([A5, E5, Fs5, D6][k % 4], 0.12, 2.0, seed=90 + k), 1.0, 0.4 * math.sin(k))
    # S6: playful pizzicato
    pat = [D3, Fs3, A3, Fs3, D4, A3, Fs3, A3]
    for k, tt in enumerate(np.arange(49.0, 58.8, beat / 2)):
        ch = "D" if tt < 52.2 else "G" if tt < 55.3 else "A"
        root = {"D": 0, "G": 5, "A": 7}[ch]
        m = pat[k % len(pat)] + root - (12 if root > 4 else 0)
        mus.add(human(tt, k, 0.012, 3), I.pizz(m, 0.5 + 0.2 * (k % 2 == 0), 1.0, seed=k), 1.0, -0.3 + 0.6 * (k % 2))
    mus.add(EV["pounce"], I.celesta(D6, 0.35, 1.5), 1.0, 0.3)
    mus.add(EV["burrow_dive"], I.celesta(A5, 0.3, 1.5), 1.0, -0.2)
    mus.add(EV["burrow_dive"] + 0.12, I.celesta(Fs5, 0.3, 1.5), 1.0, -0.2)
    # S7: wonder sparkle, then the first fragment of TOGETHER on celesta
    for k, m in enumerate([A5, D6, Fs5 + 12, A5 + 12]):
        mus.add(EV["pebble_glint"] + 0.08 * k, I.celesta(m, 0.22, 2.0), 1.0, 0.4)
    for k, (b, m, d) in enumerate(TOGETHER[:6]):
        mus.add(human(67.0 + b * 0.55, k, 0.01), I.celesta(m, 0.42, 2.5), 1.0, 0.2)
    # S8: warm cadence; the star planted as the faintest G#6
    mus.add(72.0, I.strings([D3, A3, Fs4, D5], 11.0, 0.16, att=2.5, rel=2.5, seed=11), 1.0, 0.0)
    mus.add(78.8, I.glass_tone(Gs5 + 12, 4.5, 0.06, att=1.5, rel=2.0), 1.0, 0.5)

    # ---------------------------------------------------------------- M3 Fern Dark (83–136)
    mus.add(83.0, I.strings([A5, E5 + 12], 7.5, 0.10, att=1.5, rel=1.0, tasto=0.0, seed=13), 1.0, 0.0)
    for k, tt in enumerate(np.arange(90.0, 97.25, 60 / 140 / 2)):
        m = [D4, A4, E4, A4, F4, A4, E4, A4][k % 8] + (12 if tt > 94.5 else 0)
        mus.add(human(tt, k, 0.006, 5), I.pizz(m, 0.35 + 0.15 * (tt - 90) / 7, 0.6, seed=k + 200), 1.0,
                -0.4 + 0.8 * ((k * 0.37) % 1))
    mus.add(EV["dragonfly_catch"], I.celesta(D6, 0.35, 1.2), 1.0, 0.2)
    # the hunter: col legno ticks, a low cluster growing, drum pulses on the booms
    rng = np.random.default_rng(7)
    for tt in np.sort(rng.uniform(101.0, 110.0, 26)):
        click = I.hp(rng.standard_normal(int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / 150.0), 1500)
        mus.add(tt, (click * 0.08).astype(np.float32), 1.0, rng.uniform(-0.7, 0.7))
    cl = np.linspace(0.1, 1.0, 50) ** 2
    mus.add(101.0, I.strings([Cs3 - 12, D2, Ds, E2], 10.0, 0.30, att=3.0, rel=0.8, cresc=cl, tasto=0.0, seed=17), 1.0, 0.0)
    for tt in EV["rex_boom"]:
        mus.add(tt, drum(0.9), 1.0, 0.0)
    # Old Horn's motif turns defiant in the low brass; drums on every rex step
    for k, (tt, m, d) in enumerate([(111.2, D2, 1.3), (112.5, A2, 2.2), (115.0, D2, 1.1), (116.1, A2, 1.9),
                                    (119.0, D2, 1.1), (120.1, A2, 2.6)]):
        mus.add(tt, I.brass(m, d, 0.85, att=0.08, rel=0.4, seed=k), 1.0, -0.15)
        mus.add(tt, I.brass(m + 12, d, 0.5, att=0.1, rel=0.4, seed=k + 9), 1.0, 0.15)
    for tt in EV["rex_steps"]:
        mus.add(tt, drum(0.7), 1.0, 0.0)
    trem = np.clip(np.linspace(0.3, 1.0, 40), 0, 1)
    mus.add(110.5, I.strings([D3, Ds, A3], 12.8, 0.18, att=0.6, rel=1.0, cresc=trem, seed=19), 1.0, 0.0)
    # release to solo cello (hers), then the soft reprise walking home
    mus.add(124.6, I.bowed(D3, 2.2, 0.45, att=0.5, rel=0.8, tasto=0.6, cello=True, seed=21), 1.0, -0.2)
    mus.add(126.6, I.bowed(A3, 3.6, 0.42, att=0.6, rel=1.8, tasto=0.6, cello=True, seed=22), 1.0, -0.2)
    mus.add(130.0, I.strings([D3, A3, Fs4, A4], 6.5, 0.26, att=1.5, rel=2.0, seed=23), 1.0, 0.0)
    mus.add(130.0, I.bowed(D2, 6.0, 0.35, att=1.2, rel=2.0, tasto=0.7, cello=True, seed=24), 1.0, -0.3)
    for k, (b, m, d) in enumerate(TOGETHER[:6]):
        mus.add(human(130.4 + b * 0.8, k, 0.01, 2), I.harp(m, 0.3, 3.0, seed=300 + k), 1.0, 0.25)

    # ---------------------------------------------------------------- M4 Counting Stars (136–173)
    mus.add(136.0, I.strings([D3, A3, Fs4, A4], 10.0, 0.22, att=2.5, rel=2.0, tasto=0.6, seed=25), 1.0, 0.0)
    mus.add(136.0, I.bowed(D2, 9.5, 0.4, att=2.0, rel=2.5, tasto=0.8, cello=True, seed=26), 1.0, -0.3)
    arpeggio(mus, 136.4, 144.5, CH["Dadd9"], 60 / 60, "harp", 0.2, 0.3, seed=777)
    mus.add(139.5, I.glass_tone(Gs5, 6.5, 0.16, att=2.5, rel=2.0), 1.0, 0.4)     # the star, recognised
    mus.add(141.8, I.celesta(A5, 0.3, 2.0), 1.0, 0.3)
    mus.add(142.0, I.celesta(D6, 0.3, 2.5), 1.0, 0.3)
    for k, (c, h) in enumerate(TL.DUET):
        mus.add(c, I.celesta(A5, 0.4, 1.6), 1.0, 0.3)
        mus.add(h, I.bowed(D3, 0.8, 0.45, att=0.08, rel=0.4, tasto=0.5, cello=True, seed=30 + k), 1.0, -0.3)
    for k, tt in enumerate(np.arange(149.73, 153.5, TL.DUET_BEAT)):
        mus.add(human(tt, k, 0.01), I.piano([D4, A4, Fs4, A4][k % 4], 0.3, 2.5, seed=400 + k), 1.0, 0.0)
    mus.add(151.4, I.strings([D4, Fs4, A4], 4.0, 0.12, att=1.2, rel=1.5, seed=27), 1.0, 0.0)
    mus.add(TL.NEW_STAR_TRILL, I.glass_tone(Gs5, 5.5, 0.28, att=0.3, rel=2.0), 1.0, 0.35)   # the star enters the harmony
    mus.add(TL.NEW_STAR_TRILL, I.strings([D4, A4, Gs5 - 12], 4.5, 0.12, att=0.4, rel=1.5, seed=29), 1.0, 0.0)
    for k, (tt, m) in enumerate([(156.2, Fs4), (157.8, E4), (159.0, D4)]):
        mus.add(tt, I.piano(m, 0.25, 2.5, seed=500 + k), 1.0, 0.0)
    # S17: the full TOGETHER theme — the warmest music of the film (3/4, 84 bpm)
    b = 60 / 84
    t0 = 160.3
    for k, (bb, m, d) in enumerate(TOGETHER + TOGETHER_B):
        tt = human(t0 + bb * b, k, 0.012, 4)
        mus.add(tt, I.piano(m, 0.46, d * b + 2.5, felt=0.6, seed=600 + k), 1.0, 0.1)
        mus.add(tt, I.celesta(m + 12, 0.18, d * b + 1.5), 1.0, 0.3)
    harm = ["D", "Bm", "G", "A", "D", "A", "D"]
    for k, c in enumerate(harm):
        tb = t0 + k * 3 * b
        root = CH[c][0]
        mus.add(human(tb, k, 0.01), I.harp(root - 12 if root > 45 else root, 0.35, 3.0, seed=700 + k), 1.0, -0.2)
        for j in (1, 2):
            for q, m in enumerate(CH[c][1:3]):
                mus.add(human(tb + j * b, k * 3 + j + q, 0.01), I.harp(m + 12, 0.18, 2.0, seed=720 + k * 5 + j + q), 1.0, 0.3)
    mus.add(t0, I.strings([D3, A3, D4, Fs4, A4], 13.5, 0.2, att=3.0, rel=3.0, seed=31,
                          cresc=np.r_[np.linspace(0.4, 1.0, 30), np.linspace(1.0, 0.7, 20)]), 1.0, 0.0)
    mus.add(t0 + 2 * b, I.bowed(A2, 4 * b, 0.35, att=0.6, rel=0.8, tasto=0.5, cello=True, seed=33), 1.0, -0.3)
    mus.add(t0 + 6 * b, I.bowed(D3, 6 * b, 0.35, att=0.6, rel=2.0, tasto=0.5, cello=True, seed=34), 1.0, -0.3)

    # ---------------------------------------------------------------- M5 Second Sun (173–225)
    # S18: silence. S19: the pure tone + her breath, then a choir blooming with wonder.
    mus.add(180.0, I.glass_tone(Gs5, 11.8, 0.30, att=0.8, rel=0.25, shimmer=0.1), 1.0, 0.0)
    bloom = np.r_[np.linspace(0.0, 1.0, 40) ** 1.5, np.ones(10)]
    mus.add(184.0, I.choir([D3, A3, E4, Fs4, Gs4, Cs5], 7.8, 0.9, att=2.5, rel=0.25, cresc=bloom, seed=35), 1.0, 0.0)
    mus.add(184.5, I.strings([D4, A4, E5, Gs5], 7.3, 0.14, att=3.0, rel=0.25, seed=36), 1.0, 0.0)
    # (seismic hit is sound design; the music drops out at 191.8)
    # S21: the tragic chorale — TOGETHER in D minor, augmented, over falling brass
    chorale = [(0, D5, 2), (2, C5, 2), (4, A4, 2), (6, Bb4, 2), (8, A4, 2), (10, F4, 2), (12, G4, 1.5), (13.5, F4, 1.5),
               (15, E4, 1.0)]
    for k, (bb, m, d) in enumerate(chorale):
        tt = 199.4 + bb
        mus.add(tt, I.choir([m, m - 12], d + 0.6, 0.9, att=0.35, rel=0.6, seed=40 + k), 1.0, 0.0)
        mus.add(tt, I.bowed(m, d + 0.5, 0.35, att=0.3, rel=0.5, seed=60 + k, voices=4, detune=10), 1.0, 0.2)
    for k, (tt, c) in enumerate([(199.4, "Dm"), (203.4, "Bb"), (207.4, "Gm"), (211.4, "A7")]):
        mus.add(tt, I.strings(CH[c], 4.4, 0.28, att=0.6, rel=0.8, tasto=0.0, seed=70 + k), 1.0, 0.0)
        mus.add(tt, I.choir(CH[c][:3], 4.4, 0.6, att=0.6, rel=0.8, vowel="oo", seed=80 + k), 1.0, 0.0)
    for k, (tt, m) in enumerate([(199.4, D3), (203.4, C3), (207.4, Bb2), (211.4, A2)]):
        mus.add(tt, I.brass(m, 4.2, 0.7, att=0.25, rel=0.6, seed=90 + k), 1.0, -0.1)
        mus.add(tt + 2.0, I.brass(m - 2, 2.2, 0.5, att=0.2, rel=0.5, seed=95 + k), 1.0, 0.1)
    for k, tt in enumerate(np.arange(199.4, 215.0, 1.0)):
        mus.add(tt, drum(0.45), 1.0, 0.0)
    # S22: one cello note (her hum), one celesta note (his chirp), a swell, then digital silence at 3:45
    mus.add(EV["final_hum"], I.bowed(D3, 1.6, 0.5, att=0.2, rel=0.6, tasto=0.6, cello=True, seed=101), 1.0, -0.2)
    mus.add(EV["final_chirp"], I.celesta(A5, 0.5, 2.0), 1.0, 0.25)
    mus.add(EV["final_hum2"], I.bowed(D3, 3.4, 0.5, att=0.2, rel=0.3, tasto=0.6, cello=True, seed=102), 1.0, -0.2)
    sw = np.linspace(0.0, 1.0, 50) ** 2.2
    mus.add(222.0, I.strings([D3, A3, D4, Fs4, A4, D5], 3.0, 0.45, att=0.05, rel=0.001, cresc=sw, seed=103), 1.0, 0.0)
    mus.add(222.0, I.choir([D4, Fs4, A4, D5], 3.0, 0.9, att=0.05, rel=0.001, cresc=sw, seed=104), 1.0, 0.0)

    # ---------------------------------------------------------------- M6 Ash (225–254)
    mus.add(231.0, I.bowed(D2, 22.5, 0.35, att=4.0, rel=5.0, tasto=0.9, cello=True, seed=110), 1.0, 0.0)
    mus.add(EV["life_note"], I.celesta(Fs5 + 12, 0.14, 3.0, bright=0.5), 1.0, 0.1)

    # ---------------------------------------------------------------- M7 What the Stone Remembers (254–309)
    bb = 1.0
    phrase_minor = [(0, D5, 1), (1, C5, 1), (2, A4, 1), (3, Bb4, 1), (4, A4, 1), (5, F4, 1), (6, G4, 1), (7, F4, 1),
                    (8, E4, 1), (9, D4, 3),
                    (12, F4, 1), (13, A4, 1), (14, D5, 1), (15, C5, 1), (16, A4, 1), (17, F4, 1), (18, G4, 1),
                    (19, A4, 1), (20, Bb4, 1), (21, A4, 3),
                    (24, D5, 1), (25, C5, 1), (26, A4, 1), (27, Bb4, 1), (28, A4, 1), (29, G4, 1), (30, F4, 1),
                    (31, E4, 1), (32, Cs4, 1), (33, D4, 3)]
    t0 = 255.0
    for k, (b0, m, d) in enumerate(phrase_minor):
        tt = human(t0 + b0 * bb * 1.08, k, 0.02, 7)
        mus.add(tt, I.piano(m, 0.40, d * 1.08 + 3.0, felt=0.75, seed=800 + k), 1.0, 0.1)
    left = [(0, "Dm"), (3, "Bb"), (6, "Gm"), (9, "Dm"), (12, "Dm"), (15, "F" if False else "Bb"), (18, "Gm"),
            (21, "A"), (24, "Dm"), (27, "Bb"), (30, "Gm"), (32, "A7"), (33, "Dm")]
    for k, (b0, c) in enumerate(left):
        tt = human(t0 + b0 * 1.08, k, 0.02, 9)
        root = CH[c][0]
        mus.add(tt, I.piano(root - 12 if root > 44 else root, 0.28, 4.0, felt=0.85, seed=900 + k), 1.0, -0.25)
        mus.add(tt + 1.08, I.piano(CH[c][1] + 12, 0.18, 3.0, felt=0.85, seed=950 + k), 1.0, -0.1)
    # museum: Bb -> Gm -> A -> (the child takes her hand) D MAJOR, soft strings join
    for k, (tt, c) in enumerate([(291.4, "Bb"), (293.6, "Gm"), (295.8, "Asus"), (296.9, "A7"), (EV["hand_take"], "D")]):
        for j, m in enumerate(CH[c]):
            mus.add(human(tt, k * 5 + j, 0.02), I.piano(m, 0.30 + 0.06 * (c == "D"), 4.0 if c != "D" else 7.0,
                                                        felt=0.8, seed=1000 + k * 7 + j), 1.0, -0.2 + 0.13 * j)
    th = EV["hand_take"]
    for k, (b0, m, d) in enumerate(TOGETHER[:9]):
        mus.add(human(th + 0.6 + b0 * 0.85, k, 0.015), I.piano(m, 0.38, d * 0.85 + 2.5, felt=0.7, seed=1100 + k), 1.0, 0.1)
    mus.add(th, I.strings([D3, A3, D4, Fs4], 9.5, 0.14, att=2.5, rel=3.0, seed=120), 1.0, 0.0)
    mus.add(th + 0.6 + 9 * 0.85, I.piano(D4, 0.3, 5.0, felt=0.8, seed=1200), 1.0, 0.0)
    # the last sound: his chirp note answered by her hum note
    mus.add(EV["end_chirp"], I.celesta(A5, 0.32, 2.0), 1.0, 0.25)
    mus.add(EV["end_hum"], I.bowed(D3, 1.2, 0.4, att=0.12, rel=0.6, tasto=0.7, cello=True, seed=130), 1.0, -0.25)
    return mus


def drum(vel=0.7):
    """Low membrane pulse (timpani-ish), felt in the chest."""
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    f = 52 * (1 + 0.4 * np.exp(-t / 0.05))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.45) + 0.35 * np.sin(1.6 * ph) * np.exp(-t / 0.2)
    x += I.lp(np.random.default_rng(3).standard_normal(n), 300) * np.exp(-t / 0.03) * 0.3
    return (x * vel * 0.35 * np.clip(t / 0.003, 0, 1)).astype(np.float32)


if __name__ == "__main__":
    import time
    t0 = time.time()
    m = build()
    out = os.path.join(HERE, "..", "build")
    os.makedirs(out, exist_ok=True)
    np.save(os.path.join(out, "music_dry.npy"), m.st())
    print(f"score built in {time.time() - t0:.0f}s, peak {np.abs(m.st()).max():.3f}")
