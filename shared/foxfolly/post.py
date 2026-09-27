"""Cinematic post-processing for float32 RGB frames in [0, 1+].

Order used by the channel look:
    god_rays -> bloom -> grade -> vignette -> (text) -> grain -> to_uint8
"""
import cv2
import numpy as np


def _down(img, f):
    h, w = img.shape[:2]
    return cv2.resize(img, (w // f, h // f), interpolation=cv2.INTER_AREA)


def _up(img, w, h):
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)


def bloom(img, threshold=0.55, strength=0.6, radius=1.0):
    """Multi-scale soft bloom. Brighter-than-threshold light bleeds outward."""
    h, w = img.shape[:2]
    small = _down(img, 4)
    lum = small.max(axis=2, keepdims=True)
    knee = np.clip((lum - threshold) / max(1e-4, 1 - threshold), 0, None)
    bright = small * (knee / np.maximum(lum, 1e-4))
    acc = np.zeros_like(bright)
    for sigma, wgt in ((4, 0.5), (12, 0.35), (32, 0.25)):
        acc += cv2.GaussianBlur(bright, (0, 0), sigma * radius) * wgt
    return img + _up(acc, w, h) * strength


def god_rays(img, sun_xy, strength=0.5, decay=0.965, samples=36, length=0.55,
             threshold=0.6):
    """Screen-space crepuscular rays radiating from sun_xy (pixels).

    Bright sky showing between occluders is smeared toward/away from the sun,
    which gives volumetric-looking shafts through the flowers.
    """
    if strength <= 0:
        return img
    h, w = img.shape[:2]
    f = 4
    small = _down(img, f)
    lum = small.mean(axis=2, keepdims=True)
    src = small * np.clip((lum - threshold) * 3.0, 0, 1)
    cx, cy = sun_xy[0] / f, sun_xy[1] / f
    acc = np.zeros_like(src)
    wsum = 0.0
    wt = 1.0
    for i in range(samples):
        s = 1.0 - length * i / samples
        m = np.array([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]], np.float32)
        # sample the source "closer to the sun" for every pixel
        acc += cv2.warpAffine(src, m, (small.shape[1], small.shape[0]),
                              flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_CONSTANT) * wt
        wsum += wt
        wt *= decay
    acc /= wsum
    acc = cv2.GaussianBlur(acc, (0, 0), 1.5)
    return img + _up(acc, w, h) * strength


def grade(img, lift=(0.012, 0.016, 0.03), gain=(1.0, 1.0, 1.0), gamma=1.0,
          saturation=1.0, warm_highlights=0.0):
    """Lift/gamma/gain with gentle split toning. Tone-maps highlights softly."""
    out = img * np.array(gain, np.float32)
    # soft, hue-preserving shoulder so bright colours never clip to lemon/white
    lum = out.max(axis=2, keepdims=True)
    over = np.maximum(lum - 0.75, 0)
    comp = np.where(lum > 0.75, 0.75 + over / (1.0 + over * 2.2), lum)
    out = out * (comp / np.maximum(lum, 1e-5))
    if saturation != 1.0:
        lum = (out * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(2, keepdims=True)
        out = lum + (out - lum) * saturation
    if warm_highlights:
        lum = out.mean(2, keepdims=True)
        out = out + warm_highlights * lum * lum * np.array([0.06, 0.02, -0.05], np.float32)
    if gamma != 1.0:
        out = np.power(np.clip(out, 0, None), 1.0 / gamma)
    lift = np.array(lift, np.float32)
    out = lift + out * (1 - lift)
    return out


_VIG = {}


def vignette(img, amount=0.35, softness=0.9):
    h, w = img.shape[:2]
    key = (h, w, amount, softness)
    if key not in _VIG:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (x - w / 2) / (w / 2)
        ny = (y - h / 2) / (h / 2)
        r = np.sqrt(nx * nx * 0.85 + ny * ny)
        v = 1 - amount * np.clip((r - (1 - softness)) / softness, 0, 1) ** 2
        _VIG[key] = v[..., None].astype(np.float32)
    return img * _VIG[key]


def grain(img, frame, amount=0.018, seed=1234):
    """Luminance film grain, slightly soft, fresh every frame (also dithers)."""
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed + frame * 7919)
    g = rng.standard_normal((h // 2, w // 2)).astype(np.float32)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
    # grain is strongest in the midtones, like film
    lum = img.mean(2, keepdims=True)
    k = amount * (0.35 + 1.3 * lum * (1.0 - np.clip(lum, 0, 1)))
    return img + g[..., None] * k


def to_uint8(img, frame=0):
    """Quantise with triangular dither to avoid banding in dark gradients."""
    h, w = img.shape[:2]
    rng = np.random.default_rng(99 + frame)
    d = (rng.random((h, w, 1), dtype=np.float32) - rng.random((h, w, 1), dtype=np.float32))
    return np.clip(img * 255.0 + d, 0, 255).astype(np.uint8)
