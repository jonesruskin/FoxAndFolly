"""Timing helpers: easing curves and keyframe tracks.

Every animated value in a Fox & Folly video should come from one of these,
never from raw linear interpolation, so motion always starts and ends softly.
"""
import math

import numpy as np
from scipy.interpolate import PchipInterpolator


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, x):
    return a + (b - a) * x


def smoothstep(e0, e1, x):
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    x = clamp((x - e0) / (e1 - e0))
    return x * x * (3 - 2 * x)


def smootherstep(e0, e1, x):
    x = clamp((x - e0) / (e1 - e0)) if e1 != e0 else float(x >= e1)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_in_out_sine(x):
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp(x)
    return x ** 3


def window(t, t0, t1, fade_in, fade_out=None):
    """0→1→0 envelope: rises over fade_in after t0, falls over fade_out before t1."""
    if fade_out is None:
        fade_out = fade_in
    return smoothstep(t0, t0 + fade_in, t) * (1.0 - smoothstep(t1 - fade_out, t1, t))


class Track:
    """Keyframed value.

    mode="pchip": smooth, monotone-preserving curve through all keys (C1).
                  Repeated values produce clean holds; no overshoot.
    mode="ease":  each segment eased in-out (velocity 0 at every key).
    Values may be scalars or equal-length tuples.
    """

    def __init__(self, keys, mode="pchip"):
        keys = sorted(keys, key=lambda k: k[0])
        self.t = np.array([k[0] for k in keys], dtype=float)
        v = np.array([np.atleast_1d(k[1]) for k in keys], dtype=float)
        self.v = v
        self.scalar = np.ndim(keys[0][1]) == 0
        self.mode = mode
        if mode == "pchip" and len(keys) >= 2:
            self._f = PchipInterpolator(self.t, v, axis=0, extrapolate=False)

    def __call__(self, t):
        if t <= self.t[0]:
            out = self.v[0]
        elif t >= self.t[-1]:
            out = self.v[-1]
        elif self.mode == "pchip":
            out = self._f(t)
        else:
            i = int(np.searchsorted(self.t, t) - 1)
            x = (t - self.t[i]) / (self.t[i + 1] - self.t[i])
            out = self.v[i] + (self.v[i + 1] - self.v[i]) * ease_in_out_sine(x)
        return float(out[0]) if self.scalar else tuple(float(a) for a in out)
