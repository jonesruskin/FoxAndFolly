"""Facing East — original score, synthesised entirely in code.

Tempo 60 BPM, so one beat = one second and every cue lines up with the
timeline in story.py. Key: D major / B minor.

Leitmotifs
  SUN   rising  D-E-F#-A   (Hesper following the light)
  NIGHT falling A-F#-E-D   (the secret turn back east)

    python music.py            -> build/music.wav (mastered, -14 LUFS)
"""
import os
import sys

import numpy as np
import pyloudnorm as pyln
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared"))
from foxfolly.audio import (SR, Buffer, additive_tone, automation, bell,  # noqa: E402
                            convolve_reverb, db, env_asr, limiter, midi_hz,
                            noise_band, reverb_ir, true_peak)

import story  # noqa: E402

DUR = story.DURATION
BUILD = os.path.join(HERE, "..", "build")

CH = {  # pad voicings (MIDI)
    "Bm9": [47, 54, 57, 61, 62], "Gmaj7": [43, 50, 54, 59], "Dadd9": [50, 57, 64, 66],
    "Asus4": [45, 50, 52, 57], "Em7": [40, 47, 50, 55], "D/F#": [42, 45, 50, 57],
    "A": [45, 52, 57, 61], "Bm": [47, 50, 54, 59], "G": [43, 50, 55, 59], "D": [50, 54, 57, 62],
}

PROGRESSION = [  # (start, end, chord)
    (0, 8, "Bm9"), (8, 16, "Gmaj7"), (16, 22, "Asus4"),
    (22, 30, "D"), (30, 34, "G"), (34, 38, "D/F#"), (38, 42, "Em7"), (42, 46, "A"),
    (46, 50, "D"), (50, 54, "G"), (54, 58, "Bm"), (58, 62, "G"),
    (62, 70, "Em7"), (70, 78, "Bm"), (78, 86, "G"), (86, 92, "Asus4"), (92, 97, "A"),
    (97, 101, "D"), (101, 105, "G"), (105, 109, "Em7"), (109, 113, "A"),
    (113, 121, "Dadd9"), (121, 125, "Gmaj7"), (125, 131, "Asus4"), (131, 136, "Bm"),
    (136, 144, "G"), (144, 152, "Em7"), (152, 164, "Bm"), (164, 172, "Gmaj7"),
    (172, 177, "Asus4"),
    (177, 182, "Asus4"), (182, 186, "A"), (186, 194, "Dadd9"), (194, 198, "G"),
    (198, 202, "D/F#"), (202, 206, "Em7"), (206, 210, "A"), (210, 214, "D"),
    (214, 218, "G"), (218, 222, "D/F#"), (222, 226, "Em7"), (226, 230, "D"),
    (230, 234, "Gmaj7"), (234, 238, "A"),
    (238, 246, "Bm9"), (246, 254, "Gmaj7"), (254, 262, "D"), (262, 266, "Asus4"),
    (266, DUR, "Dadd9"),
]

SUN = [(0, 74, 0.5), (0.5, 76, 0.5), (1.0, 78, 0.5), (1.5, 81, 2.5)]
NIGHT = [(0, 81, 0.6), (0.6, 78, 0.6), (1.2, 76, 0.6), (1.8, 74, 2.5)]


def motif(buf, start, notes, transpose=0, vel=0.35, stretch=1.0, pan=0.15, octave_double=False):
    for off, m, d in notes:
        f = midi_hz(m + transpose)
        buf.add(start + off * stretch, bell(f, dur=d * stretch + 3.0, vel=vel), pan=pan)
        if octave_double:
            buf.add(start + off * stretch, bell(f * 2, dur=d * stretch + 2.5, vel=vel * 0.45),
                    pan=-pan)


def chord_tones(t):
    for s, e, c in PROGRESSION:
        if s <= t < e:
            return CH[c]
    return CH["Dadd9"]


def build():
    rng = np.random.default_rng(2026)
    pad = Buffer(DUR + 1)
    strings = Buffer(DUR + 1)
    keys = Buffer(DUR + 1)
    low = Buffer(DUR + 1)
    tex = Buffer(DUR + 1)

    # ---------------------------------------------------------------- pads
    for i, (s, e, c) in enumerate(PROGRESSION):
        dur = (e - s) + 3.0
        bright = 1.9 if (113 <= s < 125 or 186 <= s < 202) else 2.2
        for j, m in enumerate(CH[c]):
            tone = additive_tone(midi_hz(m), dur, harmonics=9, tilt=bright,
                                 detune_cents=(-7, 0, 6), attack=1.8, release=3.0,
                                 seed=i * 10 + j)
            pad.add(s - 0.6, tone, gain=0.10, pan=(j / max(1, len(CH[c]) - 1) - 0.5) * 0.9)

    # ------------------------------------------------------------- strings
    # swells at the bloom (113-125) and the dawn (182-214), gentler elsewhere
    for s, e, c in PROGRESSION:
        if not (100 <= s < 136 or 177 <= s < 238 or s >= 262):
            continue
        dur = (e - s) + 2.5
        voicing = [m + 12 for m in CH[c][1:]] + [CH[c][0] + 24]
        for j, m in enumerate(voicing):
            tone = additive_tone(midi_hz(m), dur, harmonics=14, tilt=1.25,
                                 detune_cents=(-9, -3, 3, 9), vib=0.004, vib_rate=5.2,
                                 attack=2.2, release=2.5, seed=500 + int(s) * 7 + j)
            strings.add(s - 0.8, tone, gain=0.06, pan=(j / len(voicing) - 0.5) * 1.2)

    # ------------------------------------------------------ keys: motifs
    motif(keys, 3.2, NIGHT, transpose=-12, vel=0.26)
    motif(keys, 11.3, NIGHT, transpose=-12, vel=0.22, stretch=1.3)
    motif(keys, 26.0, SUN, vel=0.33)
    motif(keys, 46.0, SUN, vel=0.30, octave_double=True)
    motif(keys, 55.0, NIGHT, transpose=-12, vel=0.25, stretch=1.2)
    motif(keys, 64.2, SUN[:3], transpose=-12, vel=0.24, stretch=1.4)   # unfinished
    motif(keys, 81.0, [(0, 71, 1.0), (1.0, 69, 2.5)], vel=0.22)       # doubt
    motif(keys, 88.0, SUN, vel=0.32, stretch=0.9)                     # the promise
    motif(keys, 115.0, SUN, vel=0.40, stretch=1.2, octave_double=True)  # bloom
    motif(keys, 124.5, NIGHT, transpose=-24, vel=0.22, stretch=1.6)   # can't turn
    motif(keys, 139.0, [(0, 81, 1.5), (1.5, 78, 1.5), (3.0, 76, 1.5), (4.5, 74, 4)],
          vel=0.24, stretch=1.1)
    for tt, m in ((147.5, 71), (152.5, 66), (160.2, 59), (168.0, 62)):
        keys.add(tt, bell(midi_hz(m), 5.0, vel=0.2), pan=0.1)
    # heartbeat before the dawn
    for k, tt in enumerate(np.arange(179.0, 186.0, 1.0)):
        keys.add(tt, bell(midi_hz(62), 2.5, vel=0.10 + 0.03 * k), pan=0.0)
    motif(keys, 186.0, SUN, vel=0.45, octave_double=True)
    motif(keys, 190.0, [(0, 81, 0.5), (0.5, 83, 0.5), (1.0, 85, 0.5), (1.5, 86, 3.0)],
          vel=0.40, octave_double=True)
    motif(keys, 205.5, SUN, vel=0.28, stretch=1.2)
    motif(keys, 216.0, SUN, vel=0.28, stretch=1.5)
    motif(keys, 223.0, SUN, transpose=12, vel=0.18, stretch=1.5)
    keys.add(230.0, bell(midi_hz(74), 6, vel=0.26))
    motif(keys, 240.0, NIGHT, vel=0.2, stretch=1.6)
    motif(keys, 255.5, SUN, vel=0.22, stretch=1.6)
    motif(keys, 268.0, SUN, transpose=12, vel=0.20, stretch=1.8)

    # --------------------------------------- arpeggiated time-lapse pulse
    def arps(t0, t1, step0, step1, vel, octave=12):
        tt = t0
        k = 0
        while tt < t1:
            u = (tt - t0) / (t1 - t0)
            tones = chord_tones(tt)
            m = tones[(k * 2 + k // 3) % len(tones)] + octave
            env = np.sin(np.pi * u) ** 0.6
            keys.add(tt, bell(midi_hz(m), 1.8, vel=vel * env, bright=0.6),
                     pan=0.35 * np.sin(k * 1.3))
            tt += step0 + (step1 - step0) * u
            k += 1
    arps(30.0, 54.0, 0.5, 0.5, 0.11)
    arps(97.0, 114.0, 0.5, 0.25, 0.15)
    arps(198.0, 214.0, 0.5, 0.5, 0.12, octave=24)

    # ------------------------------------------------------- low + texture
    t = np.arange(int((DUR + 1) * SR)) / SR
    drone = (np.sin(2 * np.pi * midi_hz(38) * t) * 0.6 + np.sin(2 * np.pi * midi_hz(45) * t) * 0.25)
    drone *= 1 + 0.25 * np.sin(2 * np.pi * t / 11.0)
    low.add(0, drone.astype(np.float32), gain=0.04)
    # soft "sunrise" swells (sub + noise whoosh) at the two big moments
    for tt, g in ((114.2, 0.8), (185.2, 1.0)):
        n = int(4 * SR)
        tb = np.arange(n) / SR
        boom = np.sin(2 * np.pi * (48 - 8 * tb) * tb) * np.exp(-tb / 1.3) * np.clip(tb / 0.05, 0, 1)
        low.add(tt, boom.astype(np.float32), gain=0.18 * g)
        wh = noise_band(3.0, 300, 3000, seed=int(tt)) * env_asr(int(3 * SR), 2.4, 0.6)
        tex.add(tt - 2.2, wh, gain=0.03 * g)
    # wind through the field: always present, softly breathing
    wind = noise_band(DUR + 1, 180, 1400, seed=9)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * t / 9.0) * np.sin(2 * np.pi * t / 23.0 + 1)
    tex.add(0, (wind * lfo).astype(np.float32), gain=0.012, pan=-0.3)
    wind2 = noise_band(DUR + 1, 220, 1600, seed=10)
    tex.add(0, (wind2 * (1 - lfo)).astype(np.float32), gain=0.012, pan=0.3)
    # night sparkles (stars)
    for lo_t, hi_t in ((0, 21), (58, 64), (150, 178)):
        for tt in np.sort(rng.uniform(lo_t, hi_t, int((hi_t - lo_t) * 0.6))):
            m = int(rng.choice([86, 88, 90, 93, 95]))
            tex.add(tt, bell(midi_hz(m), 2.5, vel=0.05, bright=0.3), pan=rng.uniform(-0.8, 0.8))

    # ------------------------------------------------------------- mix bus
    stems = {"pad": pad, "strings": strings, "keys": keys, "low": low, "tex": tex}
    mix = sum(b.stereo() for b in stems.values())
    ir = reverb_ir(4.5, decay=1.5)
    send = pad.stereo() * 0.5 + strings.stereo() * 0.7 + keys.stereo() * 0.9 + tex.stereo() * 0.6
    wet = convolve_reverb(send, ir)
    mix = mix * 0.75 + wet * 0.55

    # emotional arc automation (dB)
    arc = automation([
        (0, -13), (16, -11), (22, -6), (40, -5), (54, -4.5), (62, -6), (97, -5), (110, -3), (118, 1.5),
        (123, 1.0), (130, -4), (150, -9), (160, -12), (176, -9), (186, -1), (192, 1.0), (205, -1),
        (220, -4), (240, -6), (262, -6), (DUR + 1, -8),
    ], len(mix))
    mix = mix * arc[:, None]
    # gentle tone shaping: clean the mud, soften the top
    sos_hp = signal.butter(3, 45, "high", fs=SR, output="sos")
    sos_lp = signal.butter(4, 10000, "low", fs=SR, output="sos")
    mix = signal.sosfilt(sos_lp, signal.sosfilt(sos_hp, mix, axis=0), axis=0)
    mix = mix[: int(DUR * SR)]
    # fade in / out
    n = len(mix)
    fade = np.ones(n, np.float32)
    fi, fo = int(2.5 * SR), int(6.0 * SR)
    fade[:fi] = np.linspace(0, 1, fi) ** 2
    fade[-fo:] = np.linspace(1, 0, fo) ** 2
    mix = (mix * fade[:, None]).astype(np.float32)
    return mix


def master(mix, target_lufs=-14.0, ceiling=-1.5):
    meter = pyln.Meter(SR)
    for _ in range(3):
        lufs = meter.integrated_loudness(mix)
        mix = mix * db(target_lufs - lufs)
        mix = limiter(mix, ceiling_db=ceiling)
    return mix, meter.integrated_loudness(mix), true_peak(mix)


def main():
    os.makedirs(BUILD, exist_ok=True)
    mix = build()
    mix, lufs, tp = master(mix)
    print(f"integrated {lufs:.2f} LUFS, true peak {tp:.2f} dBTP, "
          f"duration {len(mix) / SR:.2f}s")
    out = os.path.join(BUILD, "music.wav")
    wavfile.write(out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print(out)


if __name__ == "__main__":
    main()
