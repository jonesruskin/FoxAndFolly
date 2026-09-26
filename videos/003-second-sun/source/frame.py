"""Frame canvas + compositing helpers + post stack for SECOND SUN."""
import math
import os
import sys
from contextlib import contextmanager

import cv2
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "shared"))
from foxfolly import post  # noqa: E402

W, H = 1920, 1080


class Frame:
    """A float16 Skia canvas in 1920x1080 design units (scale < 1 for animatics)."""

    def __init__(self, t, scale=1.0):
        self.t = t
        self.s = scale
        self.w, self.h = int(W * scale), int(H * scale)
        self.surf = self._new()
        self.cv = self.surf.getCanvas()
        self.cv.scale(scale, scale)
        self.post = {}

    def _new(self):
        info = skia.ImageInfo.Make(self.w, self.h, skia.kRGBA_F16_ColorType, skia.kPremul_AlphaType)
        return skia.Surface.MakeRaster(info)

    def snapshot(self):
        a = self.surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_F16_ColorType)
        return a[..., :3].astype(np.float32)

    def put(self, img):
        a = np.empty((self.h, self.w, 4), np.float16)
        a[..., :3] = img
        a[..., 3] = 1
        self.cv.save()
        self.cv.resetMatrix()
        self.cv.clear(skia.ColorBLACK)
        self.cv.drawImage(skia.Image.fromarray(a, colorType=skia.kRGBA_F16_ColorType), 0, 0)
        self.cv.restore()

    def defocus(self, sigma):
        """Blur everything drawn so far (depth of field for the background)."""
        if sigma <= 0.3:
            return
        img = self.snapshot()
        sg = sigma * self.s
        if sg > 6:
            f = 4
            small = cv2.resize(img, (self.w // f, self.h // f), interpolation=cv2.INTER_AREA)
            img = cv2.resize(cv2.GaussianBlur(small, (0, 0), sg / f), (self.w, self.h))
        else:
            img = cv2.GaussianBlur(img, (0, 0), sg)
        self.put(img)

    def process(self, fn):
        """Apply a numpy function to what has been drawn so far."""
        self.put(fn(self.snapshot()))

    @contextmanager
    def layer(self, blur=0.0, alpha=1.0, blend=None, color_filter=None):
        """Draw into a separate transparent layer, optionally blurred (foreground DOF)."""
        surf = self._new()
        cv = surf.getCanvas()
        cv.clear(skia.ColorTRANSPARENT)
        cv.scale(self.s, self.s)
        yield cv
        img = surf.makeImageSnapshot()
        p = skia.Paint()
        p.setAlphaf(alpha)
        if blend is not None:
            p.setBlendMode(blend)
        if color_filter is not None:
            p.setColorFilter(color_filter)
        if blur > 0.3:
            p.setImageFilter(skia.ImageFilters.Blur(blur * self.s, blur * self.s))
        self.cv.save()
        self.cv.resetMatrix()
        self.cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        self.cv.restore()


# ------------------------------------------------------------------ post
GRADES = {
    # lift (rgb), gain (rgb), gamma, saturation, warm
    "cold_open": ((0.006, 0.008, 0.02), (1.0, 1.0, 1.05), 1.0, 1.0, 0.0),
    "act1": ((0.020, 0.018, 0.022), (1.03, 1.0, 0.95), 1.02, 1.08, 0.5),
    "act2": ((0.012, 0.016, 0.012), (1.0, 1.0, 0.97), 1.0, 1.02, 0.3),
    "act2_gold": ((0.02, 0.012, 0.01), (1.06, 0.98, 0.88), 1.0, 1.1, 0.8),
    "act3_dusk": ((0.018, 0.012, 0.03), (1.0, 0.96, 1.02), 1.0, 1.05, 0.3),
    "act3_night": ((0.008, 0.012, 0.03), (0.95, 1.0, 1.08), 1.0, 1.0, 0.0),
    "act3_flash": ((0.03, 0.028, 0.02), (1.0, 0.98, 0.92), 1.0, 0.9, 0.6),
    "act3_fire": ((0.02, 0.005, 0.0), (1.08, 0.92, 0.8), 1.0, 1.15, 0.5),
    "act4": ((0.03, 0.03, 0.03), (1.0, 1.0, 1.0), 1.0, 0.08, 0.0),
    "epi_bad": ((0.02, 0.015, 0.025), (1.03, 0.98, 0.95), 1.0, 1.0, 0.4),
    "epi_museum": ((0.015, 0.01, 0.005), (1.05, 0.97, 0.86), 1.0, 0.95, 0.6),
}


def finish(img, P, frame_idx, t):
    """Post stack. P keys: rays (x, y, k), bloom (thr, k), grade (name or tuple),
    grade_mix ((name_b, k)), shake (px), heat (k), pov (0..1 blur + bloom), white (0..1),
    black (0..1), vignette, grain, sat_override."""
    h, w = img.shape[:2]
    s = w / W
    if "rays" in P and P["rays"][2] > 0.01:
        x, y, k = P["rays"]
        img = post.god_rays(img, (x * s, y * s), strength=k, threshold=P.get("ray_thr", 0.55))
    if P.get("heat", 0) > 0:
        k = P["heat"]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dx = (np.sin(yy * 0.07 + t * 9) * 1.2 + np.sin(yy * 0.023 - t * 5) * 1.6) * k * s
        dy = np.sin(xx * 0.05 + t * 7) * 0.8 * k * s
        img = cv2.remap(img, xx + dx, yy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if P.get("pov", 0) > 0:
        k = P["pov"]
        small = cv2.resize(img, (w // 8, h // 8), interpolation=cv2.INTER_AREA)
        blur = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3.5 * k + 0.5), (w, h))
        img = img * (1 - k) + blur * k
    thr, bk = P.get("bloom", (0.62, 0.5))
    img = post.bloom(img, threshold=thr, strength=bk)
    g = P.get("grade", "act1")
    ga = GRADES[g] if isinstance(g, str) else g
    if "grade_mix" in P:
        gb, gk = P["grade_mix"]
        gb = GRADES[gb]
        ga = tuple(tuple(ga[i][j] + (gb[i][j] - ga[i][j]) * gk for j in range(3)) if isinstance(ga[i], tuple)
                   else ga[i] + (gb[i] - ga[i]) * gk for i in range(5))
    lift, gain, gamma, sat, warm = ga
    img = post.grade(img, lift=lift, gain=gain, gamma=gamma, saturation=sat, warm_highlights=warm)
    img = post.vignette(img, amount=P.get("vignette", 0.38))
    if P.get("shake", 0) > 0:
        a = P["shake"] * s
        dx = a * (math.sin(t * 37) * 0.6 + math.sin(t * 61) * 0.4)
        dy = a * (math.sin(t * 43 + 1) * 0.6 + math.sin(t * 71) * 0.4)
        m = np.float32([[1.02, 0, dx - w * 0.01], [0, 1.02, dy - h * 0.01]])
        img = cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REFLECT)
    if P.get("white", 0) > 0:
        img = img * (1 - P["white"]) + P["white"] * np.array(P.get("white_col", (1, 1, 1)), np.float32)
    if P.get("black", 0) > 0:
        img = img * (1 - P["black"])
    return img


def to_uint8(img, frame_idx, grain=0.02):
    img = post.grain(img, frame_idx, amount=grain)
    return post.to_uint8(img, frame_idx)
