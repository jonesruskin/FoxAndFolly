"""SECOND SUN — environments and effects (lantern luminism).

Everything is procedural and seeded. Plants never stand still: every frond,
bough and flower head sways with a shared wind field. Colour comes from a
per-shot Look (sky, ambient, key, rim, fog) so each act can be graded.
"""
import math
import os
import sys

import cv2
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared"))
from foxfolly.noise import fractal_noise  # noqa: E402

from rig import Light, c4, catmull, ellipse_path, mix, scl, tube  # noqa: E402

W, H = 1920, 1080


# =====================================================================
#                                LOOKS
# =====================================================================
def look(**kw):
    base = dict(zen=(0.1, 0.12, 0.25), mid=(0.3, 0.3, 0.4), hor=(0.8, 0.6, 0.5),
                sun=None, sun_rgb=(1, 0.8, 0.6), sun_r=40, sun_k=1.0, glow_k=1.0,
                ambient=(0.6, 0.6, 0.6), key=(1, 0.9, 0.8), key_dir=-2.4, rim=(1, 0.8, 0.6),
                rim_w=0.07, rim_k=0.9, fog=(0.7, 0.6, 0.55), fog_far=0.55, fog_mid=0.3,
                water=(0.25, 0.45, 0.45), stars=0.0, clouds=0.4, cloud_col=None,
                mist=0.4, mist_col=(0.9, 0.95, 0.9), plant=(0.30, 0.42, 0.22),
                shade=0.45)
    base.update(kw)
    return base


LOOKS = {
    "ink": look(zen=(0.004, 0.006, 0.02), mid=(0.012, 0.018, 0.05), hor=(0.03, 0.04, 0.09),
                ambient=(0.05, 0.06, 0.1), stars=1.0, clouds=0.0, mist=0.0, fog=(0.02, 0.03, 0.06)),
    "dawn": look(zen=(0.22, 0.30, 0.52), mid=(0.80, 0.58, 0.52), hor=(1.0, 0.76, 0.52),
                 sun=(300, 520), sun_rgb=(1.0, 0.78, 0.46), sun_r=34, ambient=(0.78, 0.66, 0.58),
                 key=(1.0, 0.8, 0.55), key_dir=-2.7, rim=(1.0, 0.78, 0.5), fog=(0.96, 0.80, 0.66),
                 fog_far=0.62, fog_mid=0.32, water=(0.30, 0.62, 0.60), clouds=0.5,
                 cloud_col=(1.0, 0.72, 0.6), mist=0.75, mist_col=(0.80, 0.98, 0.88),
                 plant=(0.28, 0.44, 0.24)),
    "morning": look(zen=(0.26, 0.44, 0.66), mid=(0.62, 0.72, 0.78), hor=(0.98, 0.88, 0.70),
                    sun=(360, 260), sun_rgb=(1.0, 0.9, 0.7), sun_r=30, ambient=(0.86, 0.80, 0.70),
                    key=(1.0, 0.9, 0.7), key_dir=-2.5, rim=(1.0, 0.9, 0.7), fog=(0.9, 0.9, 0.82),
                    fog_far=0.5, water=(0.26, 0.62, 0.64), clouds=0.4, mist=0.35,
                    mist_col=(0.85, 0.98, 0.9), plant=(0.30, 0.48, 0.24)),
    "midday": look(zen=(0.40, 0.56, 0.72), mid=(0.80, 0.84, 0.84), hor=(0.98, 0.96, 0.88),
                   sun=(1000, 60), sun_rgb=(1.0, 0.98, 0.9), sun_r=26, ambient=(0.98, 0.95, 0.86),
                   key=(1.0, 1.0, 0.94), key_dir=-1.7, rim=(1.0, 1.0, 0.95), rim_k=0.6,
                   fog=(0.97, 0.96, 0.9), fog_far=0.6, water=(0.5, 0.7, 0.72), clouds=0.15,
                   mist=0.0, plant=(0.40, 0.50, 0.28), shade=0.35),
    "fern": look(zen=(0.06, 0.10, 0.07), mid=(0.10, 0.16, 0.10), hor=(0.18, 0.26, 0.16),
                 sun=None, ambient=(0.34, 0.42, 0.32), key=(0.9, 1.0, 0.7), key_dir=-1.9,
                 rim=(0.75, 1.0, 0.55), rim_k=0.7, fog=(0.14, 0.22, 0.14), fog_far=0.7, fog_mid=0.45,
                 clouds=0.0, mist=0.25, mist_col=(0.45, 0.6, 0.4), plant=(0.14, 0.26, 0.12), shade=0.55),
    "golden": look(zen=(0.30, 0.30, 0.46), mid=(0.96, 0.62, 0.36), hor=(1.0, 0.80, 0.44),
                   sun=(1560, 600), sun_rgb=(1.0, 0.70, 0.30), sun_r=40, ambient=(0.62, 0.46, 0.36),
                   key=(1.0, 0.72, 0.38), key_dir=-0.25, rim=(1.0, 0.72, 0.36), rim_w=0.10, rim_k=1.2,
                   fog=(0.98, 0.70, 0.42), fog_far=0.65, water=(0.6, 0.45, 0.3), clouds=0.35,
                   cloud_col=(1.0, 0.6, 0.4), mist=0.2, mist_col=(1.0, 0.8, 0.6), plant=(0.30, 0.34, 0.16)),
    "dusk": look(zen=(0.10, 0.08, 0.26), mid=(0.46, 0.26, 0.44), hor=(0.98, 0.56, 0.52),
                 sun=None, ambient=(0.42, 0.34, 0.44), key=(1.0, 0.62, 0.55), key_dir=-2.9,
                 rim=(1.0, 0.64, 0.6), rim_k=0.8, fog=(0.60, 0.40, 0.52), fog_far=0.6,
                 water=(0.36, 0.26, 0.46), stars=0.25, clouds=0.4, cloud_col=(0.9, 0.5, 0.55),
                 mist=0.35, mist_col=(0.7, 0.55, 0.75), plant=(0.20, 0.24, 0.20)),
    "night": look(zen=(0.014, 0.022, 0.062), mid=(0.04, 0.06, 0.13), hor=(0.09, 0.12, 0.22),
                  sun=None, ambient=(0.30, 0.36, 0.56), key=(0.7, 0.8, 1.0), key_dir=-1.2,
                  rim=(0.55, 0.68, 1.0), rim_k=0.7, fog=(0.06, 0.09, 0.17), fog_far=0.6,
                  water=(0.06, 0.10, 0.20), stars=1.0, clouds=0.0, mist=0.25,
                  mist_col=(0.25, 0.32, 0.5), plant=(0.10, 0.14, 0.14)),
    "predawn": look(zen=(0.05, 0.08, 0.18), mid=(0.12, 0.18, 0.32), hor=(0.26, 0.34, 0.50),
                    ambient=(0.30, 0.36, 0.52), key=(0.7, 0.8, 1.0), key_dir=-1.5, rim=(0.6, 0.7, 1.0),
                    rim_k=0.5, fog=(0.18, 0.24, 0.38), water=(0.12, 0.18, 0.30), stars=0.5,
                    mist=0.35, mist_col=(0.4, 0.5, 0.7), plant=(0.12, 0.16, 0.18)),
    "flash": look(zen=(0.40, 0.38, 0.50), mid=(0.95, 0.86, 0.74), hor=(1.5, 1.4, 1.2),
                  sun=(1330, 575), sun_rgb=(1.5, 1.42, 1.25), sun_r=46, sun_k=2.0, glow_k=1.6,
                  ambient=(0.55, 0.50, 0.46), key=(1.3, 1.2, 1.0), key_dir=-0.35, rim=(1.5, 1.35, 1.05),
                  rim_w=0.12, rim_k=1.6, fog=(0.95, 0.88, 0.76), fog_far=0.45, fog_mid=0.2,
                  water=(0.85, 0.80, 0.70), stars=0.0, mist=0.35, mist_col=(1.0, 0.92, 0.8),
                  plant=(0.22, 0.26, 0.16), shade=0.6),
    "fire": look(zen=(0.20, 0.03, 0.02), mid=(0.72, 0.20, 0.06), hor=(1.0, 0.52, 0.16),
                 ambient=(0.62, 0.30, 0.18), key=(1.0, 0.5, 0.2), key_dir=-0.6, rim=(1.0, 0.45, 0.15),
                 rim_w=0.10, rim_k=1.3, fog=(0.55, 0.18, 0.08), fog_far=0.6, water=(0.5, 0.18, 0.08),
                 stars=0.0, clouds=0.6, cloud_col=(0.3, 0.06, 0.04), mist=0.3, mist_col=(0.6, 0.3, 0.2),
                 plant=(0.12, 0.08, 0.06)),
    "ash": look(zen=(0.50, 0.50, 0.50), mid=(0.62, 0.62, 0.61), hor=(0.72, 0.72, 0.70),
                ambient=(0.60, 0.60, 0.59), key=(0.7, 0.7, 0.7), key_dir=-1.6, rim=(0.7, 0.7, 0.7),
                rim_k=0.25, fog=(0.66, 0.66, 0.65), fog_far=0.7, fog_mid=0.45, water=(0.42, 0.42, 0.42),
                clouds=0.3, cloud_col=(0.5, 0.5, 0.5), mist=0.3, mist_col=(0.7, 0.7, 0.7),
                plant=(0.18, 0.18, 0.18), shade=0.3),
    "badlands": look(zen=(0.12, 0.16, 0.34), mid=(0.40, 0.42, 0.60), hor=(0.94, 0.66, 0.48),
                     ambient=(0.66, 0.56, 0.54), key=(1.0, 0.7, 0.5), key_dir=-2.8, rim=(1.0, 0.7, 0.5),
                     fog=(0.60, 0.52, 0.60), stars=0.2, clouds=0.3, cloud_col=(0.8, 0.5, 0.5), mist=0.0),
}


def blend_look(a, b, k):
    out = {}
    for key in a:
        va, vb = a[key], b.get(key, a[key])
        if isinstance(va, tuple) and isinstance(vb, tuple) and len(va) == len(vb):
            out[key] = tuple(va[i] + (vb[i] - va[i]) * k for i in range(len(va)))
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[key] = va + (vb - va) * k
        else:
            out[key] = vb if k > 0.5 else va
    return out


def light_of(lk, fog_k=0.0):
    return Light(ambient=lk["ambient"], key=lk["key"], key_dir=lk["key_dir"], rim=lk["rim"],
                 rim_w=lk["rim_w"], rim_k=lk["rim_k"], shade=lk["shade"], fog=lk["fog"], fog_k=fog_k)


# =====================================================================
#                            ASSET CACHE
# =====================================================================
class Cache:
    _inst = None

    def __init__(self):
        self.clouds = fractal_noise(256, 512, beta=2.6, seed=21)
        self.mist = self._mist()
        self.stars = self._stars()
        self.grain = None

    @classmethod
    def get(cls):
        if cls._inst is None:
            cls._inst = Cache()
        return cls._inst

    def _mist(self):
        n = fractal_noise(128, 512, beta=2.8, seed=77)
        n = cv2.resize(n, (int(W * 2), 300))
        y = np.linspace(-1, 1, 300, dtype=np.float32)[:, None]
        a = np.clip((n - 0.32) * 1.7, 0, 1) * np.exp(-(y / 0.55) ** 2)
        img = np.zeros((300, int(W * 2), 4), np.float16)
        img[..., 0] = img[..., 1] = img[..., 2] = img[..., 3] = a
        return skia.Image.fromarray(img, colorType=skia.kRGBA_F16_ColorType)

    def _stars(self):
        rng = np.random.default_rng(7)
        S = 3000
        img = np.zeros((S, S, 4), np.float32)
        band = cv2.resize(fractal_noise(S // 6, S // 6, beta=2.1, seed=8), (S, S))
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
        d = np.abs((yy - 0.42) - (xx - 0.5) * 0.7)
        mw = np.exp(-(d / 0.11) ** 2) * (0.25 + band) ** 2.2
        dust = np.clip(cv2.resize(fractal_noise(S // 6, S // 6, beta=1.6, seed=9), (S, S)) - 0.45, 0, 1) * 2
        mw = mw * (1 - 0.6 * dust * np.exp(-(d / 0.05) ** 2))  # dark dust lanes
        img[..., 0] = mw * 0.10
        img[..., 1] = mw * 0.10
        img[..., 2] = mw * 0.14
        n = 9000
        xs = rng.random(n) * S
        ys = rng.random(n) * S
        mags = rng.pareto(2.0, n) * 0.22 + 0.05
        dens = 1 + 3.0 * np.exp(-(np.abs((ys / S - 0.42) - (xs / S - 0.5) * 0.7) / 0.11) ** 2)
        for x, y, m, dd in zip(xs, ys, mags, dens):
            if rng.random() > 0.35 * dd:
                continue
            m = min(m, 2.5)
            r = 0.9 + min(m, 1.3) * 1.3
            x0, x1 = int(max(0, x - 4 * r)), int(min(S, x + 4 * r + 1))
            y0, y1 = int(max(0, y - 4 * r)), int(min(S, y + 4 * r + 1))
            gy, gx = np.mgrid[y0:y1, x0:x1]
            g = np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (2 * (r * 0.42) ** 2)) * m
            tint = (0.85 + 0.3 * rng.random(), 0.92, 1.0 + 0.25 * rng.random())
            for ch in range(3):
                img[y0:y1, x0:x1, ch] += g * tint[ch]
        img[..., 3] = 1.0
        return skia.Image.fromarray(np.clip(img, 0, 8).astype(np.float16), colorType=skia.kRGBA_F16_ColorType)


# =====================================================================
#                                 SKY
# =====================================================================
def sky(cv, lk, t, horizon=620.0, cam=(0, 0, 1)):
    sw, sh = 384, 216
    k = W / sw
    hy = horizon / k
    ys = np.arange(sh, dtype=np.float32)[:, None]
    xs = np.arange(sw, dtype=np.float32)[None, :]
    v = np.clip((hy - ys) / max(hy, 1), 0, 1)
    zen, mid, hor = (np.array(lk[c], np.float32) for c in ("zen", "mid", "hor"))
    a = np.clip(v / 0.35, 0, 1)[..., None]
    b = np.clip((v - 0.35) / 0.65, 0, 1)[..., None] ** 0.8
    col = hor * (1 - a) + mid * a
    col = col * (1 - b) + zen * b
    col = np.broadcast_to(col, (sh, sw, 3)).copy()
    if lk["sun"] is not None:
        sx, sy = lk["sun"][0] / k, lk["sun"][1] / k
        d = np.sqrt((xs - sx) ** 2 + (ys - sy) ** 2)
        g = (np.exp(-d / 30.0) * 0.45 + np.exp(-d / 8.0) * 0.7) * lk["glow_k"]
        band = np.exp(-((xs - sx) / 140.0) ** 2) * np.exp(-((ys - hy) / 26.0) ** 2) * 0.6 * lk["glow_k"]
        col += (g + band)[..., None] * np.array(lk["sun_rgb"], np.float32) * lk["sun_k"] * 0.6
    if lk["clouds"] > 0:
        cl = Cache.get().clouds
        off = t * 2.0
        yi = ys.astype(int) % cl.shape[0]
        ci = ((xs + off) % cl.shape[1]).astype(int)
        c = cl[yi, ci]
        dens = np.clip((c - 0.5) * 2.6, 0, 1) * np.exp(-((ys - (hy - 45)) / 42.0) ** 2) * lk["clouds"]
        cc = np.array(lk["cloud_col"] or lk["mid"], np.float32)
        col = col * (1 - dens[..., None] * 0.75) + cc * dens[..., None] * 0.75
    full = cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC)
    out = np.empty((H, W, 4), np.float16)
    out[..., :3] = full
    out[..., 3] = 1
    cv.drawImage(skia.Image.fromarray(out, colorType=skia.kRGBA_F16_ColorType), 0, 0)
    if lk["stars"] > 0:
        stars(cv, lk["stars"], t)
    if lk["sun"] is not None:
        sx, sy = lk["sun"]
        glow(cv, sx, sy, lk["sun_r"] * 6, lk["sun_rgb"], 0.35 * lk["sun_k"])
        cv.drawCircle(sx, sy, lk["sun_r"], skia.Paint(AntiAlias=True, Color4f=c4(scl(lk["sun_rgb"], 3.0 * lk["sun_k"]))))


def stars(cv, alpha, t, rot=0.0, cx=W * 0.5, cy=H * 0.35, scale=1.0):
    p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
    p.setAlphaf(min(1.0, alpha))
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(rot)
    cv.scale(scale, scale)
    cv.drawImage(Cache.get().stars, -1500, -1500, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    cv.restore()


def glow(cv, x, y, r, rgb, a):
    if a <= 0.002 or r <= 0:
        return
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                   Shader=skia.GradientShader.MakeRadial(
                       (x, y), r, [c4(rgb, a), c4(rgb, a * 0.3), c4(rgb, 0.0)], [0.0, 0.3, 1.0]))
    cv.drawCircle(x, y, r, p)


def the_star(cv, x, y, k, t):
    """The warm star. k: 0 (a tremble among thousands) .. 1 (casting shadows)."""
    tw = 1 + 0.08 * math.sin(t * 13.0) + 0.05 * math.sin(t * 7.3)
    col = (1.0, 0.86, 0.66)
    glow(cv, x, y, (30 + 520 * k * k) * tw, col, 0.10 + 0.35 * k)     # haze
    glow(cv, x, y, (8 + 60 * k) * tw, col, 0.5 + 0.4 * k)
    cv.drawCircle(x, y, 1.6 + 5 * k, skia.Paint(AntiAlias=True, Color4f=c4(scl(col, 3 + 4 * k))))
    if k > 0.4:  # faint diffraction spikes once it is brighter than any planet
        sp = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, StrokeWidth=1.2,
                        Style=skia.Paint.kStroke_Style)
        L = 40 + 160 * (k - 0.4)
        for a in (0, math.pi / 2):
            sp.setShader(skia.GradientShader.MakeLinear(
                [(x - L * math.cos(a), y - L * math.sin(a)), (x + L * math.cos(a), y + L * math.sin(a))],
                [c4(col, 0), c4(col, 0.5 * k), c4(col, 0)], [0, 0.5, 1]))
            cv.drawLine(x - L * math.cos(a), y - L * math.sin(a), x + L * math.cos(a), y + L * math.sin(a), sp)


# =====================================================================
#                          RIDGE, HILLS, SHORE
# =====================================================================
SADDLE_X = 1330.0


def ridge_path(base_y, amp, seed, saddle_x=SADDLE_X, saddle=True, x0=-400, x1=W + 400):
    n = fractal_noise(1, 1024, beta=3.0, seed=seed)[0]
    xs = np.linspace(x0, x1, 260)
    ys = base_y - amp * (np.interp(np.linspace(0, 1023, len(xs)), np.arange(1024), n) - 0.35) * 2.2
    if saddle:
        # the Saddle: two shoulders and a deep, clean notch between them
        sh = np.exp(-((xs - saddle_x + 95) / 70) ** 2) + np.exp(-((xs - saddle_x - 95) / 70) ** 2)
        ys -= 60 * sh
        ys += 95 * np.exp(-((xs - saddle_x) / 38) ** 2)
    p = skia.Path()
    p.moveTo(x0, H + 600)
    for x, y in zip(xs, ys):
        p.lineTo(float(x), float(y))
    p.lineTo(x1, H + 600)
    p.close()
    return p


def fill(cv, path, rgb, a=1.0):
    cv.drawPath(path, skia.Paint(AntiAlias=True, Color4f=c4(rgb, a)))


def vgrad(cv, path, top_y, bot_y, c_top, c_bot, a=1.0):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, top_y), (0, bot_y)], [c4(c_top, a), c4(c_bot, a)], [0, 1]))
    cv.drawPath(path, p)


def fogged(rgb, lk, k):
    return mix(rgb, lk["fog"], k)


# =====================================================================
#                                PLANTS
# =====================================================================
def wind(t, x, gust=1.0):
    return (0.6 * math.sin(t * 0.9 + x * 0.004) + 0.3 * math.sin(t * 2.1 + x * 0.011) +
            0.15 * math.sin(t * 5.3 + x * 0.03)) * gust


def fern(cv, x, y, size, rgb, t, seed=0, n_fronds=7, spread=1.0, gust=1.0, a=1.0, lean=0.0,
         burnt=0.0):
    """A fern clump: arching fronds with alternating pinnae, swaying in the wind.
    burnt: 0..1 fronds curl, blacken and lose pinnae (Act IV)."""
    rng = np.random.default_rng(seed)
    p = skia.Paint(AntiAlias=True)
    for f in range(n_fronds):
        base_ang = -math.pi / 2 + (f - (n_fronds - 1) / 2) / max(1, n_fronds - 1) * 1.9 * spread
        base_ang += (rng.random() - 0.5) * 0.3 + lean
        L = size * (0.7 + 0.5 * rng.random())
        droop = 0.9 + 0.5 * rng.random() + 0.8 * burnt
        sway = 0.10 * wind(t, x + f * 40, gust)
        col = scl(rgb, 0.75 + 0.35 * rng.random())
        col = mix(col, (0.04, 0.035, 0.03), burnt)
        p.setColor4f(c4(col, a))
        path = skia.Path()
        pts = []
        n = 16
        for i in range(n + 1):
            u = i / n
            ang = base_ang + (droop * u * u) * (1 if math.cos(base_ang) >= 0 else -1) + sway * u * u * 2
            if i == 0:
                px, py = x, y
            else:
                px = pts[-1][0] + math.cos(ang) * L / n
                py = pts[-1][1] + math.sin(ang) * L / n
            pts.append((px, py))
        # rachis
        rp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.0, size * 0.012),
                        Color4f=c4(scl(col, 0.8), a))
        rach = skia.Path()
        rach.moveTo(*pts[0])
        for q in pts[1:]:
            rach.lineTo(*q)
        cv.drawPath(rach, rp)
        if burnt > 0.85:
            continue
        for i in range(2, n):
            u = i / n
            px, py = pts[i]
            dx, dy = pts[i + 1][0] - px, pts[i + 1][1] - py
            dl = math.hypot(dx, dy) + 1e-6
            nx, ny = -dy / dl, dx / dl
            pl = L * 0.16 * math.sin(math.pi * min(1, u * 1.15)) * (1 - 0.6 * burnt)
            for side in (-1, 1):
                tipx = px + (nx * side * 0.9 + dx / dl * 0.45) * pl
                tipy = py + (ny * side * 0.9 + dy / dl * 0.45) * pl + pl * 0.25
                path.moveTo(px, py)
                path.quadTo(px + nx * side * pl * 0.5 - dy / dl * pl * 0.15 * side,
                            py + ny * side * pl * 0.5 + pl * 0.05, tipx, tipy)
                path.quadTo(px + nx * side * pl * 0.35 + dx / dl * pl * 0.5,
                            py + ny * side * pl * 0.35 + dy / dl * pl * 0.5, px + dx * 0.8, py + dy * 0.8)
                path.close()
        cv.drawPath(path, p)


def horsetail(cv, x, y, h, rgb, t, seed=0, a=1.0, burnt=0.0):
    rng = np.random.default_rng(seed)
    sway = 0.04 * wind(t, x)
    segs = 9
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    px, py = x, y
    col = mix(scl(rgb, 0.9 + 0.2 * rng.random()), (0.05, 0.05, 0.05), burnt)
    for i in range(segs):
        u = (i + 1) / segs
        nx = x + math.sin(sway * u * 6) * h * 0.2 * u
        ny = y - h * u
        p.setStrokeWidth(max(1.2, h * 0.018 * (1 - 0.5 * u)))
        p.setColor4f(c4(col, a))
        cv.drawLine(px, py, nx, ny, p)
        if burnt < 0.7 and i < segs - 1:  # whorl of needle leaves at each node
            p.setStrokeWidth(max(0.8, h * 0.006))
            for k in range(6):
                ang = -math.pi / 2 + (k - 2.5) * 0.45 + sway
                ll = h * 0.07 * (1 - u * 0.5)
                cv.drawLine(nx, ny, nx + math.cos(ang) * ll * 1.4, ny + math.sin(ang) * ll * 0.6 + ll * 0.5, p)
        px, py = nx, ny
    if burnt < 0.7:
        cv.drawOval(skia.Rect(px - h * 0.015, py - h * 0.05, px + h * 0.015, py),
                    skia.Paint(AntiAlias=True, Color4f=c4(scl(col, 0.8), a)))


def magnolia(cv, x, y, size, leaf_rgb, t, seed=0, a=1.0, flower=(0.98, 0.88, 0.86), lk=None, burnt=0.0):
    """Low magnolia shrub: glossy leaves and cupped white-pink flowers."""
    rng = np.random.default_rng(seed)
    p = skia.Paint(AntiAlias=True)
    for i in range(26):
        ang = -math.pi / 2 + (rng.random() - 0.5) * 2.6
        r = size * (0.25 + 0.6 * rng.random())
        sw = 0.05 * wind(t, x + i * 13)
        lx = x + math.cos(ang) * r * 1.2
        ly = y + math.sin(ang) * r * 0.8
        col = scl(leaf_rgb, 0.6 + 0.6 * rng.random())
        col = mix(col, (0.04, 0.04, 0.04), burnt)
        p.setColor4f(c4(col, a))
        if burnt > 0.9:
            continue
        cv.save()
        cv.translate(lx, ly)
        cv.rotate(math.degrees(ang + sw + rng.random() - 0.5))
        cv.drawOval(skia.Rect(-size * 0.02, -size * 0.07, size * 0.26, size * 0.07), p)
        cv.restore()
    if burnt > 0.3:
        return
    for i in range(5):
        ang = -math.pi / 2 + (rng.random() - 0.5) * 2.0
        r = size * (0.3 + 0.5 * rng.random())
        fx = x + math.cos(ang) * r + 3 * wind(t, x + i * 30)
        fy = y + math.sin(ang) * r * 0.7
        fs = size * (0.07 + 0.03 * rng.random())
        for k in range(6):
            pa = -math.pi / 2 + (k - 2.5) * 0.42
            pc = mix(flower, (0.95, 0.55, 0.62), 0.25 if k % 2 else 0.05)
            p.setColor4f(c4(pc, a))
            cv.save()
            cv.translate(fx, fy)
            cv.rotate(math.degrees(pa))
            cv.drawOval(skia.Rect(-fs * 0.28, -fs * 1.05, fs * 0.28, 0), p)
            cv.restore()


def conifer(cv, x, y, h, rgb, t, seed=0, a=1.0, burnt=0.0, bare=0.0):
    """Tall layered conifer silhouette (Cretaceous Metasequoia/araucaria feel)."""
    rng = np.random.default_rng(seed)
    p = skia.Paint(AntiAlias=True, Color4f=c4(mix(scl(rgb, 0.7), (0.03, 0.03, 0.03), burnt), a))
    tw = h * 0.02
    trunk = skia.Path()
    trunk.moveTo(x - tw, y)
    trunk.lineTo(x - tw * 0.3, y - h)
    trunk.lineTo(x + tw * 0.3, y - h)
    trunk.lineTo(x + tw, y)
    trunk.close()
    cv.drawPath(trunk, p)
    tiers = 9
    for i in range(tiers):
        u = i / tiers
        ty = y - h * (0.22 + 0.78 * u)
        wdt = h * 0.22 * (1 - u) ** 0.9 * (0.8 + 0.4 * rng.random())
        sw = 2 * wind(t, x) * u
        if bare > 0.5:
            if rng.random() < 0.5:
                continue
            bp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1, h * 0.006),
                            Color4f=c4((0.04, 0.04, 0.04), a))
            sd = -1 if rng.random() < 0.5 else 1
            cv.drawLine(x, ty, x + sd * wdt * (0.3 + 0.4 * rng.random()), ty + wdt * 0.2, bp)
            continue
        tier = catmull([(x - wdt + sw, ty + h * 0.05), (x - wdt * 0.4 + sw, ty - h * 0.03), (x + sw, ty - h * 0.07),
                        (x + wdt * 0.4 + sw, ty - h * 0.03), (x + wdt + sw, ty + h * 0.05), (x + sw, ty + h * 0.02)],
                       closed=True)
        p.setColor4f(c4(mix(scl(rgb, 0.65 + 0.3 * rng.random()), (0.03, 0.03, 0.03), burnt), a))
        cv.drawPath(tier, p)


def palm(cv, x, y, h, rgb, t, seed=0, a=1.0, burnt=0.0):
    rng = np.random.default_rng(seed)
    col = mix(rgb, (0.04, 0.04, 0.04), burnt)
    sw = wind(t, x) * 0.05
    top = (x + h * 0.12 + sw * h * 0.3, y - h)
    trunk = tube([(x, y), (x + h * 0.06, y - h * 0.5), top], [h * 0.035, h * 0.028, h * 0.022], n=16)
    fill(cv, trunk, scl(col, 0.8), a)
    if burnt > 0.8:
        return
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    for k in range(9):
        ang = -math.pi / 2 + (k - 4) * 0.36 + sw * 3 + (rng.random() - 0.5) * 0.1
        L = h * (0.38 + 0.12 * rng.random())
        pts = []
        for i in range(9):
            u = i / 8
            aa = ang + u * u * 1.2 * (1 if math.cos(ang) > 0 else -1)
            if i == 0:
                pts.append(top)
            else:
                pts.append((pts[-1][0] + math.cos(aa) * L / 8, pts[-1][1] + math.sin(aa) * L / 8))
        for i in range(1, 9):
            u = i / 8
            p.setStrokeWidth(max(1.0, h * 0.025 * math.sin(math.pi * u) + 1))
            p.setColor4f(c4(scl(col, 0.9 + 0.2 * rng.random()), a))
            cv.drawLine(*pts[i - 1], *pts[i], p)


def foliage(cv, x, y, w, h, col, t, seed=0, a=1.0, top=None, n=11):
    """Irregular layered foliage mass: overlapping blobs, lighter on top (sky light)."""
    rng = np.random.default_rng(seed)
    top = top or scl(col, 1.35)
    sw = 2.5 * wind(t, x)
    for i in range(n):
        u = rng.random()
        v = rng.random()
        bx = x + (u - 0.5) * w + sw * (1 - v)
        by = y + (v - 0.5) * h
        r = (0.18 + 0.2 * rng.random()) * max(w, h) * 0.6
        c = mix(col, top, (1 - v) * 0.8 * rng.random())
        cv.drawOval(skia.Rect(bx - r * 1.3, by - r * 0.7, bx + r * 1.3, by + r * 0.7),
                    skia.Paint(AntiAlias=True, Color4f=c4(c, a)))


# =====================================================================
#                             THE SPLIT TREE
# =====================================================================
def split_tree(cv, x, y, h, rgb, t, lk, char=0.0, knot=None, scale_leaf=1.0, a=1.0, detail=1.0):
    """Giant conifer split by lightning into a V. char: 0 alive .. 1 charred black and bare.
    knot: optional (u) to draw the treasure knot-hole; returns its position."""
    bark = mix(scl(rgb, 0.55), (0.02, 0.018, 0.016), char)
    inner = mix((0.55, 0.40, 0.28), (0.02, 0.02, 0.02), char)
    w0 = h * 0.11
    split_y = y - h * 0.38
    sw = wind(t, x) * 2
    L1 = [(x - w0 * 0.2, y), (x - w0 * 0.2, split_y), (x - h * 0.10 + sw, y - h * 0.75), (x - h * 0.16 + sw * 2, y - h * 1.2)]
    L2 = [(x + w0 * 0.2, y), (x + w0 * 0.2, split_y), (x + h * 0.12 + sw, y - h * 0.72), (x + h * 0.20 + sw * 2, y - h * 1.2)]
    left = tube(L1, [w0 * 0.55, w0 * 0.42, w0 * 0.30, w0 * 0.18], n=24)
    right = tube(L2, [w0 * 0.55, w0 * 0.40, w0 * 0.28, w0 * 0.16], n=24)
    base = catmull([(x - w0 * 1.3, y + 6), (x - w0 * 0.6, y - h * 0.05), (x - w0 * 0.5, y - h * 0.30),
                    (x + w0 * 0.5, y - h * 0.30), (x + w0 * 0.6, y - h * 0.05), (x + w0 * 1.4, y + 6)], closed=True)
    p = skia.Paint(AntiAlias=True, Color4f=c4(bark, a))
    # boughs behind the trunk (alive) or bare snags (charred)
    rng = np.random.default_rng(5)
    for side, pts in ((-1, L1), (1, L2)):
        for i in range(10 if detail > 0.5 else 6):
            u = 0.45 + 0.55 * i / 9
            bx = pts[1][0] + (pts[3][0] - pts[1][0]) * (u - 0.3) / 0.7
            by = y - h * (0.38 + 0.82 * (u - 0.3) / 0.7)
            ln = h * (0.16 + 0.08 * rng.random()) * (1.1 - u * 0.5)
            ang = (math.pi if side < 0 else 0) + side * (0.25 + 0.2 * rng.random()) * -1 + 0.03 * wind(t, bx + i * 20)
            ex, ey = bx + math.cos(ang) * ln, by + math.sin(ang) * ln * 0.35 + ln * 0.12
            if char < 0.5:
                bp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.5, h * 0.008),
                                Color4f=c4(bark, a))
                cv.drawLine(bx, by, ex, ey, bp)
                fc = mix(scl(lk["plant"], 0.5 + 0.25 * rng.random()), lk["fog"], 0.08)
                foliage(cv, (bx + ex) / 2 + math.cos(ang) * ln * 0.1, (by + ey) / 2, ln * 1.1, ln * 0.32, fc, t,
                        seed=int(i * 7 + (3 if side > 0 else 0)), a=a * max(0.0, 1 - 2 * char),
                        top=mix(fc, lk["key"], 0.35), n=9)
            else:
                if rng.random() < 0.45:
                    continue                      # many boughs burnt away entirely
                frac = 0.2 + 0.45 * rng.random()
                bp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.2, h * 0.007),
                                Color4f=c4(bark, a), StrokeCap=skia.Paint.kRound_Cap)
                mx_, my_ = bx + (ex - bx) * frac, by + (ey - by) * frac + ln * 0.08 * rng.random()
                cv.drawLine(bx, by, mx_, my_, bp)
                if rng.random() < 0.5:           # a crooked, broken twig
                    cv.drawLine(mx_, my_, mx_ + (ex - bx) * 0.12, my_ - ln * 0.07, bp)
    from rig import draw_form
    sil = skia.Op(skia.Op(left, right, skia.PathOp.kUnion_PathOp), base, skia.PathOp.kUnion_PathOp)
    L = light_of(lk)
    alb = tuple(bark[i] / max(0.05, L.ambient[i]) for i in range(3))
    draw_form(cv, [(sil, alb, 1.0)], L, sil=sil, texture=0.35, tex_scale=0.012 / max(0.3, h / 1180),
              size=w0 * 2.2, ao=False, rim_scale=0.8)
    # the pale, splintered heartwood inside the V
    v = catmull([(x - w0 * 0.25, split_y + h * 0.02), (x - h * 0.05, y - h * 0.55), (x, split_y - h * 0.03),
                 (x + h * 0.06, y - h * 0.55), (x + w0 * 0.25, split_y + h * 0.02)], closed=True)
    cv.drawPath(v, skia.Paint(AntiAlias=True, Color4f=c4(inner, 0.8 * a)))
    # bark furrows
    fp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1, h * 0.004),
                    Color4f=c4(scl(bark, 0.55), 0.8 * a))
    for k in range(7):
        ox = (k - 3) * w0 * 0.2
        cv.drawLine(x + ox, y, x + ox * 0.7, split_y + h * 0.02, fp)
    out = None
    if knot is not None:
        kx, ky = x + w0 * 0.15, y - h * knot
        cv.drawOval(skia.Rect(kx - w0 * 0.16, ky - w0 * 0.22, kx + w0 * 0.16, ky + w0 * 0.22),
                    skia.Paint(AntiAlias=True, Color4f=c4(scl(bark, 0.25), a)))
        rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.5, w0 * 0.05),
                         Color4f=c4(scl(bark, 1.5), a))
        cv.drawOval(skia.Rect(kx - w0 * 0.17, ky - w0 * 0.23, kx + w0 * 0.17, ky + w0 * 0.23), rim)
        out = (kx, ky, w0 * 0.16)
    return out


# =====================================================================
#                                WATER
# =====================================================================
def reflect(img, y0, y1, t, strength=0.8, tint=(0.3, 0.5, 0.5), ripple=1.0, src_y=None, surge=0.0):
    """Mirror everything above water line y0 into rows [y0, y1) with wave distortion.
    img: float32 HxWx3 (modified in place). src_y = reflection axis (defaults to y0)."""
    ax = y0 if src_y is None else src_y
    rows = np.arange(y0, min(y1, img.shape[0]))
    depth = (rows - y0) / max(1, (y1 - y0))
    Wi = img.shape[1]
    xs = np.arange(Wi, dtype=np.float32)
    out = np.empty((len(rows), Wi, 3), np.float32)
    for i, r in enumerate(rows):
        d = depth[i]
        amp = ripple * (1.5 + 10 * d) * (1 + 3 * surge)
        wav = amp * np.sin(xs * (0.03 + 0.02 * (1 - d)) + t * (1.4 + d) + r * 0.35)
        srow = int(np.clip(2 * ax - r - wav.mean() * 0 + amp * math.sin(t * 1.1 + r * 0.9) * 0.5, 0, ax - 1))
        sx = np.clip(xs + wav * 0.6, 0, Wi - 1).astype(np.int32)
        out[i] = img[srow, sx]
    tint = np.array(tint, np.float32)
    fres = (0.55 + 0.45 * (1 - depth))[:, None, None]
    img[y0:y0 + len(rows)] = out * strength * fres + tint * (1 - strength * fres) * 0.9
    return img


def water_glints(cv, y0, y1, t, rgb, a=0.6, n=160, seed=3, x0=0, x1=W):
    rng = np.random.default_rng(seed)
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, StrokeCap=skia.Paint.kRound_Cap,
                   Style=skia.Paint.kStroke_Style)
    for i in range(n):
        u = rng.random()
        y = y0 + (y1 - y0) * u ** 1.6
        x = x0 + rng.random() * (x1 - x0) + 20 * math.sin(t * 0.6 + i)
        tw = max(0.0, math.sin(t * (1.2 + rng.random() * 2) + i * 2.3)) ** 3
        L = 4 + 30 * u
        p.setStrokeWidth(1 + 2 * u)
        p.setColor4f(c4(rgb, a * tw))
        cv.drawLine(x - L, y, x + L, y, p)


def mist(cv, y, h, rgb, a, t, speed=6.0, x_off=0.0):
    if a <= 0.002:
        return
    img = Cache.get().mist
    p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix([rgb[0], 0, 0, 0, 0, 0, rgb[1], 0, 0, 0,
                                                         0, 0, rgb[2], 0, 0, 0, 0, 0, 1, 0]))
    p.setAlphaf(min(1.0, a))
    off = (t * speed + x_off) % (W * 0.9)
    cv.drawImageRect(img, skia.Rect(off, 0, off + W, 300), skia.Rect(0, y - h / 2, W, y + h / 2),
                     skia.SamplingOptions(skia.FilterMode.kLinear), p)


# =====================================================================
#                              PARTICLES
# =====================================================================
_R = np.random.default_rng(99)
FF = _R.random((70, 6))
DF = _R.random((8, 6))
ASH = _R.random((900, 5))
BEADS = _R.random((2600, 6))
EMB = _R.random((300, 5))


def fireflies(cv, t, a, x0=0, x1=W, y0=600, y1=1000, n=70, seed_off=0.0):
    if a <= 0:
        return
    for i, (p1, p2, p3, p4, p5, p6) in enumerate(FF[:n]):
        x = x0 + p1 * (x1 - x0) + 50 * math.sin(t * (0.2 + 0.2 * p2) + 6.28 * p3)
        y = y0 + p2 * (y1 - y0) + 25 * math.sin(t * (0.3 + 0.15 * p4) + 6.28 * p5)
        per = 2.5 + 4 * p4
        ph = ((t + p6 * per + seed_off) % per) / per
        bl = (min(1, ph / 0.15)) * max(0, 1 - max(0, ph - 0.25) / 0.3) if ph < 0.55 else 0
        glow(cv, x, y, 14 + 10 * p2, (0.95, 0.85, 0.35), a * bl * 0.7)
        glow(cv, x, y, 3, (1.0, 1.0, 0.8), a * bl)


def dragonfly(cv, x, y, t, s=1.0, col=(0.2, 0.55, 0.95), a=1.0, heading=0.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(heading))
    cv.scale(s, s)
    body = skia.Paint(AntiAlias=True, Color4f=c4(col, a))
    cv.drawRoundRect(skia.Rect(-14, -1.6, 12, 1.6), 1.6, 1.6, body)
    cv.drawCircle(13, 0, 2.6, body)
    wing = skia.Paint(AntiAlias=True, Color4f=c4((0.9, 0.95, 1.0), 0.35 * a))
    fl = math.sin(t * 90)
    for sx in (-1, 1):
        cv.save()
        cv.translate(4, 0)
        cv.scale(1, fl * sx)
        cv.drawOval(skia.Rect(-10, 0, 2, 12), wing)
        cv.drawOval(skia.Rect(-2, 0, 8, 10), wing)
        cv.restore()
    cv.restore()


def ash(cv, t, a, density=1.0, col=(0.85, 0.85, 0.84), wind_x=18.0, x0=0, x1=W, fall=38.0):
    if a <= 0:
        return
    n = int(len(ASH) * density)
    p = skia.Paint(AntiAlias=True)
    pb = skia.Paint(AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.6))
    for i, (p1, p2, p3, p4, p5) in enumerate(ASH[:n]):
        size = 1.2 + 4.5 * p3 ** 3
        spd = fall * (0.5 + p4)
        x = (p1 * (x1 - x0 + 400) + t * wind_x * (0.6 + p5) + 30 * math.sin(t * 0.7 + i)) % (x1 - x0 + 400) + x0 - 200
        y = (p2 * (H + 200) + t * spd) % (H + 200) - 100
        q = pb if size > 3 else p
        q.setColor4f(c4(col, a * (0.35 + 0.5 * p5)))
        cv.drawCircle(x, y, size, q)


def bead_shower(cv, t, t0, k, horizon=620, radiant=(1330, -380)):
    """Impact spherules re-entering: thousands of glowing streaks radiating from the
    south (like a meteor storm's radiant), with bright heads and the odd fireball."""
    if k <= 0:
        return []
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, StrokeCap=skia.Paint.kRound_Cap,
                   Style=skia.Paint.kStroke_Style)
    n = int(len(BEADS) * 0.5 * min(1.0, k))
    rx, ry = radiant
    for i, (p1, p2, p3, p4, p5, p6) in enumerate(BEADS[:n]):
        life = 0.45 + 0.9 * p3
        period = life + 0.4 + 2.0 * p6
        age = ((t - t0) + p4 * period) % period
        if age > life:
            continue
        u = age / life
        # born anywhere in the sky, streaking directly away from the radiant in the south
        bx = -200 + ((p1 + math.floor((t - t0 + p4 * period) / period) * 0.618) % 1.0) * (W + 400)
        by = -60 + p2 * (horizon + 250)
        ang = math.atan2(by - ry, bx - rx)
        speed = 700 + 1300 * p5
        x = bx + math.cos(ang) * speed * age
        y = by + math.sin(ang) * speed * age
        if y > horizon + 300 * p6:
            continue
        L = 50 + 190 * p5 ** 1.3
        dx, dy = math.cos(ang), math.sin(ang)
        heat = 1.0 - 0.5 * u
        col = (1.0, 0.72 * heat + 0.25, 0.30 * heat + 0.05)
        a = k * math.sin(math.pi * u) ** 0.7
        p.setStrokeWidth(0.9 + 2.4 * p5 ** 2)
        p.setShader(skia.GradientShader.MakeLinear(
            [(x - dx * L, y - dy * L), (x, y)], [c4(col, 0.0), c4(col, 0.9 * a)], [0, 1]))
        cv.drawLine(x - dx * L, y - dy * L, x, y, p)
        if p5 > 0.7:
            glow(cv, x, y, 5 + 14 * p5, (1.0, 0.85, 0.55), 0.6 * a)
        if p5 > 0.985:
            glow(cv, x, y, 70, (1.0, 0.6, 0.25), 0.5 * a)
            cv.drawCircle(x, y, 4, skia.Paint(AntiAlias=True, Color4f=c4((3, 2.6, 2), a)))
    return []


def flames(cv, x, y, w, h, t, a=1.0, seed=0):
    rng = np.random.default_rng(seed)
    for i in range(int(max(3, w / 18))):
        fx = x + (i + 0.5) / max(1, int(max(3, w / 18))) * w + 6 * math.sin(t * 7 + i)
        fh = h * (0.5 + 0.5 * abs(math.sin(t * (3 + rng.random() * 3) + i * 1.3)))
        fw = w / max(3, w / 18) * 0.8
        flame = catmull([(fx - fw, y), (fx - fw * 0.5, y - fh * 0.5), (fx + 4 * math.sin(t * 9 + i), y - fh),
                         (fx + fw * 0.5, y - fh * 0.45), (fx + fw, y)], closed=True)
        cv.drawPath(flame, skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Shader=skia.GradientShader.MakeLinear(
            [(0, y), (0, y - fh)], [c4((1.0, 0.8, 0.3), a), c4((1.0, 0.35, 0.05), a * 0.6), c4((0.6, 0.1, 0.0), 0)],
            [0, 0.5, 1])))
        glow(cv, fx, y - fh * 0.3, fh * 0.9, (1.0, 0.45, 0.1), 0.25 * a)


def steam(cv, x, y, age, a=1.0, s=1.0):
    if age < 0 or age > 2.5:
        return
    r = (10 + 60 * age) * s
    al = a * (1 - age / 2.5) * 0.5
    p = skia.Paint(AntiAlias=True, Color4f=c4((0.95, 0.85, 0.8), al),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.5))
    cv.drawCircle(x, y - 30 * age * s, r, p)
