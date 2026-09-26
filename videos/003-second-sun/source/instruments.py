"""Synthesised instruments for SECOND SUN (no samples, no soundfonts).

Every voice returns a mono float32 array at 48 kHz. Designed to sound like
real instruments in a real room once the convolution hall is applied:
inharmonic piano partials with hammer noise, Karplus-Strong plucks,
bowed strings with body-resonance filtering and vibrato, formant choir.
"""
import math

import numpy as np
from scipy import signal

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _env(n, a, r, curve=2.0):
    e = np.ones(n, np.float32)
    ai = min(n // 2, max(1, int(a * SR)))
    ri = min(n - ai, max(1, int(r * SR)))
    e[:ai] = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, ai))) ** (curve / 2)
    e[n - ri:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, ri))) ** (curve / 2)
    return e


def _peak(x, f, q, gain_db):
    b, a = signal.iirpeak(f / (SR / 2), q)
    y = signal.lfilter(b, a, x)
    return x + (10 ** (gain_db / 20) - 1) * y


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, min(f, SR * 0.45), "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- piano
def piano(m, vel=0.6, dur=4.0, felt=0.7, seed=0):
    """Felt piano: inharmonic partials (B), two-stage decay, soft hammer thump."""
    rng = np.random.default_rng(seed + int(m * 7))
    f0 = hz(m)
    t = _t(dur)
    B = 0.0004 * (f0 / 261.6) ** 0.5
    out = np.zeros_like(t)
    bright = (0.35 + 0.65 * vel) * (1.1 - felt)
    for k in range(1, 18):
        fk = f0 * k * math.sqrt(1 + B * k * k)
        if fk > SR * 0.42:
            break
        amp = (1 / k ** (1.3 + 1.2 * felt)) * (1 + bright * (k > 1) * 1.5)
        amp *= math.exp(-k * felt * 0.12)
        t1 = (2.2 + 4 * (261.6 / f0) ** 0.6) / (1 + 0.15 * k)
        t2 = t1 * 5
        dec = 0.6 * np.exp(-t / (t1 * 0.25)) + 0.4 * np.exp(-t / t2)
        det = 1 + (rng.random() - 0.5) * 0.0006
        out += amp * dec * (np.sin(2 * np.pi * fk * det * t + rng.random() * 6.28) +
                            0.5 * np.sin(2 * np.pi * fk * (2 - det) * t))
    thump = lp(rng.standard_normal(len(t)) * np.exp(-t / 0.012), 900 + 1500 * vel) * 0.25 * vel
    out = out * vel * _env(len(t), 0.002, min(0.8, dur * 0.3)) + thump
    return (out * 0.18).astype(np.float32)


# ------------------------------------------------------- plucks (harp, pizz)
def pluck(m, vel=0.6, dur=3.0, bright=0.5, decay=0.996, seed=0):
    """Karplus-Strong string via an IIR comb (vectorised with lfilter)."""
    rng = np.random.default_rng(seed + int(m * 13))
    f0 = hz(m)
    Lf = SR / f0
    L = int(Lf)
    n = int(dur * SR)
    exc = np.zeros(n)
    burst = rng.standard_normal(L)
    burst = lp(burst, 800 + 7000 * bright)
    exc[:L] = burst * vel
    g = decay ** (440.0 / f0) ** 0.3
    a = np.zeros(L + 2)
    a[0] = 1.0
    a[L] = -g * 0.5
    a[L + 1] = -g * 0.5
    y = signal.lfilter([1.0], a, exc)
    y = lp(y, 1500 + 6000 * bright)
    return (y * 0.35 * _env(n, 0.001, 0.3)).astype(np.float32)


def harp(m, vel=0.5, dur=4.0, seed=0):
    return pluck(m, vel, dur, bright=0.45, decay=0.998, seed=seed)


def pizz(m, vel=0.6, dur=1.2, seed=0):
    y = pluck(m, vel, dur, bright=0.3, decay=0.985, seed=seed)
    return _body(y, cello=m < 55) * 1.3


# ----------------------------------------------------------- bowed strings
def _body(x, cello=False):
    """Wooden body resonances."""
    if cello:
        for f, q, g in ((110, 2.0, 5), (230, 3, 4), (540, 3, 2), (1400, 2, -3)):
            x = _peak(x, f, q, g)
    else:
        for f, q, g in ((280, 3, 4), (520, 3, 3), (1150, 2, 2), (2700, 2, -2)):
            x = _peak(x, f, q, g)
    return x


def bowed(m, dur, vel=0.5, att=0.35, rel=0.6, vib=0.005, tasto=0.0, cello=False, seed=0, voices=1, detune=6.0,
          cresc=None):
    """Bowed string: band-limited saw-like additive, vibrato fading in, bow noise, body EQ.
    tasto: 0..1 sul tasto (darker, fewer harmonics). cresc: optional envelope array (0..1)."""
    rng = np.random.default_rng(seed + int(m * 17))
    f0 = hz(m)
    t = _t(dur)
    n = len(t)
    out = np.zeros(n)
    for v in range(voices):
        dc = (v - (voices - 1) / 2) * detune / max(1, voices - 1) if voices > 1 else 0.0
        fv = f0 * 2 ** (dc / 1200)
        vr = 5.0 + 0.6 * rng.random()
        vdepth = vib * np.clip(t / 0.6, 0, 1)
        ph = 2 * np.pi * np.cumsum(fv * (1 + vdepth * np.sin(2 * np.pi * vr * t + rng.random() * 6))) / SR
        kmax = int(min(40, (SR * 0.42) / fv))
        tilt = 1.0 + 0.9 * tasto
        for k in range(1, kmax + 1):
            out += np.sin(k * ph + rng.random() * 6.28) / k ** tilt * (1 - 0.5 * tasto * (k > 4))
    out /= max(1, voices)
    noise = bp(rng.standard_normal(n), 1500, 6000) * 0.03 * (1 - 0.5 * tasto)
    out = out + noise
    out = _body(out, cello)
    env = _env(n, att, rel)
    if cresc is not None:
        env = env * np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(cresc)), cresc)
    return (out * env * vel * 0.12).astype(np.float32)


def strings(chord, dur, vel=0.4, att=1.2, rel=1.5, cresc=None, seed=0, tasto=0.2):
    out = np.zeros(int(dur * SR), np.float32)
    for i, m in enumerate(chord):
        out += bowed(m, dur, vel, att, rel, vib=0.004, tasto=tasto, cello=m < 50, seed=seed + i, voices=4,
                     detune=10, cresc=cresc)
    return out / math.sqrt(max(1, len(chord)))


# ------------------------------------------------------------------ choir
FORMANTS_AH = ((800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.25), (3900, 130, 0.12))
FORMANTS_OO = ((350, 60, 1.0), (600, 70, 0.4), (2400, 100, 0.1))


def choir(chord, dur, vel=0.4, att=1.5, rel=2.0, vowel="ah", seed=0, cresc=None):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    src = np.zeros(n)
    for i, m in enumerate(chord):
        for v in range(5):
            f = hz(m) * 2 ** ((rng.random() - 0.5) * 14 / 1200)
            vib = 1 + 0.006 * np.sin(2 * np.pi * (4.6 + rng.random()) * t + rng.random() * 6)
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            kmax = int(min(30, SR * 0.4 / f))
            for k in range(1, kmax + 1):
                src += np.sin(k * ph + rng.random() * 6) / k
    src += rng.standard_normal(n) * 0.2   # breath
    out = np.zeros(n)
    for f, bw, g in (FORMANTS_AH if vowel == "ah" else FORMANTS_OO):
        out += bp(src, f - bw, f + bw) * g
    env = _env(n, att, rel)
    if cresc is not None:
        env = env * np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(cresc)), cresc)
    return (out * env * vel * 0.05 / math.sqrt(len(chord))).astype(np.float32)


# ------------------------------------------------------------------ brass
def brass(m, dur, vel=0.6, att=0.12, rel=0.5, seed=0):
    rng = np.random.default_rng(seed + m)
    f0 = hz(m)
    t = _t(dur)
    n = len(t)
    ph = 2 * np.pi * np.cumsum(f0 * (1 + 0.003 * np.sin(2 * np.pi * 5 * t))) / SR
    bright = np.clip(t / (att * 3), 0, 1) * (0.5 + 0.5 * vel)
    out = np.zeros(n)
    for k in range(1, int(min(30, SR * 0.4 / f0)) + 1):
        out += np.sin(k * ph) / k * np.clip(bright * 12 / k, 0, 1)
    out = _peak(out, 1100, 2, 4)
    return (out * _env(n, att, rel) * vel * 0.15).astype(np.float32)


# ---------------------------------------------------------------- bells etc.
def celesta(m, vel=0.4, dur=3.0, bright=1.0):
    f = hz(m)
    t = _t(dur)
    out = np.zeros_like(t)
    tau = 1.3 * (440.0 / f) ** 0.3
    for r, a, dk in ((1.0, 1.0, 1.0), (2.0, 0.22 * bright, 2.2), (3.0, 0.1 * bright, 3.0), (4.1, 0.06, 4.5),
                     (0.5, 0.05, 1.2)):
        if f * r < SR * 0.45:
            out += a * np.sin(2 * np.pi * f * r * t + r) * np.exp(-t * dk / tau)
    out *= np.clip(t / 0.003, 0, 1)
    return (out * vel * 0.3 * _env(len(t), 0.0, min(0.5, dur * 0.3))).astype(np.float32)


def glass_tone(m, dur, vel=0.3, att=1.0, rel=1.5, shimmer=0.3):
    """The Star: a pure, glassy tone with a faint beating shimmer."""
    f = hz(m)
    t = _t(dur)
    out = np.sin(2 * np.pi * f * t) + 0.12 * np.sin(2 * np.pi * f * 2.001 * t) + 0.05 * np.sin(2 * np.pi * f * 3.003 * t)
    out *= 1 + shimmer * 0.25 * np.sin(2 * np.pi * 0.7 * t) * np.sin(2 * np.pi * 3.1 * t)
    return (out * _env(len(t), att, rel) * vel * 0.2).astype(np.float32)


# ----------------------------------------------------------------- voices
def hum(m=38, dur=2.0, vel=0.6, shaky=0.0, seed=0):
    """Old Horn's low closed-mouth hum: a nasal 'mmm' — voiced source, nasal formants, breath."""
    rng = np.random.default_rng(seed)
    t = _t(dur)
    n = len(t)
    f0 = hz(m) * (1 + 0.012 * np.sin(2 * np.pi * 4.2 * t) * shaky * 3 + 0.004 * np.sin(2 * np.pi * 5.1 * t))
    f0 = f0 * (1 + 0.03 * np.exp(-t / 0.15))          # slight scoop into the note
    ph = 2 * np.pi * np.cumsum(f0) / SR
    src = np.zeros(n)
    for k in range(1, 24):
        src += np.sin(k * ph) / k ** 1.1
    out = _peak(lp(src, 900), 250, 1.5, 9)
    out = _peak(out, 90, 1.2, 4)
    out += lp(rng.standard_normal(n), 400) * 0.04
    trem = 1 + shaky * 0.25 * np.sin(2 * np.pi * 7.5 * t + 1)
    return (out * _env(n, 0.18, 0.5) * trem * vel * 0.16).astype(np.float32)


def chirp(vel=0.6, notes=(81, 86), gap=0.11, dur=0.1, broken=0.0, seed=0):
    """Wisp's bright two-note call (A5 -> D6): bird-like FM glide with a trill."""
    rng = np.random.default_rng(seed)
    parts = []
    for i, m in enumerate(notes):
        t = _t(dur + 0.03)
        f = hz(m) * (1 + 0.06 * np.exp(-t / 0.02) * (1 if i else -1))
        if broken > 0:
            f = f * (1 + broken * 0.08 * np.sin(2 * np.pi * 23 * t) + broken * 0.1 * rng.random())
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph + 0.4 * np.sin(2 * ph)) * (1 + 0.3 * np.sin(2 * np.pi * 60 * t))
        s *= _env(len(t), 0.004, 0.05)
        parts.append(s)
    g = np.zeros(int(gap * SR))
    out = np.concatenate([parts[0], g[: max(0, len(g) - len(parts[0]))], parts[1]]) if len(notes) > 1 else parts[0]
    return (out * vel * 0.18).astype(np.float32)
