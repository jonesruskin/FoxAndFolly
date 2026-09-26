"""COLD OPEN (S1–S2)."""
import math

import skia

import timeline as TL
import world as Wd
from foxfolly.anim import ease_in_out_sine, clamp, smoothstep
from world import LOOKS


def S01(F, u, dur, t):
    F.cv.clear(skia.Color4f(0, 0, 0, 1))
    F.post = {"grade": "cold_open", "bloom": (0.9, 0.0), "vignette": 0.0, "grain": 0.012}


def S02(F, u, dur, t):
    """A slow drift through the ancient night sky that settles on one warm star."""
    cv = F.cv
    lk = LOOKS["ink"]
    Wd.sky(cv, dict(lk, stars=0.0), t, horizon=1400)
    k = ease_in_out_sine(clamp(u / 8.5))
    fade = smoothstep(0.0, 2.0, u)
    # drift: rotate + push in; the warm star is placed so it arrives near frame centre
    Wd.stars(cv, fade * 1.1, t, rot=6 - 4 * k, cx=W2 - 380 * (1 - k) + 60, cy=H2 + 120 * (1 - k) - 40, scale=1.0 + 0.35 * k)
    sx, sy = W2 + 60 + 20 * (1 - k), H2 - 40 + 30 * (1 - k)
    tone = smoothstep(TL.EV["star_tone"] - 7.0 - 0.5, TL.EV["star_tone"] - 7.0 + 1.5, u)  # brightens as its tone enters
    Wd.the_star(cv, sx, sy, (0.08 + 0.05 * tone) * fade, t)
    F.post = {"grade": "cold_open", "bloom": (0.5, 0.6), "vignette": 0.5, "black": 1 - smoothstep(0.0, 1.6, u)}


W2, H2 = Wd.W / 2, Wd.H / 2
SHOTS = {"S01": S01, "S02": S02}
