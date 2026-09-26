"""SECOND SUN — sound design, synthesised and frame-locked to picture events.

Footfalls are computed from the same gait functions that plant the feet in the
animation, so every thud lands on the frame where a foot touches down.
    python sfx.py -> build/sfx_dry.npy (stereo, pre-master)
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
from foxfolly.anim import Track, clamp, ease_in_out_sine  # noqa: E402
from music import Bus  # noqa: E402

SR = I.SR
EV = TL.EV
RNG = np.random.default_rng(2066)


def noise(dur, seed=None):
    r = RNG if seed is None else np.random.default_rng(seed)
    return r.standard_normal(int(dur * SR))


def env_exp(n, tau, att=0.002):
    t = np.arange(n) / SR
    return np.exp(-t / tau) * np.clip(t / att, 0, 1)


# ------------------------------------------------------------------ voices
def thud(weight=1.0, dur=0.9):
    """Footfall scaled to mass: low body + soil crunch."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = (70 - 30 * weight) * (1 + 0.5 * np.exp(-t / 0.03))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.12 + 0.18 * weight))
    crunch = I.bp(noise(dur), 150, 1800) * env_exp(n, 0.05 + 0.04 * weight) * 0.5
    return ((body * weight + crunch * (0.6 + 0.4 * weight)) * 0.5).astype(np.float32)


def tap(dur=0.08):
    n = int(dur * SR)
    return (I.bp(noise(dur), 900, 5000) * env_exp(n, 0.012) * 0.25).astype(np.float32)


def rustle(dur=0.8):
    n = int(dur * SR)
    x = I.bp(noise(dur), 1800, 9000) * (0.5 + 0.5 * np.abs(np.sin(np.arange(n) / SR * 2 * np.pi * 14)))
    return (x * I._env(n, 0.05, 0.25) * 0.18).astype(np.float32)


def squeak(f=3200, dur=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * (1 + 0.25 * np.sin(np.pi * t / dur))
    return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * I._env(n, 0.005, 0.04) * 0.08).astype(np.float32)


def click(dur=0.05, f=2500):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.008) + I.hp(noise(dur), 2000) * np.exp(-t / 0.004) * 0.5
    return (x * 0.2).astype(np.float32)


def boom(dur=3.5, vel=1.0):
    """The Hunter's closed-mouth infrasonic boom: 18-35 Hz felt more than heard, with audible chest harmonics."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 30 * (1 - 0.25 * t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.12 * np.sin(4 * ph)
    x += I.lp(noise(dur), 200) * 0.15
    return (x * I._env(n, 0.5, 1.4) * vel * 0.45).astype(np.float32)


def snort(dur=0.9):
    n = int(dur * SR)
    return (I.bp(noise(dur), 120, 900) * I._env(n, 0.25, 0.4) * 0.25).astype(np.float32)


def bellow(dur=1.6, f0=95, seed=0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    f = f0 * (1 + 0.08 * np.sin(np.pi * t / dur)) * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = sum(np.sin(k * ph) / k for k in range(1, 14))
    x = I._peak(I.lp(src, 1800), 420, 2, 6) + I.lp(r.standard_normal(n), 800) * 0.05
    return (x * I._env(n, 0.15, 0.6) * 0.12).astype(np.float32)


def breath(dur=3.4, vel=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    envl = np.sin(np.pi * np.clip(t / (dur * 0.42), 0, 1)) ** 2 * (t < dur * 0.42)
    envl += 0.8 * np.sin(np.pi * np.clip((t - dur * 0.5) / (dur * 0.45), 0, 1)) ** 2 * (t > dur * 0.5)
    return (I.bp(noise(dur), 180, 1400) * envl * vel * 0.12).astype(np.float32)


def whistle(dur=0.9, f0=2400):
    """A bead streaking down: a descending airy whistle."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 - 0.45 * t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    air = I.bp(noise(dur), 1800, 7000) * 0.6
    return ((tone + air) * np.sin(np.pi * t / dur) ** 2 * 0.05).astype(np.float32)


def hiss(dur=1.4):
    n = int(dur * SR)
    return (I.hp(noise(dur), 2500) * env_exp(n, 0.35, 0.01) * 0.18).astype(np.float32)


def swish(dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (I.bp(noise(dur), 1200, 7000) * np.sin(np.pi * t / dur) ** 2 * 0.12).astype(np.float32)


def bed(kind, t0, t1, level, bus, pan_w=0.6, seed=0):
    """Continuous ambience beds, softly faded at both ends."""
    dur = t1 - t0
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    if kind == "wind":
        x = I.bp(r.standard_normal(n), 120, 1200)
        x *= 0.6 + 0.4 * np.sin(2 * np.pi * t / 9.0 + r.random() * 6) * np.sin(2 * np.pi * t / 23.0 + 1)
    elif kind == "insects":      # midday drone
        x = I.bp(r.standard_normal(n), 4200, 6500) * (0.7 + 0.3 * np.sin(2 * np.pi * 38 * t))
    elif kind == "crickets":
        x = np.zeros(n)
        for k in range(6):
            fc = 4200 + 600 * k
            gate = (np.sin(2 * np.pi * (2.0 + 0.3 * k) * t + k) > 0.3) * (np.sin(2 * np.pi * 30 * t) > 0)
            x += np.sin(2 * np.pi * fc * t) * gate * (0.4 + 0.2 * r.random())
        x = I.lp(x, 9000)
    elif kind == "frogs":
        x = np.zeros(n)
        for k in range(10):
            per = 0.9 + r.random() * 1.6
            ph = r.random() * per
            gate = ((t + ph) % per) < 0.18
            f = 380 + 260 * r.random()
            x += np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 42 * t)) * gate * (0.3 + 0.4 * r.random())
        x = I.lp(x, 2500)
    elif kind == "water":
        x = I.bp(r.standard_normal(n), 250, 2200) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * t / 2.7)) ** 3)
    elif kind == "room":
        x = I.lp(r.standard_normal(n), 400) * 0.6 + np.sin(2 * np.pi * 60 * t) * 0.02
    elif kind == "fire":
        x = I.bp(r.standard_normal(n), 300, 3000) * 0.4
        pops = (r.random(n) > 0.9993) * r.standard_normal(n) * 6
        x += I.hp(pops, 1500)
        x += I.lp(r.standard_normal(n), 150) * 0.8
    elif kind == "rumble":
        x = I.lp(r.standard_normal(n), 90) * 2.0
    else:
        raise ValueError(kind)
    fade = np.ones(n)
    f = min(n // 2, int(1.2 * SR))
    fade[:f] = np.linspace(0, 1, f) ** 2
    fade[-f:] = np.linspace(1, 0, f) ** 2
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * fade * level
    # decorrelated stereo
    d = int(0.011 * SR)
    xl = x
    xr = np.r_[np.zeros(d), x[:-d]]
    i0 = int(t0 * SR)
    m = min(n, bus.n - i0)
    bus.L[i0:i0 + m] += xl[:m].astype(np.float32)
    bus.R[i0:i0 + m] += xr[:m].astype(np.float32)


def contact_times(sfun, t0, t1, gait, dt=1 / 480):
    """Times (and foot index) at which a gait's feet touch down, from the body's s(t)."""
    out = []
    t = t0
    s_prev = sfun(t0)
    while t < t1:
        t2 = t + dt
        s2 = sfun(t2)
        if s2 > s_prev:
            for s_c, i in gait.contacts(s_prev, s2):
                out.append((t + dt * (s_c - s_prev) / max(1e-9, s2 - s_prev), i))
        s_prev = s2
        t = t2
    return out


def build():
    from creatures import OH_GAIT, WI_GAIT_RUN
    import shots_act2 as A2
    bus = Bus(TL.DURATION + 4)
    # ------------------------------------------------------------ ambience beds
    bed("wind", 7.0, 17.0, 0.006, bus, seed=1)
    bed("frogs", 17.0, 30.0, 0.010, bus, seed=2)
    bed("water", 17.0, 83.0, 0.010, bus, seed=3)
    bed("wind", 17.0, 83.0, 0.008, bus, seed=4)
    bed("insects", 83.0, 97.3, 0.006, bus, seed=5)           # stops dead: the insects go silent
    bed("wind", 83.0, 136.0, 0.006, bus, seed=6)
    bed("wind", 130.0, 145.0, 0.008, bus, seed=7)
    bed("water", 136.0, 173.0, 0.008, bus, seed=8)
    bed("frogs", 138.0, 173.0, 0.012, bus, seed=9)
    bed("crickets", 143.0, 173.0, 0.005, bus, seed=10)
    bed("rumble", 191.6, 225.0, 0.04, bus, seed=11)
    bed("fire", 201.0, 225.0, 0.03, bus, seed=12)
    bed("wind", 230.0, 254.0, 0.014, bus, seed=13)            # ash wind (after 5 s of true silence)
    bed("wind", 254.0, 291.0, 0.007, bus, seed=14)
    bed("room", 291.0, 305.0, 0.004, bus, seed=15)
    # ------------------------------------------------------------ Old Horn: footfalls, breath, hums
    s_end = OH_GAIT.settle(0.0)
    walks = [
        (lambda t: -330 * (1 - ease_in_out_sine(clamp((t - 44.2) / 2.6))) + s_end * ease_in_out_sine(clamp((t - 44.2) / 2.6)), 44.2, 47.0, 0.9),
        (lambda t: min(A2.S9_S(t), s_end), 83.0, 86.0, 0.9),
        (lambda t: A2.OH12_S(t), 110.0, 113.0, 1.25),
        (lambda t: (t - 130.0) * 110.0, 130.0, 136.0, 0.75),
    ]
    for sf, a, b, w in walks:
        for tt, i in contact_times(sf, a, b, OH_GAIT):
            bus.add(tt, thud(w * (1.0 if i >= 2 else 0.85)), 0.55 * (1 if i % 2 == 0 else 0.8), 0.1 * (i - 1.5))
    bus.add(EV["lie_down"] + 1.2, thud(1.3, 1.4), 0.7, 0.0)
    bus.add(EV["buckle"] + 0.3, thud(1.4, 1.4), 0.8, 0.0)
    bus.add(39.6, bellow(1.2, 70, seed=3), 0.25, -0.1)        # knees complain: a low grunt as she rises
    for tt in np.arange(180.2, 191.0, 3.6):                   # S19: only her breathing remains
        bus.add(tt, breath(3.4, 0.9), 1.0, -0.1)
    for tt, sh in [(EV["hum_s8"], 0), (EV["hum_shaky"], 1), (EV["hum_gift"], 0), (EV["final_hum"], 0),
                   (EV["final_hum2"], 0), (EV["end_hum"], 0)] + [(h, 0) for c, h in TL.DUET]:
        d = 1.0 if tt in [h for c, h in TL.DUET] else 1.8
        bus.add(tt, I.hum(38, d, 0.9, shaky=sh, seed=int(tt)), 1.0, -0.15)
    # ------------------------------------------------------------ Wisp: chirps, hops, rustles
    chirps = list(EV["chirp_s5"]) + [c for c, h in TL.DUET] + [130.3 + 0.78 * k for k in range(8)] + \
        [89.2, EV["final_chirp"], EV["end_chirp"]]
    for tt in chirps:
        bus.add(tt, I.chirp(0.6 if tt < 300 else 0.35, seed=int(tt * 10)), 1.0, 0.2)
    for k, tt in enumerate(EV["indignant"]):
        bus.add(tt, I.chirp(0.8, notes=(86, 83), gap=0.08, seed=70 + k), 1.0, -0.3)
    bus.add(EV["broken_call"], I.chirp(0.55, broken=1.0, seed=99), 1.0, -0.2)
    for k in range(4):
        bus.add(TL.NEW_STAR_TRILL + 0.13 * k, I.chirp(0.7, notes=(86 + (k % 2) * 3,), dur=0.08, seed=110 + k), 1.0, 0.3)
    bus.add(EV["wisp_yawn"], squeak(1800, 0.45), 0.6, 0.2)
    bus.add(33.2, rustle(0.9), 1.0, 0.25)
    bus.add(EV["wisp_wake_tuft"], rustle(0.3), 0.6, 0.25)
    for tt in [38.0, 52.2, 68.3, 80.9, 96.6, 161.3, 215.9]:
        bus.add(tt, tap(), 1.0, 0.1)
    for a, b in [(52.2, 54.6), (90.0, 94.5), (206.6, 207.0), (208.4, 210.0), (210.0, 215.0), (79.2, 80.2)]:
        for tt in np.arange(a, b, 0.14):
            bus.add(tt + RNG.uniform(-0.01, 0.01), tap(0.05), 0.5, RNG.uniform(-0.3, 0.3))
    for k, tt in enumerate(np.arange(90.0, EV["dragonfly_catch"], 0.9)):   # dragonfly wings
        n = int(0.8 * SR)
        tb = np.arange(n) / SR
        buzz = np.sin(2 * np.pi * 180 * tb) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * tb))
        bus.add(tt, (I.lp(buzz, 1200) * I._env(n, 0.2, 0.3) * 0.02).astype(np.float32), 1.0, 0.4 * math.sin(k))
    # ------------------------------------------------------------ the Burrower, the pebble
    bus.add(51.7, squeak(3600, 0.1), 1.0, -0.3)
    bus.add(EV["burrow_dive"], squeak(3000, 0.14), 1.0, -0.4)
    bus.add(55.3, squeak(3900, 0.08), 0.7, -0.4)
    bus.add(206.8, squeak(3300, 0.1), 0.8, -0.4)
    for tt in (251.2, 252.0, 252.6):
        bus.add(tt, squeak(4200, 0.05), 0.35, -0.2)            # sniffing the grey air
    bus.add(EV["pebble_drop"], click(0.05, 2200), 1.0, 0.1)
    bus.add(EV["pebble_nudge"], I.bp(noise(0.25), 800, 3000).astype(np.float32) * 0.03, 1.0, 0.1)
    bus.add(EV["knot_store"], click(0.06, 1500), 1.0, -0.2)
    bus.add(EV["pebble_give"], click(0.05, 2400), 1.0, 0.1)
    # ------------------------------------------------------------ the Hunter
    for tt in EV["rex_boom"]:
        bus.add(tt, boom(3.5), 1.0, 0.1)
    for tt in A2.FAR_STEPS:
        bus.add(tt, thud(1.6, 1.2), 0.35, 0.3)
    for tt in EV["rex_steps"] + [109.4] + [EV["rex_leave"] + 1.1 * k for k in range(4)]:
        g = 0.9 if tt < 124 else 0.6 * (1 - (tt - 124.0) / 5)
        bus.add(tt, thud(1.8, 1.4), max(0.1, g), 0.2 * math.sin(tt))
    for tt in [101.6, 103.9, 105.8, 108.2, 114.2, 118.8, 122.6]:
        bus.add(tt, snort(1.0), 0.8, 0.2)
    # ------------------------------------------------------------ the herd
    for k, tt in enumerate([21.5, 25.8, 33.0, 46.5, 74.0]):
        bus.add(tt, bellow(1.2, 110 + 10 * k, seed=k), 0.25, 0.4)
    bus.add(176.4, bellow(2.2, 80, seed=20), 0.5, 0.3)
    for k in range(7):
        bus.add(192.0 + 0.35 * k, bellow(1.4, 90 + 12 * k, seed=30 + k), 0.55, -0.5 + 0.18 * k)
    # ------------------------------------------------------------ the end of the world
    n = int(5.0 * SR)
    tb = np.arange(n) / SR
    quake = I.lp(noise(5.0), 60) * 3 + np.sin(2 * np.pi * 24 * tb) * 1.2
    bus.add(EV["seismic"], (quake * I._env(n, 0.02, 2.5) * 0.35).astype(np.float32), 1.0, 0.0)
    surge = I.bp(noise(3.5), 100, 1500) * I._env(int(3.5 * SR), 1.2, 1.2)
    bus.add(192.4, (surge * 0.12).astype(np.float32), 1.0, 0.0)
    for k in range(260):                                       # bead streaks, hisses, patter
        tt = 199.4 + (k / 260) ** 0.9 * 25.4
        if tt >= 224.9:
            continue
        bus.add(tt + RNG.uniform(0, 0.08), whistle(0.5 + RNG.random() * 0.8, 1600 + RNG.random() * 2400),
                0.5 + 0.5 * RNG.random(), RNG.uniform(-0.9, 0.9))
    import shots_act3 as A3
    for a_, b_, t0 in A3.STEAM:
        bus.add(t0, hiss(1.3), 0.5, RNG.uniform(-0.6, 0.6))
    for tt in np.arange(204.0, 224.9, 0.05):
        if RNG.random() < 0.5:
            bus.add(tt, tap(0.03), 0.25, RNG.uniform(-0.9, 0.9))
    # ------------------------------------------------------------ Act IV + epilogue
    for tt in np.arange(231.0, 254.0, 0.07):                   # the faint tick of ash
        if RNG.random() < 0.2:
            bus.add(tt, tap(0.02), 0.06, RNG.uniform(-0.8, 0.8))
    for tt in EV["brush"]:
        for k in range(3):
            bus.add(tt + 0.45 * k, swish(0.35), 0.8, 0.2)
    return bus


if __name__ == "__main__":
    import time
    t0 = time.time()
    b = build()
    st = b.st()
    # the cut to white is a cut to *digital* silence: nothing survives 225.0–230.0
    st[int(225.0 * SR):int(230.0 * SR)] = 0.0
    np.save(os.path.join(HERE, "..", "build", "sfx_dry.npy"), st)
    print(f"sfx built in {time.time() - t0:.0f}s, peak {np.abs(st).max():.3f}")
