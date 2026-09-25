"""Facing East — frame renderer.

    python render.py stills 5 40 70 ...      # style frames -> build/stills/
    python render.py video                   # full render -> build/video.mp4
    python render.py video --start 100 --end 120   # partial preview

The whole film is one continuous world (a sunflower field) whose time of day,
camera and characters are driven by keyframe tracks, so every transition is
motivated by light rather than by a cut.
"""
import argparse
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "shared"))

from foxfolly import post  # noqa: E402
from foxfolly.anim import (Track, clamp, lerp, smoothstep, window,  # noqa: E402
                           ease_in_out_sine)
from foxfolly.noise import fractal_noise  # noqa: E402
from foxfolly.text import TextCache, composite  # noqa: E402

import flora  # noqa: E402
import story  # noqa: E402
from flora import Light, c4, draw_flower  # noqa: E402

W, H, FPS = story.W, story.H, story.FPS
HORIZON = 610.0
BUILD = os.path.join(HERE, "..", "build")

# =====================================================================
#                              TIME TRACKS
# =====================================================================
# Clock in days. frac 0.25 = sunrise, 0.5 = noon, 0.75 = sunset.
CLOCK = Track([
    (0, 1.060), (18, 1.190), (22, 1.214), (26, 1.246), (30, 1.270),
    (38, 1.360), (46, 1.500), (54, 1.690), (58, 1.765),
    (61, 1.960), (64.5, 2.380), (70, 2.540), (80, 2.620), (90, 2.670), (97, 2.700),
    (112, 5.195), (115, 5.232), (118, 5.258), (122, 5.285), (128, 5.330), (136, 5.420),
    (139, 5.460), (147, 5.715), (151, 5.775), (156, 5.850), (166, 5.985),
    (175, 6.160), (178, 6.203), (181, 6.228), (186, 6.252), (190, 6.264),
    (198, 6.281), (214, 6.310), (240, 6.345), (300, 6.40),
])

# Camera keys are (look-at x, look-at y, zoom) in hero-plane world pixels.
_CAM_KEYS = [
    (0, (1000, 560, 1.00)), (14, (1120, 620, 1.25)), (22, (1150, 640, 1.40)),
    (27, (1080, 600, 1.35)), (40, (1000, 540, 1.10)), (52, (1060, 580, 1.20)),
    (60, (1120, 620, 1.30)),
    (64, (960, 560, 1.05)), (73, (600, 590, 1.22)), (80, (640, 590, 1.18)),
    (87, (1080, 600, 1.20)), (97, (1130, 620, 1.30)),
    (104, (1000, 520, 1.05)), (112, (980, 470, 1.00)), (115, (1140, 500, 1.30)),
    (123, (1170, 505, 1.50)), (136, (1120, 500, 1.30)),
    (143, (1000, 480, 1.05)), (151, (1040, 490, 1.10)), (162, (1130, 510, 1.35)),
    (177, (1170, 520, 1.50)),
    (186, (1130, 510, 1.42)), (196, (1080, 500, 1.30)), (206, (985, 480, 1.03)),
    (214, (960, 470, 1.00)), (238, (900, 455, 1.05)), (300, (900, 455, 1.05)),
]
CAM = Track([(t, (x - W / 2, y - H / 2, z)) for t, (x, y, z) in _CAM_KEYS])

H_YAW_S1 = Track([(0, 62), (4, 62), (17, -70), (22, -72)], mode="ease")
H_HEIGHT = Track([(0, 820), (97, 820), (100, 835), (111, 980), (136, 995)])
H_HEAD = Track([(0, 92), (97, 92), (100, 96), (111, 140), (115, 142), (122, 178)])
H_BLOOM = Track([(0, 0.22), (97, 0.22), (111, 0.36), (115.5, 0.36), (121.5, 1.0)])
H_X, H_BASE_Y = 1240.0, 1480.0

OLD_ONES = [  # x, base_y, height, head_r, yaw, pitch, depth, seed
    (1640, 1080, 470, 78, -70, -20, 0.62, 13),
    (860, 1090, 480, 84, -72, -18, 0.66, 11),
    (560, 1120, 540, 96, -67, -22, 0.74, 12),
    (230, 1150, 600, 108, -74, -24, 0.80, 14),
    (1960, 1160, 620, 112, -76, -26, 0.84, 15),
]


# =====================================================================
#                           LIGHT & SKY MODEL
# =====================================================================
_E = [-1.0, -0.30, -0.12, -0.035, 0.02, 0.12, 0.35, 1.0]
_ZEN = [(0.012, 0.018, 0.050), (0.016, 0.024, 0.065), (0.035, 0.045, 0.110),
        (0.075, 0.090, 0.200), (0.140, 0.180, 0.340), (0.220, 0.300, 0.500),
        (0.180, 0.320, 0.580), (0.130, 0.270, 0.560)]
_HOR = [(0.070, 0.095, 0.180), (0.080, 0.105, 0.195), (0.170, 0.130, 0.210),
        (0.560, 0.310, 0.230), (0.980, 0.560, 0.240), (1.000, 0.740, 0.420),
        (0.860, 0.760, 0.600), (0.700, 0.740, 0.740)]
_AMB = [(0.095, 0.115, 0.200), (0.100, 0.120, 0.210), (0.130, 0.120, 0.190),
        (0.240, 0.190, 0.210), (0.300, 0.240, 0.240), (0.360, 0.330, 0.320),
        (0.400, 0.400, 0.400), (0.420, 0.430, 0.440)]
_SUN = [(1.0, 0.40, 0.15)] * 4 + [(1.0, 0.48, 0.18), (1.0, 0.64, 0.32),
                                  (1.0, 0.86, 0.64), (1.0, 0.95, 0.86)]


def _interp(table, e):
    a = np.array(table)
    return tuple(float(np.interp(e, _E, a[:, i])) for i in range(3))


class Env:
    """Everything about the light at clock value D."""

    def __init__(self, D):
        f = D % 1.0
        self.D, self.f = D, f
        self.e = math.sin(2 * math.pi * (f - 0.25))
        self.zenith = _interp(_ZEN, self.e)
        self.horizon = _interp(_HOR, self.e)
        self.ambient = _interp(_AMB, self.e)
        self.sun_rgb = _interp(_SUN, self.e)
        self.sun_k = smoothstep(-0.03, 0.10, self.e)
        self.night = smoothstep(-0.02, -0.22, self.e)
        p = (f - 0.25) / 0.5
        self.p = p
        # sun position in screen space (sky is at infinity)
        self.sun_x = W / 2 - (W / 2 - 150) * math.cos(math.pi * p)
        self.sun_y = HORIZON - 15 - 620 * self.e
        # azimuth as a flower-yaw: -90 east .. +90 west
        self.sun_yaw = clamp(-90 + 180 * p, -110, 110) if 0 <= p <= 1 else (-90 if p < 0 else 90)
        self.light = Light(self.ambient, self.sun_rgb, self.sun_k, self.sun_yaw)


# =====================================================================
#                                ASSETS
# =====================================================================
class Assets:
    def __init__(self):
        t0 = time.time()
        self.disc = flora.make_disc_image(512, seed=3)
        self.disc_hi = flora.make_disc_image(1800, n=2600, seed=5)
        self.clouds = fractal_noise(256, 512, beta=2.6, seed=21)
        self.stars = self._stars()
        self.hills = self._hills()
        self.field_far, self.field_far_face = self._field(0)
        self.field_mid, self.field_mid_face = self._field(1)
        self.fore = self._foreground()
        self.mist = self._mist()
        self.text = TextCache()
        import cv2
        lo = cv2.resize(fractal_noise(270, 480, beta=2.4, seed=61), (W, H))
        hi = fractal_noise(H, W, beta=0.6, seed=62)
        self.paper = (1 + 0.05 * (lo - 0.5) + 0.03 * (hi - 0.5))[..., None].astype(np.float32)
        self.load_time = time.time() - t0

    # -- stars: static sky that rotates slowly about a pole off-frame
    def _stars(self):
        rng = np.random.default_rng(7)
        S = 2800
        img = np.zeros((S, S, 4), np.float32)
        # milky way band
        band = fractal_noise(S // 4, S // 4, beta=2.2, seed=8)
        import cv2
        band = cv2.resize(band, (S, S))
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
        d = np.abs((yy - 0.35) - (xx - 0.5) * 0.55)
        mw = np.exp(-(d / 0.09) ** 2) * (0.35 + band) ** 2 * 0.07
        img[..., 0] = mw * 0.75
        img[..., 1] = mw * 0.80
        img[..., 2] = mw * 1.00
        n = 2600
        xs = rng.random(n) * S
        ys = rng.random(n) * S
        mags = rng.pareto(2.2, n) * 0.25 + 0.08
        dens = 1 + 2.5 * np.exp(-(np.abs((ys / S - 0.35) - (xs / S - 0.5) * 0.55) / 0.09) ** 2)
        for x, y, m, dd in zip(xs, ys, mags, dens):
            if rng.random() > 0.55 * dd:
                continue
            m = min(m, 2.2)
            r = 1.0 + min(m, 1.2) * 1.4
            x0, x1 = int(max(0, x - 4 * r)), int(min(S, x + 4 * r + 1))
            y0, y1 = int(max(0, y - 4 * r)), int(min(S, y + 4 * r + 1))
            gy, gx = np.mgrid[y0:y1, x0:x1]
            g = np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (2 * (r * 0.45) ** 2)) * m
            tint = (0.85 + 0.3 * rng.random(), 0.9, 1.0 + 0.2 * rng.random())
            for ch in range(3):
                img[y0:y1, x0:x1, ch] += g * tint[ch]
        img[..., 3] = 1.0
        return skia.Image.fromarray(np.clip(img, 0, 8).astype(np.float16),
                                    colorType=skia.kRGBA_F16_ColorType)

    def _hills(self):
        rng = np.random.default_rng(31)
        out = []
        for layer, (base, amp, seed) in enumerate(((HORIZON - 70, 55, 1), (HORIZON - 22, 30, 2))):
            xs = np.linspace(-800, W + 800, 180)
            n1 = fractal_noise(1, 512, beta=3.2, seed=40 + seed)[0]
            ys = base - amp * (np.interp(np.linspace(0, 511, len(xs)), np.arange(512), n1) - 0.4) * 2
            pth = skia.Path()
            pth.moveTo(xs[0], H + 400)
            for x, y in zip(xs, ys):
                pth.lineTo(float(x), float(y))
            pth.lineTo(xs[-1], H + 400)
            pth.close()
            out.append(pth)
        return out

    def _field(self, which):
        """Pre-rendered crowd of mature (east-facing) sunflowers.

        Returns (albedo_layer, face_layer). The face layer is black except the
        flower faces, and is added with the sun colour at dawn so the whole
        field "lights up" when the sun rises in front of it.
        """
        rng = np.random.default_rng(100 + which)
        LW, LH = int(W * 1.7), H + 200
        ox = (LW - W) / 2
        if which == 0:
            rows = np.linspace(HORIZON - 12, HORIZON + 150, 34)
            rmin, rmax, per = 2.2, 8.0, 70
        else:
            rows = np.linspace(HORIZON + 70, HORIZON + 470, 16)
            rmin, rmax, per = 9.0, 30.0, 26
        items = []
        for i, ry in enumerate(rows):
            u = i / (len(rows) - 1)
            r = rmin + (rmax - rmin) * u ** 1.3
            cnt = int(per * (1.2 - 0.5 * u))
            for k in range(cnt):
                x = rng.random() * LW
                y = ry + rng.normal() * (rows[1] - rows[0]) * 0.4
                items.append((y, x, r * (0.8 + 0.4 * rng.random()), rng.integers(1e6)))
        items.sort()
        layers = []
        for face_only in (False, True):
            surf = skia.Surface(LW, LH)
            cv = surf.getCanvas()
            cv.clear(skia.ColorTRANSPARENT)
            if which == 0:
                # dark ground under the far rows
                p = skia.Paint(Color4f=c4((0.10, 0.16, 0.06) if not face_only else (0, 0, 0)))
                cv.drawRect(skia.Rect(0, HORIZON - 4, LW, LH), p)
            L = Light((1, 1, 1), (0, 0, 0), 0.0, 0.0)
            for y, x, r, seed in items:
                yaw = -72 + rng.normal() * 9
                draw_flower(cv, self.disc, (x, y + r * 6.5), r * 6.5, r, yaw,
                            -16 + rng.normal() * 6, 1.0, L, seed=int(seed),
                            leaves=2 if which == 0 else 3, detail=0.2 if which == 0 else 0.4,
                            face_only=face_only, petal_n=21)
            img = surf.makeImageSnapshot()
            layers.append((img, ox))
        return layers

    def _mist(self):
        """Low drifting ground mist (alpha texture, tinted per frame)."""
        import cv2
        n = fractal_noise(128, 512, beta=2.8, seed=77)
        n = cv2.resize(n, (int(W * 1.8), 360))
        y = np.linspace(-1, 1, 360, dtype=np.float32)[:, None]
        prof = np.exp(-(y / 0.55) ** 2)
        a = np.clip((n - 0.3) * 1.6, 0, 1) * prof
        img = np.zeros((360, int(W * 1.8), 4), np.float16)
        img[..., 0] = a
        img[..., 1] = a
        img[..., 2] = a
        img[..., 3] = a
        return skia.Image.fromarray(img, colorType=skia.kRGBA_F16_ColorType)

    def _foreground(self):
        """Out-of-focus foliage framing the bottom corners (depth of field)."""
        LW, LH = W + 800, H + 400
        surf = skia.Surface(LW, LH)
        cv = surf.getCanvas()
        cv.clear(skia.ColorTRANSPARENT)
        L = Light((1, 1, 1), (0, 0, 0), 0.0, 0.0)
        draw_flower(cv, self.disc, (170, LH + 60), 520, 150, -70, -22, 1.0, L, seed=91,
                    leaves=3)
        draw_flower(cv, self.disc, (LW - 120, LH + 140), 440, 120, -78, -28, 1.0, L,
                    seed=92, leaves=3)
        p = skia.Paint(AntiAlias=True, Color4f=c4(flora.LEAF_DARK))
        for (x, y, rot, s) in ((380, LH - 40, -30, 330), (LW - 420, LH - 20, 210, 360),
                               (60, LH - 330, 20, 260)):
            cv.save()
            cv.translate(x, y)
            cv.rotate(rot)
            cv.drawPath(flora.leaf_path(s, s * 0.45), p)
            cv.restore()
        img = surf.makeImageSnapshot()
        blurred = skia.Surface(LW, LH)
        bc = blurred.getCanvas()
        bc.clear(skia.ColorTRANSPARENT)
        bp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(16, 16))
        bc.drawImage(img, 0, 0, skia.SamplingOptions(), bp)
        return blurred.makeImageSnapshot(), 400, 400


# =====================================================================
#                              PARTICLES
# =====================================================================
_prng = np.random.default_rng(555)
FIREFLIES = _prng.random((46, 6))
POLLEN = _prng.random((150, 5))
BEES = _prng.random((16, 6))


def draw_glow(cv, x, y, r, rgb, a):
    if a <= 0.003:
        return
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                   Shader=skia.GradientShader.MakeRadial(
                       (x, y), r, [c4(rgb, a), c4(rgb, a * 0.25), c4(rgb, 0.0)], [0.0, 0.25, 1.0]))
    cv.drawCircle(x, y, r, p)


def fireflies(cv, t, amount):
    if amount <= 0:
        return
    for i, (a, b, c, d, e, f) in enumerate(FIREFLIES):
        x = 80 + a * (W - 160) + 60 * math.sin(t * (0.13 + 0.1 * b) + 6.28 * c)
        y = HORIZON + 40 + b * 420 + 30 * math.sin(t * (0.21 + 0.12 * d) + 6.28 * e)
        period = 3.0 + 4.0 * d
        ph = ((t + f * period) % period) / period
        blink = smoothstep(0.0, 0.18, ph) * (1 - smoothstep(0.25, 0.55, ph))
        s = 0.5 + b
        draw_glow(cv, x, y, 16 * s, (0.72, 1.0, 0.45), amount * blink * 0.9)
        draw_glow(cv, x, y, 2.4 * s, (1.0, 1.0, 0.85), amount * blink)


def pollen(cv, t, amount, warm):
    if amount <= 0:
        return
    for (a, b, c, d, e) in POLLEN:
        x = (a * (W + 200) + t * (6 + 10 * c)) % (W + 200) - 100
        y = (b * (H + 100) - t * (4 + 8 * d)) % (H + 100) - 50 + 12 * math.sin(t * 0.5 + 6 * e)
        tw = 0.5 + 0.5 * math.sin(t * (0.8 + e) + a * 20)
        r = 1.2 + 2.6 * e
        draw_glow(cv, x, y, r * 4, warm, amount * (0.25 + 0.45 * tw) * 0.5)


def bees(cv, t, amount, targets):
    """Bees at dawn: small amber bodies with blurred glinting wings."""
    if amount <= 0 or not targets:
        return
    for i, (a, b, c, d, e, f) in enumerate(BEES):
        tx, ty, tr = targets[i % len(targets)]
        arrive = 180.0 + 6 + a * 14  # arrive from the east over time
        k = ease_in_out_sine(clamp((t - arrive) / 5.0))
        if k <= 0:
            continue
        # orbit around the flower face
        w1 = 0.6 + 0.8 * b
        ox = math.cos(t * w1 + 6.28 * c) * tr * (0.7 + 0.5 * d)
        oy = math.sin(t * w1 * 1.3 + 6.28 * e) * tr * 0.45
        sx, sy = -300 + 200 * f, ty - 200 - 250 * e
        x = lerp(sx, tx + ox, k)
        y = lerp(sy, ty + oy, k) + 14 * math.sin(t * 7 + i)
        al = amount * min(1.0, k * 3)
        draw_glow(cv, x, y, 34, (1.0, 0.8, 0.4), al * 0.45)
        p = skia.Paint(AntiAlias=True, Color4f=c4((0.30, 0.19, 0.05), al))
        cv.drawOval(skia.Rect(x - 8, y - 5, x + 8, y + 5), p)
        p.setColor4f(c4((1.1, 0.78, 0.25), al))
        cv.drawOval(skia.Rect(x - 4, y - 5, x + 0.5, y + 5), p)
        cv.drawOval(skia.Rect(x + 2.5, y - 4.5, x + 5.5, y + 4.5), p)
        wing = 0.5 + 0.5 * math.sin(t * 60 + i)
        p.setColor4f(c4((1.2, 1.1, 1.0), al * (0.35 + 0.3 * wing)))
        cv.drawOval(skia.Rect(x - 6, y - 15, x + 4, y - 3), p)
        cv.drawOval(skia.Rect(x - 1, y - 13, x + 9, y - 3), p)


# =====================================================================
#                              RENDERING
# =====================================================================
def layer_matrix(cam, d):
    cx, cy, z = cam
    s = 1 + (z - 1) * d
    m = skia.Matrix()
    m.preTranslate(W / 2, H / 2)
    m.preScale(s, s)
    m.preTranslate(-W / 2 - cx * d, -H / 2 - cy * d)
    return m


def world_to_screen(cam, d, x, y):
    cx, cy, z = cam
    s = 1 + (z - 1) * d
    return (W / 2 + (x - W / 2 - cx * d) * s, H / 2 + (y - H / 2 - cy * d) * s)


def sky_array(env, cam, t, A):
    """Low-res sky computed in numpy, returned full-res float RGBA."""
    import cv2
    sw, sh = 384, 216
    k = W / sw
    hor_y = world_to_screen(cam, 0.08, 0, HORIZON)[1] / k
    ys = np.arange(sh, dtype=np.float32)[:, None]
    xs = np.arange(sw, dtype=np.float32)[None, :]
    v = np.clip((hor_y - ys) / max(hor_y, 1), 0, 1)
    zen = np.array(env.zenith, np.float32)
    hor = np.array(env.horizon, np.float32)
    mixk = (v ** 0.55)[..., None]
    sky = hor * (1 - mixk) + zen * mixk
    sky = np.broadcast_to(sky, (sh, sw, 3)).copy()
    # sun glow & warm horizon band on the sun's side
    sx, sy = env.sun_x / k, env.sun_y / k
    dx = xs - sx
    dy = ys - sy
    dist = np.sqrt(dx * dx + dy * dy)
    low = 1 - smoothstep(0.05, 0.6, env.e)
    glow = np.exp(-dist / 26.0) * (0.35 * env.sun_k) + np.exp(-dist / 7.0) * 0.7 * env.sun_k
    band = np.exp(-(dx / 150.0) ** 2) * np.exp(-((ys - hor_y) / 30.0) ** 2) * low
    pre = smoothstep(-0.16, -0.01, env.e) * (1 - 0.6 * env.sun_k)  # pre-dawn glow
    sunc = np.array(env.sun_rgb, np.float32)
    sky += glow[..., None] * sunc * 0.9
    sky += band[..., None] * sunc * (0.7 * env.sun_k + 1.3 * pre)
    # clouds: soft drifting wisps above the horizon
    cl = A.clouds
    off = t * 1.6 + env.D * 40
    yi = (np.clip(ys * 1.0, 0, sh - 1)).astype(int)
    ci = ((xs * 1.0 + off) % cl.shape[1]).astype(int)
    c = cl[(yi * 1) % cl.shape[0], ci]
    dens = np.clip((c - 0.52) * 3.0, 0, 1) * np.exp(-((ys - (hor_y - 55)) / 45.0) ** 2)
    lit = np.array(env.horizon, np.float32) * 0.8 + sunc * 0.25 * env.sun_k
    dark = np.array(env.zenith, np.float32) * 0.7
    sunside = np.exp(-(dx / 260.0) ** 2)[..., None]
    ccol = dark + (lit - dark) * (0.35 + 0.65 * sunside)
    sky = sky * (1 - dens[..., None] * 0.7) + ccol * dens[..., None] * 0.7
    full = cv2.resize(sky, (W, H), interpolation=cv2.INTER_CUBIC)
    out = np.empty((H, W, 4), np.float16)
    out[..., :3] = full
    out[..., 3] = 1
    return out


def hesper_state(t, env):
    """Yaw, pitch, height, head size, bloom, strain for the heroine."""
    if t < 22:
        yaw = H_YAW_S1(t)
    elif t < 122:
        f = env.D % 1.0
        if 0.25 <= f <= 0.75:
            yaw = clamp(-90 + 180 * (f - 0.25) / 0.5, -72, 72)
        else:
            q = ((f - 0.75) % 1.0) / 0.5
            yaw = 72 - 144 * smoothstep(0.1, 0.75, q)
        # after 118 she is facing the dawn and stays there
        yaw = lerp(yaw, -72, smoothstep(117, 121, t))
    else:
        yaw = -72
    strain = 0.0
    for t0 in (125.0, 129.5):
        strain += math.sin(math.pi * clamp((t - t0) / 2.6)) ** 2
    yaw += 14 * strain
    if t < 118:
        pitch = 6 + 16 * max(0.0, env.e) * env.sun_k
    else:
        pitch = lerp(10, -12, smoothstep(122, 145, t))
    return dict(yaw=yaw, pitch=pitch, height=H_HEIGHT(t), head=H_HEAD(t),
                bloom=H_BLOOM(t), strain=strain)


def draw_image_tinted(cv, img, x, y, rgb, blend=None):
    p = skia.Paint(AntiAlias=True, ColorFilter=flora.tint_filter(rgb))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)


def render_world(t, A):
    D = CLOCK(t)
    env = Env(D)
    cam = CAM(t)
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_F16_ColorType, skia.kPremul_AlphaType)
    surf = skia.Surface.MakeRaster(info)
    cv = surf.getCanvas()
    sky = sky_array(env, cam, t, A)
    cv.drawImage(skia.Image.fromarray(sky, colorType=skia.kRGBA_F16_ColorType), 0, 0)

    # stars (rotate slowly about a pole above the frame)
    if env.night > 0.001:
        p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
        p.setAlphaf(env.night)
        cv.save()
        cv.translate(W * 0.5, 180)
        cv.rotate(t * 0.12 + D * 8)
        cv.drawImage(A.stars, -1400, -1400, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        cv.restore()

    # moon: a small cool key light for the night scenes (high in the west)
    if env.night > 0.001:
        mx, my = W * 0.80, 150
        draw_glow(cv, mx, my, 260, (0.55, 0.65, 0.95), 0.10 * env.night)
        p = skia.Paint(AntiAlias=True, Color4f=c4((1.3, 1.35, 1.5), env.night))
        cv.drawCircle(mx, my, 17, p)
        p.setColor4f(c4(env.zenith, env.night))
        cv.drawCircle(mx - 7, my - 4, 15, p)  # crescent shadow

    # sun disc
    if env.e > -0.12:
        sx, sy = env.sun_x, env.sun_y
        core = add3(env.sun_rgb, (0.6, 0.6, 0.6))
        draw_glow(cv, sx, sy, 190, env.sun_rgb, 0.35 * env.sun_k + 0.05)
        p = skia.Paint(AntiAlias=True, Color4f=c4(tuple(3.0 * v for v in core)))
        cv.drawCircle(sx, sy, 34, p)

    # hills with atmospheric perspective
    body = env.light.body(0.35)
    for i, (pth, d) in enumerate(zip(A.hills, (0.10, 0.18))):
        mixk = 0.45 if i == 0 else 0.72
        col = tuple(env.horizon[j] * (1 - mixk) + 0.22 * body[j] * mixk * (0.9, 1.0, 0.7)[j]
                    for j in range(3))
        cv.save()
        cv.setMatrix(layer_matrix(cam, d))
        cv.drawPath(pth, skia.Paint(AntiAlias=True, Color4f=c4(col)))
        cv.restore()

    # atmospheric haze colour for distant field
    face_far = env.light.face(-72)[1]
    sunadd = tuple(v * 1.25 * face_far for v in env.sun_rgb)
    for (img, ox), (fimg, _), d, haze in ((A.field_far, A.field_far_face, 0.30, 0.35),
                                            (A.field_mid, A.field_mid_face, 0.55, 0.12)):
        cv.save()
        cv.setMatrix(layer_matrix(cam, d))
        tint = tuple(body[j] * (1 - haze) + env.horizon[j] * haze * 0.6 for j in range(3))
        draw_image_tinted(cv, img, -ox, 0, tint)
        draw_image_tinted(cv, fimg, -ox, 0, sunadd, skia.BlendMode.kPlus)
        cv.restore()

    # ground mist hugging the far field: strongest at night and dawn
    mist_a = 0.10 + 0.30 * (1 - smoothstep(0.05, 0.45, env.e))
    mist_col = tuple(env.horizon[j] * 0.8 + 0.2 * env.ambient[j] for j in range(3))
    cv.save()
    cv.setMatrix(layer_matrix(cam, 0.40))
    mp = skia.Paint(ColorFilter=flora.tint_filter(mist_col))
    mp.setAlphaf(mist_a)
    drift = (t * 9) % (W * 0.8)
    cv.drawImage(A.mist, -W * 0.4 - drift * 0.5, HORIZON - 120, skia.SamplingOptions(skia.FilterMode.kLinear), mp)
    cv.restore()

    # the old ones (drawn by depth), then Hesper
    hs = hesper_state(t, env)
    bee_targets = []
    for (x, by, h, r, yaw, pitch, d, seed) in OLD_ONES:
        cv.save()
        cv.setMatrix(layer_matrix(cam, d))
        sway = 1.5 * math.sin(t * 0.4 + seed)
        (hx, hy), ff = draw_flower(cv, A.disc, (x, by), h, r, yaw + sway, pitch, 1.0,
                                   env.light, seed=seed, leaves=5, glow=0.0)
        cv.restore()
        bee_targets.append((*world_to_screen(cam, d, hx, hy), r * (1 + (cam[2] - 1) * d)))

    cv.save()
    cv.setMatrix(layer_matrix(cam, 1.0))
    sway = 1.2 * math.sin(t * 0.5)
    glow = 0.9 * window(t, 115.5, 126, 2.0, 6.0) + 0.6 * window(t, 186, 214, 3, 10)
    # the heroine catches a little more moonlight than the field (clear focal point)
    boost = 1 + 0.9 * env.night
    hlight = Light(tuple(v * boost for v in env.ambient), env.sun_rgb, env.sun_k, env.sun_yaw)
    (hx, hy), hff = draw_flower(cv, A.disc, (H_X, H_BASE_Y), hs["height"], hs["head"],
                                hs["yaw"] + sway, hs["pitch"], hs["bloom"], hlight,
                                seed=7, leaves=5, glow=glow, strain=hs["strain"])
    # a thin rim of cool light at night so the silhouette always reads
    cv.restore()
    bee_targets.insert(0, (*world_to_screen(cam, 1.0, hx, hy), hs["head"] * cam[2]))

    # particles in screen space
    fireflies(cv, t, env.night * (0.6 + 0.4 * window(t, 150, 178, 6)))
    pollen(cv, t, env.sun_k * 0.8, add3(env.sun_rgb, (0.0, 0.0, 0.0)))
    bees(cv, t, window(t, 184, 240, 2, 4), bee_targets)

    # foreground depth-of-field foliage
    fimg, fox, foy = A.fore
    cv.save()
    cv.setMatrix(layer_matrix(cam, 1.45))
    draw_image_tinted(cv, fimg, -fox, -foy, tuple(v * 0.7 for v in env.light.body(0.5)))
    cv.restore()

    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_F16_ColorType)
    img = arr[..., :3].astype(np.float32)
    return img, env, cam, (hx, hy)


def add3(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


# ----------------------------------------------------------- macro + card
def render_macro(t, A):
    """Closing image: the sunflower face, its golden-angle spiral turning."""
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_F16_ColorType, skia.kPremul_AlphaType)
    surf = skia.Surface.MakeRaster(info)
    cv = surf.getCanvas()
    cv.clear(c4((0.02, 0.015, 0.02)))
    u = (t - 236.0) / 40.0
    cx, cy = W * 0.5 + 60 * u, H * 0.46
    R = 470 + 90 * u
    L = Light((0.30, 0.22, 0.18), (1.0, 0.66, 0.34), 1.0, -40)
    # background: soft warm dawn haze
    bg = skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (W * 0.1, H * 0.3), 1500, [c4((0.40, 0.20, 0.08)), c4((0.05, 0.03, 0.04))], [0, 1]))
    cv.drawRect(skia.Rect(0, 0, W, H), bg)
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(8 * u)
    petal = skia.Paint(AntiAlias=True)
    rng = np.random.default_rng(4)
    for ring, (col, off, ls) in enumerate(((flora.PETAL_BACK, 0.5, 0.9), (flora.PETAL, 0.0, 1.0))):
        for k in range(34):
            j = rng.random()
            ang = (k + off) * 360 / 34
            lit = 0.30 + 0.55 * max(0, math.cos(math.radians(ang + 180 - 30)))
            tip = tuple(v * lit * (0.85 + 0.3 * j) for v in col)
            root = tuple(v * 0.35 for v in tip)
            petal.setShader(skia.GradientShader.MakeLinear(
                [(R * 0.9, 0), (R * 1.85, 0)], [c4(root), c4(tip)], [0.0, 1.0]))
            cv.save()
            cv.rotate(ang)
            cv.drawPath(flora.petal_path(R * 0.9, R * 0.95 * ls * (0.9 + 0.2 * j), R * 0.16,
                                         curl=(j - 0.5) * 20), petal)
            cv.restore()
    dp = skia.Paint(AntiAlias=True, ColorFilter=flora.tint_filter((1.15, 1.0, 0.85)))
    sz = A.disc_hi.width()
    cv.drawImageRect(A.disc_hi, skia.Rect(0, 0, sz, sz), skia.Rect(-R, -R, R, R),
                     skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), dp)
    cv.restore()
    # key light from the east (left)
    kl = skia.Paint(BlendMode=skia.BlendMode.kPlus, Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (W, 0)], [c4((0.16, 0.09, 0.03)), c4((0, 0, 0))], [0, 0.7]))
    cv.drawRect(skia.Rect(0, 0, W, H), kl)
    pollen(cv, t, 1.0, (1.0, 0.75, 0.4))
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_F16_ColorType)
    import cv2
    img = arr[..., :3].astype(np.float32)
    # shallow depth of field: blur toward the frame edges
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    blur = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2)
    m = np.clip((r - 0.25) / 0.35, 0, 1)[..., None]
    return img * (1 - m) + blur * m


def narration_alpha(t, s, e):
    return smoothstep(s, s + story.FADE, t) * (1 - smoothstep(e - story.FADE, e, t))


def draw_text(frame, t, A):
    """Narration + closing card. Returns frame (modified)."""
    band_a = 0.0
    for s, e, txt in story.LINES:
        a = narration_alpha(t, s, e)
        if a > 0:
            band_a = max(band_a, a)
    if band_a > 0:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        band = smoothstep_arr(0.72, 1.0, yy) * 0.38 * band_a
        frame *= (1 - band)
    for s, e, txt in story.LINES:
        a = narration_alpha(t, s, e)
        if a <= 0:
            continue
        drift = 6 * (1 - ease_in_out_sine(clamp((t - s) / story.FADE)))
        spr = A.text.get(txt, size=56)
        composite(frame, spr, W / 2, 952 + drift, a)
    # closing card
    if t >= story.CARD_IN - 0.5:
        end_a = 1 - smoothstep(story.FADE_OUT_START, story.DURATION - 0.6, t)
        ta = smoothstep(story.CARD_IN, story.CARD_IN + 2.0, t) * end_a
        sa = smoothstep(story.CARD_IN + 1.2, story.CARD_IN + 3.2, t) * end_a
        ha = smoothstep(story.HOOK_IN, story.HOOK_IN + 1.6, t) * end_a
        title = A.text.get(story.TITLE, size=150, face="CormorantGaramond-MediumItalic.ttf",
                           glow_alpha=0.35, color=(0.99, 0.93, 0.80))
        composite(frame, title, W / 2, 455, ta)
        sub = A.text.get(story.SUBTITLE, size=50, color=(0.92, 0.86, 0.76))
        composite(frame, sub, W / 2, 590, sa)
        hook = A.text.get(story.HOOK, size=38, face="CormorantGaramond-Regular.ttf",
                          color=(0.95, 0.80, 0.55), glow_alpha=0.25, letter_spacing=0.6)
        composite(frame, hook, W / 2, 720, ha)
        brand = A.text.get("FOX & FOLLY  ·  Old wisdom. Sharp twists.", size=30,
                           face="CormorantGaramond-Medium.ttf", color=(0.80, 0.74, 0.66),
                           glow_alpha=0.0, letter_spacing=2.5)
        composite(frame, brand, W / 2, 960, ha * 0.8)
    return frame


def smoothstep_arr(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


def render_frame(t, A, frame_idx=0):
    macro_w = smoothstep(237.7, 238.9, t)
    img = None
    if macro_w < 1.0:
        img, env, cam, hpos = render_world(t, A)
        # volumetric sun shafts near the horizon
        low = 1 - smoothstep(0.2, 0.55, env.e)
        rays = env.sun_k * low * 0.55
        if rays > 0.01:
            img = post.god_rays(img, (env.sun_x, env.sun_y), strength=rays, threshold=0.55)
    if macro_w > 0.0:
        m = render_macro(t, A)
        img = m if img is None else img * (1 - macro_w) + m * macro_w
    # light-based transition: the dawn swells into a warm flare that hides the cut
    flare = (smoothstep(235.2, 238.3, t) * (1 - smoothstep(238.3, 240.8, t))) ** 1.5
    if flare > 0:
        img = img + flare * 1.1 * np.array([1.0, 0.72, 0.38], np.float32)
    # the card: dim & defocus the macro behind the title
    card = smoothstep(story.CARD_IN - 1.5, story.CARD_IN + 2.5, t)
    if card > 0:
        import cv2
        small = cv2.resize(img, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
        blur = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3), (W, H))
        img = img * (1 - card) + blur * card * 0.2
    img = post.bloom(img, threshold=0.6, strength=0.55)
    img = post.grade(img, lift=(0.010, 0.013, 0.024), gamma=1.05, saturation=1.06,
                     warm_highlights=0.6)
    img = post.vignette(img, amount=0.42)
    # global fades
    fade = smoothstep(0.0, 3.5, t) * (1 - smoothstep(story.DURATION - 0.6, story.DURATION, t))
    img *= fade
    img *= A.paper
    img = draw_text(img, t, A)
    img = post.grain(img, frame_idx, amount=0.022)
    return post.to_uint8(img, frame_idx)


# =====================================================================
#                                 CLI
# =====================================================================
_A = None


def _init():
    global _A
    _A = Assets()


def _work(i):
    return render_frame(i / FPS, _A, i).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["stills", "video"])
    ap.add_argument("times", nargs="*", type=float)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=story.DURATION)
    ap.add_argument("--out", default=None)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    args = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    if args.mode == "stills":
        import cv2
        A = Assets()
        print(f"assets {A.load_time:.1f}s")
        outdir = os.path.join(BUILD, "stills")
        os.makedirs(outdir, exist_ok=True)
        for t in args.times:
            t0 = time.time()
            fr = render_frame(t, A, int(t * FPS))
            fn = os.path.join(outdir, f"still_{t:07.2f}.png")
            cv2.imwrite(fn, fr[..., ::-1])
            print(f"{fn}  {time.time() - t0:.2f}s")
        return
    out = args.out or os.path.join(BUILD, "video.mp4")
    f0, f1 = int(round(args.start * FPS)), int(round(args.end * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-b:v", "18M", "-maxrate", "28M", "-bufsize", "40M",
           "-x264-params", "aq-mode=3:deblock=-1,-1", "-tune", "grain",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import multiprocessing as mp
    t0 = time.time()
    with mp.get_context("fork").Pool(args.jobs, initializer=_init) as pool:
        for k, buf in enumerate(pool.imap(_work, range(f0, f1), chunksize=2)):
            ff.stdin.write(buf)
            if k % 150 == 0:
                el = time.time() - t0
                print(f"frame {f0 + k}/{f1}  {el:.0f}s elapsed", flush=True)
    ff.stdin.close()
    ff.wait()
    print(f"done {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
