"""2D rigging + 'lantern luminism' form rendering for SECOND SUN.

Characters are sculpted, rim-lit silhouettes: each creature is a set of
smooth shapes (spine outlines, IK limbs, heads) unioned into one silhouette
that receives a soft key gradient, ambient occlusion at the belly, a warm or
cool rim on the light side, and a faint procedural skin texture.

Gaits are parameterised by *distance travelled*, never by time: a foot's
world position during stance depends only on the distance s, so feet are
locked to the ground and cannot slide whatever the speed curve does.
"""
import math

import numpy as np
import skia


# ------------------------------------------------------------------ colour
def c4(rgb, a=1.0):
    return skia.Color4f(max(0.0, rgb[0]), max(0.0, rgb[1]), max(0.0, rgb[2]), a)


def mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def mul(a, b):
    return tuple(a[i] * b[i] for i in range(3))


def scl(a, s):
    return tuple(v * s for v in a)


class Light:
    """Per-shot lighting for characters.

    key_dir: direction *towards* the key light in screen space (radians,
             0 = light from the right, pi/2 = from below, -pi/2 = from above).
    """

    def __init__(self, ambient=(0.5, 0.5, 0.5), key=(1, 0.9, 0.8), key_dir=-2.3,
                 rim=(1.0, 0.85, 0.6), rim_w=0.10, rim_k=1.0, shade=0.45, fog=None,
                 fog_k=0.0):
        self.ambient, self.key, self.key_dir = ambient, key, key_dir
        self.rim, self.rim_w, self.rim_k, self.shade = rim, rim_w, rim_k, shade
        self.fog, self.fog_k = fog, fog_k

    def base(self, albedo):
        c = mul(albedo, self.ambient)
        if self.fog is not None and self.fog_k > 0:
            c = mix(c, self.fog, self.fog_k)
        return c


# --------------------------------------------------------------- geometry
def catmull(points, closed=True, tension=0.5):
    """Smooth closed/open path through points (Catmull-Rom -> cubic Bezier)."""
    p = skia.Path()
    n = len(points)
    if n < 2:
        return p
    pts = list(points)
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        k = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def resample(points, n):
    pts = np.array(points, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    t = np.linspace(0, d[-1], n)
    return np.c_[np.interp(t, d, pts[:, 0]), np.interp(t, d, pts[:, 1])]


def tube(points, radii, n=28, cap=True, top_bias=None):
    """Closed smooth outline around a centre-line with varying radius.

    top_bias: optional per-point multiplier for the upper side (y-) so a body
    can be humped on top and flatter underneath.
    """
    pts = np.array(points, float)
    rad = np.array(radii, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    t = np.linspace(0, d[-1], n)
    cx = np.interp(t, d, pts[:, 0])
    cy = np.interp(t, d, pts[:, 1])
    r = np.interp(t, d, rad)
    tb = np.interp(t, d, np.array(top_bias, float)) if top_bias is not None else np.ones(n)
    dx = np.gradient(cx)
    dy = np.gradient(cy)
    L = np.hypot(dx, dy) + 1e-9
    nx, ny = -dy / L, dx / L
    # side A is where the normal points up (screen y negative) -> "top"
    up = ny < 0
    ra = np.where(up, r * tb, r)
    rb = np.where(~up, r * tb, r)
    left = list(zip(cx + nx * ra, cy + ny * ra))
    right = list(zip(cx - nx * rb, cy - ny * rb))
    outline = left + right[::-1]
    return catmull(outline, closed=True)


def ik2(hip, foot, l1, l2, bend=1.0):
    """Two-bone IK. bend=+1 knee bends to the right of the hip->foot line."""
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    d = max(1e-6, math.hypot(dx, dy))
    d_c = min(d, l1 + l2 - 1e-3)
    a = (l1 * l1 - l2 * l2 + d_c * d_c) / (2 * d_c)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    kx = hx + ux * a - uy * h * bend
    ky = hy + uy * a + ux * h * bend
    return (kx, ky)


def limb_path(pts, widths):
    """Tapered limb through joint points with widths at each joint."""
    return tube(pts, [w / 2 for w in widths], n=max(12, 8 * len(pts)))


def ellipse_path(cx, cy, rx, ry, rot=0.0):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    if rot:
        m = skia.Matrix()
        m.setRotate(math.degrees(rot), cx, cy)
        p.transform(m)
    return p


def xform(path, tx=0, ty=0, rot=0.0, sx=1.0, sy=1.0, px=0, py=0):
    """Rotate/scale about (px, py) then translate."""
    m = skia.Matrix()
    m.preTranslate(tx, ty)
    m.preTranslate(px, py)
    m.preRotate(math.degrees(rot))
    m.preScale(sx, sy)
    m.preTranslate(-px, -py)
    q = skia.Path(path)
    q.transform(m)
    return q


def rot_pt(p, c, a):
    s, co = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * co - y * s, c[1] + x * s + y * co)


def union(paths):
    out = skia.Path(paths[0])
    for q in paths[1:]:
        r = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
        if r is not None:
            out = r
    return out


# ------------------------------------------------------------------- gaits
class Gait:
    """Distance-parameterised gait. Feet are locked during stance.

    phases: per-foot phase offsets in [0,1); duty: stance fraction.
    L: stride length (distance per full cycle); lift: swing height.
    offsets: per-foot hip x offsets relative to the body origin.
    """

    def __init__(self, L, duty, phases, offsets, lift):
        self.L, self.duty, self.phases, self.offsets, self.lift = L, duty, phases, offsets, lift

    def foot(self, i, s, ground_y=0.0):
        L, duty, ph = self.L, self.duty, self.phases[i]
        v = s / L + ph
        k = math.floor(v)
        u = v - k
        plant = lambda kk: (kk + duty / 2 - ph) * L + self.offsets[i]  # noqa: E731
        if u < duty:
            return (plant(k), ground_y), 0.0
        w = (u - duty) / (1 - duty)
        e = 0.5 - 0.5 * math.cos(math.pi * w)
        x = plant(k) + (plant(k + 1) - plant(k)) * e
        return (x, ground_y - self.lift * math.sin(math.pi * w)), w

    def contacts(self, s0, s1):
        """Distances at which each foot touches down between s0 and s1."""
        out = []
        for i, ph in enumerate(self.phases):
            k0 = math.floor(s0 / self.L + ph)
            k1 = math.floor(s1 / self.L + ph)
            for k in range(k0 + 1, k1 + 1):
                out.append(((k - ph) * self.L, i))
        return sorted(out)

    def all_planted(self, s):
        return all(((s / self.L + ph) % 1.0) < self.duty for ph in self.phases)

    def settle(self, s):
        """Nearest distance >= s where every foot is planted (for clean stops)."""
        step = self.L / 400
        x = s
        while not self.all_planted(x):
            x += step
        return x


# -------------------------------------------------------------- rendering
_NOISE_CACHE = {}


def skin_shader(scale=0.02, seed=3, alpha=0.18, tint=(0, 0, 0)):
    key = (scale, seed)
    if key not in _NOISE_CACHE:
        _NOISE_CACHE[key] = skia.PerlinNoiseShader.MakeFractalNoise(scale, scale, 3, seed)
    return _NOISE_CACHE[key]


def draw_form(cv, parts, light, sil=None, texture=0.0, tex_scale=0.03, rim_scale=1.0,
              ao=True, size=100.0):
    """Draw a creature.

    parts: list of (path, albedo_rgb[, darken]) back-to-front.
    size:  characteristic size in px (rim width and blur scale with it).
    """
    paths = [p[0] for p in parts]
    if sil is None:
        sil = union(paths)
    p = skia.Paint(AntiAlias=True)
    for part in parts:
        path, alb = part[0], part[1]
        dk = part[2] if len(part) > 2 else 1.0
        p.setColor4f(c4(scl(light.base(alb), dk)))
        cv.drawPath(path, p)
    b = sil.getBounds()
    cv.save()
    cv.clipPath(sil, doAntiAlias=True)
    # form shading: lighter toward the key, darker away (soft gradient across the body)
    kx, ky = math.cos(light.key_dir), math.sin(light.key_dir)
    cxm, cym = b.centerX(), b.centerY()
    R = max(b.width(), b.height()) * 0.6
    g = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(cxm + kx * R, cym + ky * R), (cxm - kx * R, cym - ky * R)],
        [c4(light.key, 0.20), c4((0, 0, 0), 0.0), c4((0, 0, 0), light.shade)], [0.0, 0.45, 1.0]))
    cv.drawRect(b.makeOutset(4, 4), g)
    if ao:  # belly / ground occlusion
        g2 = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, b.bottom()), (0, b.bottom() - b.height() * 0.35)],
            [c4((0, 0, 0), 0.35), c4((0, 0, 0), 0.0)], [0.0, 1.0]))
        cv.drawRect(b.makeOutset(4, 4), g2)
    if texture > 0:
        t = skia.Paint(AntiAlias=True, Shader=skin_shader(tex_scale), BlendMode=skia.BlendMode.kOverlay)
        t.setAlphaf(texture)
        cv.drawRect(b.makeOutset(4, 4), t)
    # rim light on the light-facing edge
    if light.rim_k > 0:
        w = max(1.2, size * light.rim_w * rim_scale)
        cv.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kPlus))
        rp = skia.Paint(AntiAlias=True, Color4f=c4(light.rim, min(1.0, light.rim_k)))
        cv.drawPath(sil, rp)
        m = skia.Matrix()
        m.setTranslate(-kx * w, -ky * w)
        sh = skia.Path(sil)
        sh.transform(m)
        cut = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kDstOut,
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.55))
        cv.drawPath(sh, cut)
        cv.restore()
    cv.restore()
    return sil


def fuzz(cv, sil, color, length, n=160, seed=1, jitter_t=0.0, width=1.4, alpha=0.9):
    """Down feathers: short strokes normal to the silhouette (drawn *before* the fill)."""
    rng = np.random.default_rng(seed)
    meas = skia.PathMeasure(sil, False, 1.0)
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                   StrokeCap=skia.Paint.kRound_Cap, Color4f=c4(color, alpha))
    while True:
        L = meas.getLength()
        m = max(4, int(n * L / 600))
        for i in range(m):
            d = (i + rng.random() * 0.8) / m * L
            ok, pos, tan = _postan(meas, d)
            if not ok:
                continue
            nx, ny = tan.fY, -tan.fX
            ln = length * (0.5 + rng.random() * 0.8)
            wob = math.sin(jitter_t * 3 + i * 1.7) * 0.25
            ex = pos.fX + (nx + tan.fX * wob) * ln
            ey = pos.fY + (ny + tan.fY * wob) * ln
            cv.drawLine(pos.fX - nx * ln * 0.6, pos.fY - ny * ln * 0.6, ex, ey, p)
        if not meas.nextContour():
            break


def _postan(meas, d):
    r = meas.getPosTan(d)
    if isinstance(r, tuple) and len(r) == 2:
        return True, r[0], r[1]
    return r


def contact_shadow(cv, x, y, rx, ry, alpha=0.45, color=(0, 0, 0)):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x, y), rx, [c4(color, alpha), c4(color, alpha * 0.4), c4(color, 0.0)], [0, 0.5, 1]))
    cv.save()
    cv.translate(x, y)
    cv.scale(1.0, ry / rx)
    cv.translate(-x, -y)
    cv.drawCircle(x, y, rx, p)
    cv.restore()


def cast_shadow(cv, sil, ground_y, dir_x, length=1.0, alpha=0.4, blur=6.0):
    """Project a silhouette onto the ground plane (skewed, squashed) —
    used for the long golden-hour shadows and the S19 shadows swinging north."""
    k = 0.16 * length
    m = skia.Matrix.MakeAll(1, -dir_x * length, dir_x * length * ground_y,
                            0, -k, ground_y * (1 + k), 0, 0, 1)
    sh = skia.Path(sil)
    sh.transform(m)
    p = skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), alpha),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    cv.drawPath(sh, p)
