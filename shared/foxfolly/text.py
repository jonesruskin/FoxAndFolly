"""Channel typography: soft-glow italic serif narration rendered with Skia.

Text is rasterised once per (string, style) into a premultiplied float RGBA
sprite and cached; each frame only alpha-composites it, so fades are cheap
and perfectly smooth.
"""
import os

import numpy as np
import skia

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
_TF = {}


def typeface(name="CormorantGaramond-Italic.ttf"):
    if name not in _TF:
        _TF[name] = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, name))
    return _TF[name]


def _wrap(font, text, max_w):
    """Fit text in max_w; if it must break, balance the lines (no orphans)."""
    if font.measureText(text) <= max_w:
        return [text]
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wmax = max(font.measureText(a), font.measureText(b))
        if wmax <= max_w and (best is None or wmax < best[0]):
            best = (wmax, [a, b])
    if best:
        return best[1]
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if font.measureText(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def render_text_sprite(text, size=56, face="CormorantGaramond-Italic.ttf",
                       color=(0.96, 0.92, 0.85), glow=(1.0, 0.85, 0.6),
                       glow_alpha=0.18, shadow_alpha=0.75, max_width=1560,
                       letter_spacing=0.0, line_gap=1.25):
    """Return (rgba_premultiplied_float32 [h,w,4], anchor_x, anchor_y).

    anchor = centre of the text block, in sprite pixels.
    """
    font = skia.Font(typeface(face), size)
    font.setSubpixel(True)
    font.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    font.setEdging(skia.Font.Edging.kAntiAlias)
    lines = _wrap(font, text, max_width)
    widths = [font.measureText(l) + letter_spacing * max(0, len(l) - 1) for l in lines]
    lh = size * line_gap
    pad = int(size * 1.2)
    w = int(max(widths) + 2 * pad)
    h = int(lh * len(lines) + 2 * pad)
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    metrics = font.getMetrics()
    asc = -metrics.fAscent

    def draw(paint):
        for i, (l, lw) in enumerate(zip(lines, widths)):
            x = (w - lw) / 2
            y = pad + i * lh + (lh - size) / 2 + asc * 0.92
            if letter_spacing:
                for ch in l:
                    c.drawString(ch, x, y, font, paint)
                    x += font.measureText(ch) + letter_spacing
            else:
                c.drawString(l, x, y, font, paint)

    # 1) wide soft dark shadow for legibility over any background
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(0, 0, 0, shadow_alpha).toColor(),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.22))
    draw(p)
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(0, 0, 0, shadow_alpha * 0.6).toColor(),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.06))
    draw(p)
    # 2) faint warm glow
    if glow_alpha > 0:
        p = skia.Paint(AntiAlias=True, Color=skia.Color4f(*glow, glow_alpha).toColor(),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.35))
        draw(p)
    # 3) the letters
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(*color, 1.0).toColor())
    draw(p)
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType,
                                           alphaType=skia.kPremul_AlphaType)
    rgba = arr.astype(np.float32) / 255.0
    return rgba, w / 2, h / 2


class TextCache:
    def __init__(self):
        self._c = {}

    def get(self, text, **style):
        key = (text, tuple(sorted(style.items())))
        if key not in self._c:
            self._c[key] = render_text_sprite(text, **style)
        return self._c[key]


def composite(frame, sprite, cx, cy, alpha):
    """Alpha-composite a premultiplied sprite centred at (cx, cy)."""
    if alpha <= 0.001:
        return frame
    rgba, ax, ay = sprite
    sh, sw = rgba.shape[:2]
    x0 = int(round(cx - ax))
    y0 = int(round(cy - ay))
    H, W = frame.shape[:2]
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + sw), min(H, y0 + sh)
    if fx1 <= fx0 or fy1 <= fy0:
        return frame
    s = rgba[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0] * alpha
    region = frame[fy0:fy1, fx0:fx1]
    frame[fy0:fy1, fx0:fx1] = region * (1 - s[..., 3:4]) + s[..., :3]
    return frame
