"""ACT IV — AFTER (S23–S26)."""
import math

import cv2
import numpy as np
import skia

import timeline as TL
import world as Wd
from creatures import burrower
from foxfolly.anim import Track, clamp, ease_in_out_sine, smoothstep, window
from foxfolly.noise import fractal_noise
from frame import Frame
from rig import Light, c4, mix, scl
from shotkit import CAMP, SHORE, Cam, camp_bg, lake, lake_foreground, mound, shore
from shots_act1 import blinks
from world import LOOKS, W, H, blend_look, light_of

EV = TL.EV
_DRAIN = None


def drain_field(h, w):
    global _DRAIN
    if _DRAIN is None or _DRAIN.shape != (h, w):
        n = cv2.resize(fractal_noise(135, 240, beta=2.4, seed=404), (w, h))
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        # regions drain in blotches, sky first, the foreground last (as the ash falls through it)
        _DRAIN = (0.55 * n + 0.45 * (1 - yy)).astype(np.float32)
        _DRAIN = (_DRAIN - _DRAIN.min()) / (_DRAIN.max() - _DRAIN.min())
    return _DRAIN


def S23(F, u, dur, t):
    """White slowly fades to grey. Silence, then wind. Ash falls like snow."""
    k = ease_in_out_sine(clamp(u / 4.2))
    col = mix((1.0, 0.985, 0.96), (0.50, 0.50, 0.50), k)
    F.cv.clear(skia.Color4f(*col, 1))
    Wd.ash(F.cv, t, smoothstep(226.0, 229.0, t), density=0.6, col=(0.32, 0.32, 0.32), wind_x=10, fall=30)
    F.post = {"grade": "act4", "bloom": (0.9, 0.1), "vignette": 0.25 * k}


def S24(F, u, dur, t):
    """THE LAKE — after. The exact dawn frame drains, region by region, into ash."""
    ta = 22.0 + u                                    # the S3 world, still alive, still moving
    lk_a = dict(LOOKS["dawn"])
    lk_a["sun"] = (230, 610 - 110 * ease_in_out_sine(clamp((ta - 18.5) / 9.0)))
    lk_a["sun_k"] = 0.35 + 0.65 * smoothstep(EV["sun_crest"] - 1.0, EV["sun_crest"] + 1.5, ta)
    k = smoothstep(231.2, 239.6, t)
    A = None
    if k < 0.999:
        A = Frame(ta, F.s)
        st = {"herd": "drink", "dflies": True, "oh": "lying", "azhd": None,
              "oh_pose": {"crouch": 1.0, "breath": ta, "head_pitch": 0.12}, "wi_pose": {"t": ta, "curl": 1.0, "crouch": 1.0}}
        lake(A, ta, lk_a, st)
        lake_foreground(A, ta, lk_a, st)
    stb = {"after": 1.0, "herd": None, "oh": "mound"}
    lake(F, t, LOOKS["ash"], stb)
    lake_foreground(F, t, LOOKS["ash"], stb)
    if A is not None:
        a = A.snapshot()
        b = F.snapshot()
        field = drain_field(a.shape[0], a.shape[1])
        thr = 1.15 - 1.3 * k
        m = np.clip((thr - field) / 0.12 + 0.5, 0, 1)[..., None]   # 1 = still alive (high field dies first)
        # the front of the drain carries a haze of grey ash
        front = np.exp(-((field - thr) / 0.07) ** 2)[..., None] * (0.35 if k > 0 else 0)
        img = a * m + b * (1 - m)
        img = img * (1 - front) + np.array([0.6, 0.6, 0.6], np.float32) * front
        F.put(img)
    Wd.ash(F.cv, t, 0.6 + 0.4 * window(t, 231.0, 240.0, 1.5, 2.0), density=0.5 + 0.5 * window(t, 231, 240, 1.5, 2),
           col=(0.8, 0.8, 0.79), wind_x=14, fall=36)
    F.post = {"grade": "act1", "grade_mix": ("act4", k), "bloom": (0.62, 0.5 * (1 - k) + 0.15), "vignette": 0.35}


def S25(F, u, dur, t):
    """A slow push under the charred tree toward a mound shaped like a sleeping Triceratops."""
    lk = LOOKS["ash"]
    e = ease_in_out_sine(clamp(u / 6.0))
    cam = Cam(960 + 120 * e, 780 + 110 * e, 1.05 + 0.85 * e)
    camp_bg(F, t, lk, cam, {"after": 1.0, "char": 1.0})
    cv = F.cv
    from shotkit import ash_mound
    ash_mound(F, cam, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], lk)
    Wd.ash(cv, t, 0.9, density=0.7, col=(0.82, 0.82, 0.81), wind_x=12, fall=34)
    F.post = {"grade": "act4", "bloom": (0.8, 0.15), "vignette": 0.4}


def S26(F, u, dur, t):
    """Among the burnt roots the Burrower pushes out, sniffs the grey air, and blinks. Alive."""
    lk = LOOKS["ash"]
    L = light_of(lk)
    cam = Cam(300, 870, 3.4)
    bx, by = SHORE["burrow"]
    peek = ease_in_out_sine(clamp((t - 249.0) / 1.0))
    out = ease_in_out_sine(clamp((t - 250.3) / 1.2))
    sniff = window(t, 251.0, 253.2, 0.3, 0.5)

    def front(cv):
        cv.save()
        if out < 0.5:
            cv.clipRect(skia.Rect(bx - 60, by - 60, bx + 60, by + 4))
        bl = 1.0 if (252.8 < t < 252.98 or 253.3 < t < 253.46) else 0.0
        Lb = Light(ambient=(0.85, 0.85, 0.84), key=(1, 1, 1), key_dir=-1.8, rim=(1, 1, 1), rim_k=0.6)
        burrower(cv, {"t": t, "sniff": sniff, "run": 0.0}, Lb, bx + 18 - 40 * out, by + 18 - 16 * peek - 4 * out, 1.2, -1)
        if bl > 0:
            ex, ey = bx + 18 - 40 * out - 24, by + 18 - 16 * peek - 4 * out - 18
            cv.drawCircle(ex, ey, 3.2, skia.Paint(AntiAlias=True, Color4f=c4(L.base((0.40, 0.30, 0.22)))))
        cv.restore()
        cv.drawOval(skia.Rect(bx - 30, by + 2, bx + 30, by + 14), skia.Paint(AntiAlias=True, Color4f=c4((0.1, 0.1, 0.1))))

    shore(F, t, lk, cam, {"after": 1.0, "char": 1.0}, draw_front=front)
    Wd.ash(F.cv, t, 0.7, density=0.5, col=(0.82, 0.82, 0.81), wind_x=8, fall=28)
    F.post = {"grade": "act4", "bloom": (0.8, 0.15), "vignette": 0.45}


SHOTS = {"S23": S23, "S24": S24, "S25": S25, "S26": S26}
