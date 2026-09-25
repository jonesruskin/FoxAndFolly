"""Procedural sunflowers drawn with Skia.

A flower head is a planar disc (florets + petal rings) placed in 3D by its
yaw (turn east/west) and pitch (tilt up/down), then projected orthographically.
A planar figure projects to an exact affine map, so Skia can draw the petals
and the floret texture directly in the head's local coordinates.

The florets use the real sunflower arrangement: floret k sits at radius
c*sqrt(k) and angle k * 137.508 deg (the golden angle), which produces the
Fibonacci spirals seen on real sunflower heads.
"""
import math

import numpy as np
import skia

GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))  # 137.508 degrees

# albedo palette
PETAL = (1.00, 0.70, 0.10)
PETAL_BACK = (0.86, 0.50, 0.07)
STEM = (0.30, 0.46, 0.17)
LEAF = (0.24, 0.42, 0.13)
LEAF_DARK = (0.15, 0.29, 0.09)
CALYX = (0.25, 0.38, 0.13)
RIM = (0.30, 0.20, 0.07)


def c4(rgb, a=1.0):
    r, g, b = (max(0.0, x) for x in rgb)
    return skia.Color4f(r, g, b, a)


def mul(a, b):
    return (a[0] * b[0], a[1] * b[1], a[2] * b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def tint_filter(rgb):
    r, g, b = rgb
    return skia.ColorFilters.Matrix([r, 0, 0, 0, 0,
                                     0, g, 0, 0, 0,
                                     0, 0, b, 0, 0,
                                     0, 0, 0, 1, 0])


# ----------------------------------------------------------------- disc
def make_disc_image(size=512, n=None, seed=3):
    """Floret disc (albedo) on transparent background, radius = size/2."""
    rng = np.random.default_rng(seed)
    R = size / 2 * 0.98
    if n is None:
        n = int((size / 512) ** 2 * 900)
    c = R / math.sqrt(n)
    surf = skia.Surface(size, size)
    cv = surf.getCanvas()
    cv.clear(skia.ColorTRANSPARENT)
    cx = cy = size / 2
    base = skia.Paint(AntiAlias=True, Color4f=c4((0.16, 0.09, 0.035)))
    cv.drawCircle(cx, cy, R, base)
    p = skia.Paint(AntiAlias=True)
    for k in range(n, 0, -1):
        r = c * math.sqrt(k)
        th = k * GOLDEN_ANGLE
        x = cx + r * math.cos(th)
        y = cy + r * math.sin(th)
        u = r / R
        # centre: green-gold unopened florets; middle: deep brown; rim: pollen
        if u < 0.28:
            col = (0.42 - u * 0.4, 0.40 - u * 0.5, 0.10)
        elif u < 0.82:
            m = (u - 0.28) / 0.54
            col = (0.30 - 0.08 * m, 0.17 - 0.06 * m, 0.05)
        else:
            m = (u - 0.82) / 0.18
            col = (0.26 + 0.40 * m, 0.13 + 0.22 * m, 0.04 + 0.02 * m)
        j = 1 + (rng.random() - 0.5) * 0.25
        col = scale(col, j)
        fr = c * 0.58
        p.setColor4f(c4(col))
        cv.drawCircle(x, y, fr, p)
        p.setColor4f(c4(scale(col, 1.55), 0.55))
        cv.drawCircle(x - fr * 0.25, y - fr * 0.25, fr * 0.45, p)
    # dome shading: darker toward the rim
    shade = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (cx, cy), R, [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.0),
                      skia.Color4f(0, 0, 0, 0.45)], [0.0, 0.6, 1.0]))
    cv.drawCircle(cx, cy, R, shade)
    return surf.makeImageSnapshot()


# --------------------------------------------------------------- geometry
def head_basis(yaw, pitch):
    """3D basis of the head plane. yaw: -90 east(left) .. +90 west(right)."""
    y, p = math.radians(yaw), math.radians(pitch)
    n = (math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p))
    eu = (math.cos(y), 0.0, -math.sin(y))
    ev = (-math.sin(y) * math.sin(p), math.cos(p), -math.cos(y) * math.sin(p))
    return n, eu, ev


def plane_matrix(cx, cy, eu, ev):
    # local (u, v_down) -> screen; screen y points down, world y up
    return skia.Matrix.MakeAll(eu[0], -ev[0], cx,
                               -eu[1], ev[1], cy,
                               0, 0, 1)


def petal_path(r0, length, width, curl=0.0):
    pth = skia.Path()
    pth.moveTo(r0, 0)
    pth.cubicTo(r0 + length * 0.25, -width, r0 + length * 0.75, -width * 0.9 + curl,
                r0 + length, curl * 0.5)
    pth.cubicTo(r0 + length * 0.75, width * 0.9 + curl, r0 + length * 0.25, width, r0, 0)
    pth.close()
    return pth


def _stem_polygon(pts, w0, w1):
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = w0 + (w1 - w0) * i / (n - 1)
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    pth = skia.Path()
    pth.moveTo(*left[0])
    for q in left[1:]:
        pth.lineTo(*q)
    for q in reversed(right):
        pth.lineTo(*q)
    pth.close()
    return pth


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t * t
        d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def leaf_path(length, width):
    p = skia.Path()
    p.moveTo(0, 0)
    p.cubicTo(length * 0.25, -width * 1.1, length * 0.8, -width * 0.7, length, 0)
    p.cubicTo(length * 0.8, width * 0.55, length * 0.25, width * 0.9, 0, 0)
    p.close()
    return p


# ----------------------------------------------------------------- flower
class Light:
    """Lighting environment for one frame."""

    def __init__(self, ambient, sun_rgb, sun_k, sun_yaw, rim_rgb=(0, 0, 0)):
        self.ambient = ambient
        self.sun_rgb = sun_rgb
        self.sun_k = sun_k
        self.sun_yaw = sun_yaw
        self.rim = rim_rgb

    def face(self, yaw):
        """Light multiplier on a head's face given its yaw."""
        ff = max(0.0, math.cos(math.radians(yaw - self.sun_yaw))) ** 1.5 * self.sun_k
        return add(self.ambient, scale(self.sun_rgb, 0.85 * ff)), ff

    def body(self, k=0.45):
        return add(self.ambient, scale(self.sun_rgb, k * self.sun_k))


def draw_flower(cv, disc_img, base, height, head_r, yaw, pitch, bloom, light,
                lean=0.0, seed=0, leaves=4, detail=1.0, stem_w=None,
                face_only=False, glow=0.0, petal_n=34, strain=0.0):
    """Draw one sunflower. base=(x, y) ground point, height in px (to head).

    face_only: draw everything black except the face (used to build additive
               'dawn light' layers for the pre-rendered field).
    """
    rng = np.random.default_rng(seed)
    bx, by = base
    n, eu, ev = head_basis(yaw, pitch)
    hx = bx + lean * height * 0.25 + n[0] * head_r * 0.2
    hy = by - height
    depth = head_r * 0.30
    backx, backy = hx - n[0] * depth, hy + n[1] * depth
    body = light.body() if not face_only else (0, 0, 0)
    face_l, ff = light.face(yaw)
    if face_only:
        face_l = (1.0, 1.0, 1.0)
    if stem_w is None:
        stem_w = max(2.0, head_r * 0.16)

    p = skia.Paint(AntiAlias=True)
    # ---- stem (to the back of the head)
    top = (backx - n[0] * depth * 0.4, backy + head_r * 0.15)
    bend = strain * head_r * 0.35
    pts = bezier((bx, by + 5), (bx + lean * height * 0.05, by - height * 0.4),
                 (top[0] - n[0] * head_r * 0.6 + bend, top[1] + height * 0.25),
                 top, 28 if detail > 0.5 else 10)
    p.setColor4f(c4(mul(STEM, body)))
    cv.drawPath(_stem_polygon(pts, stem_w * 1.25, stem_w * 0.8), p)

    # ---- leaves
    for i in range(leaves):
        f = 0.25 + 0.55 * i / max(1, leaves - 1) + (rng.random() - 0.5) * 0.08
        idx = min(len(pts) - 1, int((1 - f) * (len(pts) - 1)))
        lx, ly = pts[idx]
        side = -1 if i % 2 == 0 else 1
        L = head_r * (1.5 - 0.5 * f) * (0.8 + 0.4 * rng.random())
        Wd = L * 0.42
        # leaves reach sideways and droop a little (screen degrees, y down)
        tilt = -15 + 40 * rng.random()
        ang = tilt if side > 0 else 180 - tilt
        cv.save()
        cv.translate(lx, ly)
        cv.rotate(ang)
        droop = 0.55 + 0.25 * rng.random()
        cv.scale(1.0, droop * side)
        p.setColor4f(c4(mul(LEAF_DARK, body)))
        cv.drawPath(leaf_path(L, Wd), p)
        p.setColor4f(c4(mul(LEAF, body)))
        cv.drawPath(leaf_path(L * 0.97, Wd * 0.8), p)
        if detail > 0.5:
            vein = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                              StrokeWidth=max(1.0, L * 0.02))
            vein.setColor4f(c4(mul(scale(LEAF, 1.35), body), 0.6))
            cv.drawLine(0, 0, L * 0.9, 0, vein)
        cv.restore()

    # ---- head thickness: stack of ellipses from back (green) to face (rim)
    steps = 6 if detail > 0.5 else 3
    for s in range(steps + 1):
        a = s / steps
        cx_ = backx + (hx - backx) * a
        cy_ = backy + (hy - backy) * a
        col = CALYX if a < 0.7 else RIM
        cv.save()
        cv.concat(plane_matrix(cx_, cy_, eu, ev))
        p.setColor4f(c4(mul(col, body) if not face_only else (0, 0, 0)))
        cv.drawCircle(0, 0, head_r * (0.92 + 0.08 * a), p)
        cv.restore()

    # ---- sepals / bracts on the back, visible around the edge
    cv.save()
    cv.concat(plane_matrix(backx, backy, eu, ev))
    p.setColor4f(c4(mul(CALYX, body) if not face_only else (0, 0, 0)))
    nb = 21 if detail > 0.5 else 13
    for k in range(nb):
        cv.save()
        cv.rotate(k * 360 / nb + 8)
        cv.drawPath(petal_path(head_r * 0.7, head_r * (0.45 + 0.25 * (1 - bloom)),
                               head_r * 0.13), p)
        cv.restore()
    cv.restore()

    # ---- halo of light behind the head, round in screen space (face stays crisp)
    if glow > 0:
        g = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                       Shader=skia.GradientShader.MakeRadial(
                           (hx, hy), head_r * 2.3,
                           [skia.Color4f(1.0, 0.75, 0.35, 0.40 * glow),
                            skia.Color4f(1.0, 0.68, 0.30, 0.22 * glow),
                            skia.Color4f(1.0, 0.6, 0.2, 0.0)], [0.0, 0.45, 1.0]))
        cv.drawCircle(hx, hy, head_r * 2.3, g)

    # ---- petals + disc on the face plane
    cv.save()
    cv.concat(plane_matrix(hx, hy, eu, ev))
    L_petal = head_r * (0.28 + 0.92 * bloom)
    W_petal = head_r * (0.10 + 0.12 * bloom)
    petal_col = tuple(PETAL[i] * (0.55 + 0.45 * bloom) + LEAF[i] * 0.45 * (1 - bloom)
                      for i in range(3))
    back_col = tuple(PETAL_BACK[i] * (0.6 + 0.4 * bloom) + LEAF[i] * 0.4 * (1 - bloom)
                     for i in range(3))
    np_ = petal_n if detail > 0.5 else 21
    rings = ((back_col, 0.5, 0.92), (petal_col, 0.0, 1.0)) if detail > 0.3 else ((petal_col, 0.0, 1.0),)
    for col, off, lscale in rings:
        for k in range(np_):
            j = rng.random()
            lf = face_l
            c = mul(scale(col, 0.88 + 0.24 * j), lf)
            p.setColor4f(c4(c))
            cv.save()
            cv.rotate((k + off) * 360 / np_ + (j - 0.5) * 4)
            cv.drawPath(petal_path(head_r * 0.82, L_petal * lscale * (0.9 + 0.2 * j),
                                   W_petal, curl=(j - 0.5) * W_petal * 0.6), p)
            cv.restore()
    # disc texture, lit
    dp = skia.Paint(AntiAlias=True, ColorFilter=tint_filter(face_l))
    sz = disc_img.width()
    r = head_r * 0.88
    cv.drawImageRect(disc_img, skia.Rect(0, 0, sz, sz), skia.Rect(-r, -r, r, r),
                     skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), dp)
    cv.restore()
    return (hx, hy), ff
