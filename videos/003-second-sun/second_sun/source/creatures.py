"""The cast of SECOND SUN, as parametric 2D rigs drawn in 'lantern luminism'.

All creatures are drawn facing +x in local units, then placed with
place(cv, x, y, scale, facing). Poses are plain dicts so shots can keyframe
any parameter with anim.Track.
"""
import math

import numpy as np
import skia

from rig import (Gait, Light, c4, catmull, contact_shadow, draw_form, ellipse_path, fuzz,
                 ik2, limb_path, mix, rot_pt, scl, tube, union, xform)


def place(cv, x, y, scale, facing=1):
    cv.save()
    cv.translate(x, y)
    cv.scale(scale * facing, scale)


def mirrored(light, facing):
    if facing > 0:
        return light
    L = Light(light.ambient, light.key, math.pi - light.key_dir, light.rim, light.rim_w,
              light.rim_k, light.shade, light.fog, light.fog_k)
    return L


def _get(p, k, d):
    return p.get(k, d)


# =====================================================================
#                              OLD HORN
# =====================================================================
OH_BODY = (0.50, 0.44, 0.38)
OH_BELLY = (0.66, 0.60, 0.52)
OH_FRILL = (0.78, 0.58, 0.55)
OH_BONE = (0.88, 0.83, 0.72)
OH_BEAK = (0.22, 0.20, 0.18)
# Triceratops: columnar hind legs under the hips, shorter forelegs under the shoulders.
OH_GAIT = Gait(L=260, duty=0.78, phases=(0.0, 0.5, 0.25, 0.75),
               offsets=(-120, -95, 210, 232), lift=24)   # near-hind, far-hind, near-front, far-front


def _frill_path(notch=True):
    """Solid bony frill (Triceratops frills have no fenestrae), seen from the side:
    a broad shield sweeping up and back from the rear of the skull, rimmed with
    triangular epoccipitals. Local head coordinates (pivot = occipital region)."""
    # broad shield rising from behind the brow horns and sweeping up and back over the neck
    rim = [(95, -45), (82, -118), (46, -186), (-12, -236), (-82, -262), (-152, -250), (-200, -202), (-214, -132),
           (-190, -64), (-138, -14)]
    body = catmull(rim + [(-60, 14), (30, 12)], closed=True, tension=0.5)
    # epoccipitals: small triangles along the outer rim
    meas = skia.PathMeasure(catmull(rim, closed=False), False, 1.0)
    L = meas.getLength()
    bumps = skia.Path()
    for k in range(1, 15):
        d = L * k / 15
        pos, tan = meas.getPosTan(d)
        nx_, ny_ = tan.fY, -tan.fX
        bumps.moveTo(pos.fX - tan.fX * 9, pos.fY - tan.fY * 9)
        bumps.lineTo(pos.fX + nx_ * -9, pos.fY + ny_ * -9)
        bumps.lineTo(pos.fX + tan.fX * 9, pos.fY + tan.fY * 9)
        bumps.close()
    p = skia.Op(body, bumps, skia.PathOp.kUnion_PathOp) or body
    if notch:
        v = skia.Path()     # the V-shaped notch in the right edge of the frill
        v.moveTo(-100, -282)
        v.lineTo(-118, -222)
        v.lineTo(-146, -272)
        v.close()
        p = skia.Op(p, v, skia.PathOp.kDifference_PathOp) or p
    # lean the whole shield further back over the neck (Triceratops frills sweep posterodorsally)
    return xform(p, 0, 0, -0.42, 0.86, 0.86, 30, 0)


_FRILL = None


def old_horn(cv, pose, light, x, y, scale, facing=1, detail=1.0):
    """Anatomically based Triceratops horridus (lateral view).

    pose keys: s (walk distance), crouch 0..1 (lying down), head_pitch (rad, + = nose down),
    listen (rad head tilt), breath (seconds), blink 0..1, eye_glow (rgb or None),
    shudder (0..1 leg tremble), mouth (0..1 hum throat pulse)."""
    global _FRILL
    if _FRILL is None:
        _FRILL = _frill_path()
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    s = _get(pose, "s", 0.0)
    cr = _get(pose, "crouch", 0.0)
    t = _get(pose, "breath", 0.0)
    br = math.sin(t * 2 * math.pi / 3.6)
    shud = _get(pose, "shudder", 0.0)
    drop = 118 * cr
    bob = 0.0 if cr > 0.5 else 5 * math.sin(2 * math.pi * (s / OH_GAIT.L) * 2)
    oy = drop + bob + shud * 3 * math.sin(t * 40)
    bb = 1 + 0.02 * br
    tail_sw = 8 * math.sin(t * 0.8)
    tail_rest = 150 * cr               # the tail lowers to the ground when she lies down
    # ---- body: hips higher than shoulders, deep barrel, tail held clear of the ground
    top = [(-500, -210 + tail_sw + tail_rest * 1.05), (-400, -262 + tail_sw * 0.6 + tail_rest * 0.7),
           (-300, -330 + tail_rest * 0.3), (-150, -398), (0, -392), (130, -368), (235, -338), (315, -300)]
    bot = [(330, -205), (255, -150 * bb), (110, -122 * bb), (-60, -126 * bb), (-170, -160), (-275, -222 + tail_rest * 0.3),
           (-395, -230 + tail_sw * 0.6 + tail_rest * 0.7), (-505, -198 + tail_sw + tail_rest * 1.05)]
    pts = [(px + s, py + oy) for px, py in top + bot]
    pts = [(px, min(py, -2.0)) for px, py in pts]
    body = catmull(pts, closed=True, tension=0.5)
    parts_back, parts_front = [], []
    # ---- legs (two-bone IK, feet locked by the distance-based gait)
    hips = [(-120, -300), (-95, -304), (212, -235), (234, -239)]
    lens = [(150, 132), (146, 128), (112, 100), (108, 96)]
    widths = [(118, 72, 60), (110, 68, 56), (84, 62, 56), (80, 58, 52)]
    for i in range(4):
        hx, hy = hips[i][0] + s, hips[i][1] + oy
        if cr < 0.999:
            (fx, fy), sw = OH_GAIT.foot(i, s)
            fx = fx + (hx - fx) * 0.25 * cr
        else:
            fx, fy = hx + (70 if i < 2 else -40), 0.0
        fy = min(fy, 0.0)
        l1, l2 = lens[i]
        bend = 1 if i < 2 else -1
        if cr > 0.3:  # folded: knee forward and low
            kx, ky = hx + (80 if i < 2 else 50) * cr, min(-20.0, hy + 110)
            ax, ay = fx, -16
        else:
            ax, ay = fx, fy - 22
            kx, ky = ik2((hx, hy), (ax, ay), l1, l2, bend)
        w0, w1, w2 = widths[i]
        leg = limb_path([(hx, hy), (kx, ky), (ax, ay), (fx + 6, fy)], [w0, w1, w2, w2 * 1.15])
        foot = ellipse_path(fx + 8, fy - 9, w2 * 0.78, 12)
        pp = union([leg, foot])
        if i < 2:
            pp = union([pp, ellipse_path(hx - 8, hy + 6, 100 if i == 0 else 92, 128, 0.22)])
        else:
            pp = union([pp, ellipse_path(hx + 4, hy + 4, 64, 84, -0.18)])
        (parts_back if i % 2 == 1 else parts_front).append((pp, OH_BODY, 0.62 if i % 2 else 1.0))
        if i % 2 == 0 and cr < 0.5:
            contact_shadow(cv, fx + 8, fy + 2, w2 * 1.2, 9, 0.35 * (1 - cr))
            # hooflike toes
            tp = skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(OH_BONE, 0.55))))
            for k in range(3 if i < 2 else 4):
                tx = fx + 8 + (k - 1) * w2 * 0.42
                cv.drawOval(skia.Rect(tx - 8, fy - 8, tx + 8, fy + 1), tp)
    if cr > 0.3:
        contact_shadow(cv, s + 20, 4, 430, 30, 0.45 * cr)
    # ---- head (pivot at the occipital region, behind the eye)
    piv = (300 + s, -270 + oy)
    hp = _get(pose, "head_pitch", 0.0) - 0.12 * cr + 0.015 * br
    tilt = _get(pose, "listen", 0.0)
    ang = 0.12 + hp + tilt * 0.6

    HS = 1.3        # Triceratops skull ~ a third of body length

    def H(path):
        return xform(path, piv[0], piv[1], ang, HS, HS * (1.0 - 0.08 * abs(tilt)), 0, 0)

    def HP(pt):
        return rot_pt((piv[0] + pt[0] * HS, piv[1] + pt[1] * HS), piv, ang)

    skull = catmull([(40, -70), (150, -78), (240, -45), (320, 0), (362, 34), (386, 66), (372, 88), (340, 84),
                     (300, 98), (160, 102), (70, 80), (20, 30)], closed=True)
    beak = catmull([(322, 6), (364, 34), (392, 70), (376, 96), (348, 90), (330, 60)], closed=True)
    jugal = catmull([(120, 30), (170, 40), (156, 120), (132, 98)], closed=True)     # cheek flare with epijugal spike
    far_horn = limb_path([(150, -72), (220, -150), (300, -228), (338, -256)], [34, 26, 13, 3])
    near_horn = catmull([(128, -70), (174, -80), (214, -126), (230, -154), (220, -150), (214, -166), (200, -156),
                         (192, -166), (176, -128), (138, -78)], closed=True)       # left brow horn broken off halfway
    nose_horn = catmull([(282, -12), (292, -52), (304, -58), (314, -12)], closed=True)
    frill = H(_FRILL)
    head_parts = [(frill, OH_FRILL, 0.95), (H(far_horn), OH_BONE, 0.55), (H(skull), OH_BODY, 1.0),
                  (H(jugal), OH_BODY, 0.9), (H(nose_horn), OH_BONE, 0.95), (H(near_horn), OH_BONE, 1.0)]
    parts = parts_back + [(body, OH_BODY, 1.0)] + parts_front + head_parts
    sil = union([pt[0] for pt in parts])
    draw_form(cv, parts, L, sil=sil, texture=0.22 * detail, tex_scale=0.035, size=320)
    # large rounded scales and skin folds along the flank (Triceratops skin impressions)
    if detail > 0.3:
        cv.save()
        cv.clipPath(body, doAntiAlias=True)
        rng = np.random.default_rng(17)
        sp_ = skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(OH_BODY, 1.12)), 0.22),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2.5))
        for k in range(60):   # large knobbly feature scales, lit from above
            cx_ = s - 350 + rng.random() * 650
            cy_ = oy - 380 + rng.random() * 230
            r_ = 6 + 7 * rng.random()
            cv.drawCircle(cx_, cy_ - 2, r_, sp_)
        fp_ = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.0,
                         Color4f=c4(L.base(scl(OH_BODY, 0.62)), 0.45))
        for k in range(4):   # neck and shoulder folds
            path = skia.Path()
            path.moveTo(s + 250 - k * 14, oy - 320 + k * 8)
            path.quadTo(s + 230 - k * 16, oy - 240, s + 250 - k * 10, oy - 160)
            cv.drawPath(path, fp_)
        cv.restore()
    # frill: faded dusty rose centre, bone rim, radiating blood-vessel grooves (solid bone)
    cv.save()
    cv.clipPath(frill, doAntiAlias=True)
    fcx, fcy = HP((-90, -90))
    g = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (fcx, fcy), 190, [c4(L.base(mix(OH_FRILL, (0.82, 0.48, 0.48), 0.35)), 0.6),
                          c4(L.base(OH_FRILL), 0.0), c4(L.base(OH_BONE), 0.75)], [0, 0.55, 1.0]))
    cv.drawCircle(fcx, fcy, 260, g)
    gp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6,
                    Color4f=c4(L.base(scl(OH_FRILL, 0.8)), 0.18), StrokeCap=skia.Paint.kRound_Cap)
    ox_, oy_ = HP((20, -10))
    for k in range(9):
        a_ = ang + math.radians(-222 + k * 12)
        cv.drawLine(ox_, oy_, ox_ + 330 * math.cos(a_), oy_ + 330 * math.sin(a_), gp)
    cv.restore()
    # beak (keratin), nostril, mouth line
    cv.drawPath(H(beak), skia.Paint(AntiAlias=True, Color4f=c4(L.base(OH_BEAK))))
    ln = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                    Color4f=c4(L.base(scl(OH_BODY, 0.45)), 0.8), StrokeCap=skia.Paint.kRound_Cap)
    mouth = skia.Path()
    mouth.moveTo(338, 82)
    mouth.quadTo(250, 90, 170, 74)
    cv.drawPath(H(mouth), ln)
    cv.drawPath(H(ellipse_path(292, 10, 16, 11, -0.4)), skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(OH_BODY, 0.3)))))
    hum = _get(pose, "mouth", 0.0)
    if hum > 0:
        cv.drawPath(H(ellipse_path(120, 110, 60 + 6 * hum, 26 + 8 * hum)),
                    skia.Paint(AntiAlias=True, Color4f=c4(L.base(OH_BELLY), 0.35 * hum)))
    # the milky, clouded eye
    ex, ey = HP((150, -38))
    blink = _get(pose, "blink", 0.0)
    glow = _get(pose, "eye_glow", None)
    eye_col = (0.80, 0.84, 0.86) if glow is None else glow
    wp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                    Color4f=c4(L.base(scl(OH_BODY, 0.55)), 0.35), StrokeCap=skia.Paint.kRound_Cap)
    for k_ in range(3):
        r_ = 23 + 5 * k_
        cv.drawArc(skia.Rect(ex - r_, ey - r_ * 0.8, ex + r_, ey + r_ * 0.8), 205 + 6 * k_, 100 - 12 * k_, False, wp)
    cv.drawCircle(ex, ey, 17.5, skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(OH_BODY, 0.38)))))
    eg = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (ex - 2, ey - 2), 14, [c4(scl(eye_col, 1.05)), c4(scl(eye_col, 0.82)), c4(scl(eye_col, 0.5))], [0, 0.55, 1.0]))
    cv.drawCircle(ex, ey, 13.5, eg)
    ir = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=c4(scl(eye_col, 0.55), 0.45))
    for k_ in range(10):
        a_ = k_ * math.pi / 5
        cv.drawLine(ex + math.cos(a_) * 5, ey + math.sin(a_) * 5, ex + math.cos(a_) * 10, ey + math.sin(a_) * 10, ir)
    cv.drawCircle(ex + 1, ey + 1, 5, skia.Paint(AntiAlias=True, Color4f=c4(scl(eye_col, 0.55), 0.55),
                                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.5)))
    cv.drawCircle(ex, ey, 12, skia.Paint(AntiAlias=True, Color4f=c4((0.95, 0.97, 1.0), 0.18)))
    arc = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0, Color4f=c4(scl(eye_col, 1.5), 0.5),
                     StrokeCap=skia.Paint.kRound_Cap)
    cv.drawArc(skia.Rect(ex - 10, ey - 10, ex + 10, ey + 10), 200, 70, False, arc)
    cv.drawCircle(ex - 4.5, ey - 5, 2.6, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.85)))
    if blink > 0:
        lid = skia.Path()
        lid.addRect(skia.Rect(ex - 20, ey - 20, ex + 20, ey - 20 + 40 * blink))
        cv.save()
        cv.clipPath(ellipse_path(ex, ey, 17.5, 17.5))
        cv.drawPath(lid, skia.Paint(AntiAlias=True, Color4f=c4(L.base(OH_BODY))))
        cv.restore()
    cv.drawCircle(ex, ey, 16.5, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.0,
                                           Color4f=c4(L.base(scl(OH_BODY, 0.3)))))
    cv.restore()

    def W(pt):
        return (x + facing * scale * pt[0], y + scale * pt[1])
    return {
        "eye": W((ex, ey)),
        "beak": W(HP((390, 76))),
        "head_top": W(HP((105, -74))),          # Wisp's feet: on the skull, between the horns and the frill
        "frill_nest": W(HP((78, -66))),         # Wisp's feet: curled in the curve where frill meets skull
        "chin": W(HP((230, 112))),
        "sil_bounds": sil.getBounds(),
    }


# =====================================================================
#                                WISP
# =====================================================================
WI_BODY = (0.62, 0.44, 0.28)
WI_BELLY = (0.88, 0.80, 0.64)
WI_DARK = (0.30, 0.20, 0.13)
WI_BAND = (0.95, 0.92, 0.82)
WI_EYE = (1.0, 0.66, 0.16)
WI_GAIT_WALK = Gait(L=80, duty=0.6, phases=(0.0, 0.5), offsets=(-4, 2), lift=16)
WI_GAIT_RUN = Gait(L=170, duty=0.32, phases=(0.0, 0.5), offsets=(-4, 2), lift=34)


def _lerp_pts(a, b, k):
    return [(pa[0] + (pb[0] - pa[0]) * k, pa[1] + (pb[1] - pa[1]) * k) for pa, pb in zip(a, b)]


def wisp(cv, pose, light, x, y, scale, facing=1, detail=1.0):
    """Pectinodon (a troodontid): a slender, fox-sized feathered theropod.
    Horizontal body and tail balanced over long legs, S-curved neck, long narrow
    toothed snout, very large forward-set eyes, feathered forelimbs folded like
    wings, a raised enlarged claw on the second toe, and a long frond-like tail
    with feathers along both sides (one pale band).

    pose keys: s, gait ('walk'|'run'|None), hop (0..1) + hop_len/hop_h, crouch 0..1, curl 0..1 (sleep),
    head_pitch, head_turn (-1 looks back), tuft 0..1, tail (rad), blink, breath, yawn, shake,
    beak_open, eye_dir, carry, glow_eye, t."""
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    t = _get(pose, "t", 0.0)
    s = _get(pose, "s", 0.0)
    cr = _get(pose, "crouch", 0.0)
    curl = _get(pose, "curl", 0.0)
    shake = _get(pose, "shake", 0.0)
    br = math.sin(t * 2 * math.pi / 1.1) * (1 - 0.5 * curl)
    gait = _get(pose, "gait", None)
    G = WI_GAIT_RUN if gait == "run" else WI_GAIT_WALK
    hop = _get(pose, "hop", None)
    ox, oy, lean = s, 0.0, 0.0
    if hop is not None:
        hl, hh = _get(pose, "hop_len", 60), _get(pose, "hop_h", 40)
        u = min(1, max(0, (hop - 0.15) / 0.7))
        ox = s + hl * (0.5 - 0.5 * math.cos(math.pi * u))
        air = math.sin(math.pi * u)
        oy = -hh * air
        squat = 0.6 * math.exp(-((hop - 0.08) / 0.07) ** 2) + 0.5 * math.exp(-((hop - 0.92) / 0.07) ** 2)
        cr = max(cr, squat)
        lean = 0.15 * air
    if gait == "run":
        lean = 0.12
        oy -= 5 * abs(math.sin(2 * math.pi * s / G.L))
    sh = shake * math.sin(t * 55) * 4
    hipy = -86 + 34 * cr + 60 * curl + oy + 1.2 * br
    hx = ox + sh * 0.3
    rot = lean - 0.08 * curl

    def R(px, py):  # body frame -> local, rotated about the hip
        c, s_ = math.cos(rot), math.sin(rot)
        return (hx + px * c - py * s_, hipy + px * s_ + py * c)

    # ---- torso: slim, horizontal, deepest at the chest
    torso = catmull([R(-26, -18), R(10, -26), R(46, -24), R(64, -12), R(62, 8), R(38, 20), R(4, 20), R(-24, 10)],
                    closed=True)
    # ---- neck + head (S-curve; the head is held level so the eyes stay stable, bird-like)
    hp = _get(pose, "head_pitch", 0.0)
    turn = _get(pose, "head_turn", 0.0)
    nb = R(56, -14)
    head_awake = (hx + 96, hipy - 64 + 14 * cr)
    head_sleep = (hx + 26, hipy - 24)                   # turned back, resting on the body when asleep
    head_c = (head_awake[0] + (head_sleep[0] - head_awake[0]) * curl, head_awake[1] + (head_sleep[1] - head_awake[1]) * curl)
    head_c = (head_c[0] + sh, head_c[1])
    mid = ((nb[0] + head_c[0]) / 2 - 10 * (1 - curl), (nb[1] + head_c[1]) / 2 + 4)
    neck = tube([nb, mid, (head_c[0] - 8, head_c[1] + 6)], [13, 9, 8], n=18)
    hd = -1 if (turn < 0 or curl > 0.5) else 1
    yawn = _get(pose, "yawn", 0.0)
    bo = max(_get(pose, "beak_open", 0.0), yawn)

    def hpt(px, py):
        return rot_pt((head_c[0] + hd * px, head_c[1] + py), head_c, hp * hd)

    # long, narrow troodontid snout
    skull = catmull([hpt(-14, -6), hpt(-6, -15), hpt(10, -16), hpt(30, -10), hpt(52, -4 - 2 * bo), hpt(54, 0 - 3 * bo),
                     hpt(30, 3), hpt(4, 8), hpt(-12, 6)], closed=True)
    jaw = catmull([hpt(8, 4), hpt(50, 2 + 9 * bo), hpt(48, 6 + 10 * bo), hpt(8, 10)], closed=True)
    # ---- tail: long and straight, stiffened, with feathers along both sides (a frond)
    ta = _get(pose, "tail", 0.0) + 0.08 * math.sin(t * 2.1) + lean * 0.4
    straight = [R(-20 - 42 * k, -8 - 3 * k + 10 * k * math.sin(ta) * 0.3) for k in range(6)]
    curled = []
    for k in range(6):   # wrapped around the body when asleep
        a_ = math.radians(185 - 32 * k)
        curled.append((hx + 20 + 66 * math.cos(a_), min(-3.0, hipy + 4 + 20 * math.sin(a_))))
    tail_pts = _lerp_pts(straight, curled, curl)
    tail = tube(tail_pts, [14, 10, 7, 5, 3, 2], n=26)
    vanes = []
    for k in range(18):
        u = 0.25 + 0.75 * k / 17
        i0 = min(4, int(u * 5))
        fu = u * 5 - i0
        px_ = tail_pts[i0][0] + (tail_pts[i0 + 1][0] - tail_pts[i0][0]) * fu
        py_ = tail_pts[i0][1] + (tail_pts[i0 + 1][1] - tail_pts[i0][1]) * fu
        dx_ = tail_pts[i0 + 1][0] - tail_pts[i0][0]
        dy_ = tail_pts[i0 + 1][1] - tail_pts[i0][1]
        a0 = math.atan2(dy_, dx_)
        for side in (-1, 1):
            ln = 12 + 14 * math.sin(math.pi * min(1, u * 1.1)) + 4 * u
            fa = a0 + side * 0.55 + 0.03 * math.sin(t * 3 + k)
            v = skia.Path()
            v.moveTo(px_, py_)
            v.lineTo(px_ + math.cos(fa - 0.12) * ln, py_ + math.sin(fa - 0.12) * ln)
            v.lineTo(px_ + math.cos(fa + 0.12) * ln * 0.9, py_ + math.sin(fa + 0.12) * ln * 0.9)
            v.close()
            vanes.append((v, u))
    fan_path = union([v[0] for v in vanes])
    # ---- legs: long; the raised enlarged second-toe claw
    legs = []
    for i in (1, 0):
        hip = R(6 + (3 if i else -2), 6)
        if curl > 0.5 or cr > 0.85:
            foot = (hip[0] + 22, 0.0)
        elif hop is not None:
            foot = (ox + (6 if i else -2), min(0.0, oy * 0.7))
        elif gait:
            (fx, fy), _ = G.foot(i, s)
            foot = (fx, fy)
        else:
            foot = (hx + (10 if i else -2), 0.0)
        ank = (foot[0] - 10, foot[1] - 26 + 12 * cr)
        knee = ik2(hip, ank, 38, 42, -1)          # knee points forward
        thigh = ellipse_path(hip[0] + 4, hip[1] + 8, 15, 22, -0.3)
        lp = union([limb_path([hip, knee, ank, (foot[0], foot[1] - 2)], [20, 10, 6, 5]), thigh])
        toes = skia.Path()
        toes.moveTo(foot[0] - 4, foot[1] - 3)
        toes.lineTo(foot[0] + 16, foot[1] - 1)
        toes.lineTo(foot[0] + 16, foot[1] + 1)
        toes.lineTo(foot[0] - 4, foot[1] + 1)
        toes.close()
        sickle = catmull([(foot[0] + 1, foot[1] - 4), (foot[0] + 3, foot[1] - 12), (foot[0] + 8, foot[1] - 12),
                          (foot[0] + 5, foot[1] - 5)], closed=True)
        legs.append((union([lp, toes, sickle]), WI_BODY, 0.6 if i == 1 else 1.0))
    # ---- the feathered arm, folded along the flank like a wing
    wing_tip = R(-18, 4)
    wing = catmull([R(40, -12), R(52, 2), R(30, 10), wing_tip, R(-6, -6), R(20, -14)], closed=True)
    parts = [legs[0], (fan_path, scl(WI_BODY, 0.8), 1.0), (tail, WI_BODY, 0.95), (torso, WI_BODY, 1.0),
             (neck, WI_BODY, 1.0), (skull, WI_BODY, 1.0), (jaw, WI_BODY, 0.9), legs[1], (wing, WI_DARK, 1.0)]
    sil = union([p[0] for p in parts])
    if detail > 0.3:  # short body down along the silhouette
        fuzz(cv, sil, L.base(mix(WI_BODY, WI_BELLY, 0.2)), 2.4 + 3 * shake, n=420, seed=4, jitter_t=t + shake * 10,
             width=1.2, alpha=0.5)
    draw_form(cv, parts, L, sil=sil, texture=0.10 * detail, tex_scale=0.09, size=90)
    # pale belly and throat
    cv.save()
    cv.clipPath(union([torso, neck]), doAntiAlias=True)
    cv.drawOval(skia.Rect(hx - 10, hipy + 2, hx + 70, hipy + 30), skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_BELLY), 0.75),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    cv.restore()
    # tail barring and the one pale band
    cv.save()
    cv.clipPath(fan_path, doAntiAlias=True)
    for v, u in vanes:
        if 0.66 < u < 0.78:
            cv.drawPath(v, skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_BAND), 0.95)))
        elif int(u * 10) % 2 == 0:
            cv.drawPath(v, skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_DARK), 0.35)))
    cv.restore()
    # wing feather lines
    wl = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.1, Color4f=c4(L.base(scl(WI_DARK, 0.6)), 0.7))
    for k in range(5):
        a0 = R(38 - 10 * k, -8 + 2 * k)
        a1 = R(22 - 12 * k, 8)
        cv.drawLine(*a0, *a1, wl)
    # tiny teeth along the jaw
    tp = skia.Paint(AntiAlias=True, Color4f=c4(L.base((0.92, 0.88, 0.78)), 0.9))
    for k in range(6):
        tx, ty = hpt(16 + 6 * k, 3.5)
        cv.drawRect(skia.Rect(tx - 0.8, ty, tx + 0.8, ty + 2.4), tp)
    # the crest tuft: springs upright when excited
    tu = _get(pose, "tuft", 0.3) * (1 - 0.7 * curl)
    tpp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, StrokeCap=skia.Paint.kRound_Cap,
                     Color4f=c4(L.base(scl(WI_BODY, 1.15))))
    base = hpt(-6, -14)
    for k in range(5):
        a = math.radians(-175 + 70 * tu + 11 * k * (0.4 + tu)) + hp * hd
        a = a if hd > 0 else math.pi - a
        wob = math.sin(t * 9 + k) * 0.05 * tu
        ln = 9 + 5 * tu - abs(k - 2) * 1.2
        cv.drawLine(base[0], base[1], base[0] + math.cos(a + wob) * ln, base[1] + math.sin(a + wob) * ln, tpp)
    # the very large, forward-set amber eye (troodontids: big eyes, keen low-light vision)
    ex, ey = hpt(4, -6)
    blink = max(_get(pose, "blink", 0.0), curl * 0.9)
    cv.drawCircle(ex, ey, 7.6, skia.Paint(AntiAlias=True, Color4f=c4((0.08, 0.05, 0.03))))
    ge = _get(pose, "glow_eye", 0.0)
    cv.drawCircle(ex, ey, 6.4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (ex, ey), 6.6, [c4(scl(WI_EYE, 1.1 + ge)), c4(scl(WI_EYE, 0.75 + ge * 0.5))], [0.3, 1.0])))
    ed = _get(pose, "eye_dir", 0.0)
    cv.drawCircle(ex + 1.6 * hd * math.cos(ed), ey + 1.6 * math.sin(ed), 3.2, skia.Paint(AntiAlias=True, Color4f=c4((0.03, 0.02, 0.02))))
    cv.drawCircle(ex - 2 * hd, ey - 2.3, 1.5, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.95)))
    if blink > 0:
        cv.save()
        cv.clipPath(ellipse_path(ex, ey, 8.0, 8.0))
        cv.drawRect(skia.Rect(ex - 9, ey - 9, ex + 9, ey - 9 + 18 * blink), skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_BODY))))
        cv.restore()
    if _get(pose, "carry", False):
        bxp, byp = hpt(52, 4)
        pebble(cv, bxp + 2 * hd, byp + 4, 8, L, glint=0.2)
    cv.restore()

    def Wp(pt):
        return (x + facing * scale * pt[0], y + scale * pt[1])
    return {"eye": Wp((ex, ey)), "beak": Wp(hpt(54, 2)), "head": Wp(head_c), "body": Wp((hx, hipy))}


def pebble(cv, x, y, r, light, rot=0.3, glint=0.0):
    """The white quartz pebble: a smooth, water-worn stone — rounded and slightly
    flattened, milky white with grey flecks and a faint crescent-shaped vein."""
    rng = np.random.default_rng(42)
    pts = []
    for k in range(14):
        a = k / 14 * 2 * math.pi
        rr = r * (1.0 + 0.06 * math.sin(3 * a + 0.7) + 0.04 * math.sin(5 * a))
        pts.append((x + rr * math.cos(a) * 1.25, y + rr * math.sin(a) * 0.82))
    stone = xform(catmull(pts, closed=True), 0, 0, rot, 1, 1, x, y)
    # contact shadow
    cv.drawOval(skia.Rect(x - r * 1.4, y + r * 0.45, x + r * 1.4, y + r * 1.05),
                skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), 0.35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.3)))
    cv.drawPath(stone, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - r * 0.45, y - r * 0.4), r * 1.9,
        [c4(light.base((1.30, 1.28, 1.22))), c4(light.base((0.92, 0.90, 0.86))), c4(light.base((0.58, 0.57, 0.56)))],
        [0.0, 0.55, 1.0])))
    cv.save()
    cv.clipPath(stone, doAntiAlias=True)
    fp = skia.Paint(AntiAlias=True, Color4f=c4(light.base((0.5, 0.48, 0.46)), 0.5))
    for k in range(9):
        cv.drawCircle(x + (rng.random() - 0.5) * r * 2.0, y + (rng.random() - 0.5) * r * 1.3, max(0.4, r * 0.05), fp)
    vein = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(0.6, r * 0.09),
                      Color4f=c4(light.base((1.1, 1.08, 1.02)), 0.6))
    cv.drawArc(skia.Rect(x - r * 0.7, y - r * 0.55, x + r * 0.5, y + r * 0.5), 110, 140, False, vein)
    cv.restore()
    cv.drawOval(skia.Rect(x - r * 0.75, y - r * 0.55, x - r * 0.2, y - r * 0.3),
                skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.08)))
    if glint > 0:
        gx, gy = x - r * 0.5, y - r * 0.45
        gp = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                        Shader=skia.GradientShader.MakeRadial((gx, gy), r * 1.3, [c4((1, 1, 0.95), glint), c4((1, 1, 1), 0)], [0, 1]))
        cv.drawCircle(gx, gy, r * 1.3, gp)


# =====================================================================
#                             THE BURROWER
# =====================================================================
BU_COL = (0.40, 0.30, 0.22)


def burrower(cv, pose, light, x, y, scale, facing=1):
    """pose: s (run distance), t, sniff 0..1, peek (0..1 how far out of a hole: clips below y)."""
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    t = _get(pose, "t", 0.0)
    s = _get(pose, "s", 0.0)
    run = _get(pose, "run", 0.0)
    bob = abs(math.sin(s / 9.0)) * 4 * run
    body = ellipse_path(s, -12 - bob, 18 + 3 * run, 11 - 2 * run)
    head = catmull([(s + 10, -24 - bob), (s + 22, -24 - bob), (s + 34, -14 - bob), (s + 22, -6 - bob),
                    (s + 10, -8 - bob)], closed=True)
    ear = ellipse_path(s + 16, -27 - bob, 5, 4)
    tail = tube([(s - 16, -10 - bob), (s - 30, -8), (s - 44, -12 + 3 * math.sin(t * 6))], [3, 2, 1], n=10)
    feet = []
    for k in range(2):
        ph = s / 9.0 + k * math.pi
        feet.append(ellipse_path(s - 6 + 16 * k + 5 * math.sin(ph) * run, -2, 5, 3))
    parts = [(tail, BU_COL, 0.8), (body, BU_COL), (head, BU_COL), (ear, BU_COL, 0.9)] + [(f, BU_COL, 0.7) for f in feet]
    sil = union([p[0] for p in parts])
    fuzz(cv, sil, L.base(scl(BU_COL, 1.2)), 2.4, n=120, seed=8, jitter_t=t)
    draw_form(cv, parts, L, sil=sil, size=40)
    ex, ey = s + 24, -18 - bob
    cv.drawCircle(ex, ey, 2.6, skia.Paint(AntiAlias=True, Color4f=c4((0.02, 0.02, 0.02))))
    cv.drawCircle(ex - 0.8, ey - 0.9, 0.9, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.9)))
    sn = _get(pose, "sniff", 0.0)
    wp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=0.8,
                    Color4f=c4(L.base((0.9, 0.85, 0.8)), 0.8))
    for k in range(3):
        a = -0.3 + 0.3 * k + 0.15 * math.sin(t * 30 * sn + k)
        cv.drawLine(s + 33, -14 - bob, s + 33 + 12 * math.cos(a), -14 - bob + 12 * math.sin(a), wp)
    cv.restore()


# =====================================================================
#                            EDMONTOSAURUS
# =====================================================================
ED_COL = (0.44, 0.44, 0.36)
ED_COMB = (0.72, 0.36, 0.26)


def edmonto(cv, pose, light, x, y, scale, facing=1, detail=1.0):
    """pose: s, t, head (0 = up, 1 = down drinking), alarm (0..1 head raised high, facing south),
    bellow (0..1 mouth open) — the herd scatters in S20."""
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    t = _get(pose, "t", 0.0)
    s = _get(pose, "s", 0.0)
    hd = _get(pose, "head", 0.0)
    alarm = _get(pose, "alarm", 0.0)
    gait = Gait(L=260, duty=0.7, phases=(0.0, 0.5, 0.25, 0.75), offsets=(-70, -50, 150, 170), lift=24)
    br = math.sin(t * 2 * math.pi / 2.8)
    rear = 40 * alarm
    top = [(-560, -200), (-380, -262), (-150, -330), (-40, -342 - rear * 0.3), (110, -305 - rear),
           (200, -270 - rear * 1.3)]
    bot = [(215, -170 - rear * 1.2), (80, -140 * (1 + 0.02 * br) - rear * 0.8), (-80, -150), (-220, -200),
           (-380, -220), (-560, -190)]
    body = catmull([(px + s, py) for px, py in top + bot], closed=True)
    legs = []
    specs = [(-80, -222, 120, 108, 100, 1), (-55, -226, 116, 104, 92, 1),
             (165, -175 - rear, 90, 80, 50, -1), (182, -179 - rear, 88, 78, 46, -1)]
    for i, (hx, hy, l1, l2, w, bend) in enumerate(specs):
        (fx, fy), _ = gait.foot(i, s)
        if i >= 2 and alarm > 0:
            fy = fy - 60 * alarm
        kx, ky = ik2((hx + s, hy), (fx, fy - 14), l1, l2, bend)
        lp = limb_path([(hx + s, hy), (kx, ky), (fx, fy - 14), (fx + 8, fy)], [w, w * 0.6, w * 0.45, w * 0.5])
        if i < 2:
            lp = union([lp, ellipse_path(hx + s - 6, hy + 6, w * 0.95, w * 1.4, 0.2)])
        legs.append((lp, ED_COL, 0.62 if i % 2 else 1.0))
    base = (200 + s, -225 - rear * 1.2)
    ang = -0.55 + 1.45 * hd - 0.55 * alarm + 0.04 * math.sin(t * 1.3)
    nl = 150
    hx = base[0] + nl * math.cos(ang)
    hy = base[1] + nl * math.sin(ang) - 20 * (1 - hd)
    neck = tube([base, ((base[0] + hx) / 2 + 6, (base[1] + hy) / 2 - 24 * (1 - hd)), (hx, hy)], [70, 46, 34], n=18)
    hang = ang * 0.55 + 0.35
    bo = _get(pose, "bellow", 0.0)
    head = xform(catmull([(-24, -26), (30, -32), (90, -20), (132, -14), (160, -4), (164, 10), (150, 22 + 7 * bo),
                          (110, 20), (60, 30), (10, 32), (-22, 16)], closed=True), hx, hy, hang)   # long skull, broad flat duck bill
    comb = xform(catmull([(-8, -28), (14, -56), (40, -50), (40, -30)], closed=True), hx, hy, hang)
    parts = [legs[1], legs[3], (body, ED_COL), legs[0], legs[2], (neck, ED_COL), (head, ED_COL)]
    sil = union([p[0] for p in parts] + [comb])
    draw_form(cv, parts + [(comb, ED_COMB, 1.0)], L, sil=sil, texture=0.15 * detail, size=260)
    ex, ey = rot_pt((hx + 34, hy - 8), (hx, hy), hang)
    cv.drawCircle(ex, ey, 5, skia.Paint(AntiAlias=True, Color4f=c4((0.05, 0.04, 0.03))))
    cv.restore()
    return {"head": (x + facing * scale * hx, y + scale * hy), "sil": sil}


# =====================================================================
#                              THE HUNTER
# =====================================================================
RX_COL = (0.24, 0.24, 0.20)
RX_GAIT = Gait(L=460, duty=0.62, phases=(0.0, 0.5), offsets=(-90, -60), lift=46)


def rex(cv, pose, light, x, y, scale, facing=1, detail=1.0):
    """Young adult T. rex. pose: s, t, head_low (0..1), jaw 0..1, nostril 0..1, eye_k (eye shine)."""
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    t = _get(pose, "t", 0.0)
    s = _get(pose, "s", 0.0)
    low = _get(pose, "head_low", 0.7)
    br = math.sin(t * 2 * math.pi / 3.4)
    bob = 7 * math.sin(2 * math.pi * s / RX_GAIT.L * 2)
    top = [(-900, -430), (-620, -505), (-330, -565), (-90, -588), (120, -548), (270, -475), (335, -425)]
    bot = [(340, -300), (220, -300 * (1 + 0.015 * br)), (80, -330), (-100, -362), (-300, -420), (-620, -442),
           (-900, -420)]
    body = catmull([(px + s, py + bob) for px, py in top + bot], closed=True)
    legs = []
    for i in (1, 0):
        hip = (-90 + s + (26 if i else 0), -440 + bob)
        (fx, fy), _ = RX_GAIT.foot(i, s)
        ank = (fx - 40, fy - 96)
        k1 = ik2(hip, ank, 230, 205, 1)
        lp = union([limb_path([hip, k1, ank, (fx + 24, fy)], [170, 92, 54, 44]),
                    ellipse_path(hip[0] - 10, hip[1] + 20, 130, 175, 0.25),
                    ellipse_path(fx + 30, fy - 10, 54, 13)])
        legs.append((lp, RX_COL, 0.58 if i == 1 else 1.0))
    arm = tube([(250 + s, -330 + bob), (290 + s, -300 + bob), (304 + s, -312 + bob)], [18, 12, 6], n=12)
    piv = (330 + s, -380 + bob + 70 * low)
    jaw = _get(pose, "jaw", 0.0)
    hang = 0.2 * low - 0.04 + 0.02 * math.sin(t * 0.7)
    skull = xform(catmull([(-50, -120), (90, -158), (250, -128), (360, -66), (392, -12), (372, 32), (160, 52),
                           (10, 84), (-60, 30)], closed=True), piv[0], piv[1], hang)
    lower = xform(catmull([(0, 52), (160, 62), (350, 40), (342, 70 + 60 * jaw), (150, 134 + 40 * jaw),
                           (-10, 112)], closed=True), piv[0], piv[1], hang + 0.14 * jaw)
    parts = [legs[0], (body, RX_COL), (lower, RX_COL, 0.85), (skull, RX_COL), (arm, RX_COL, 0.8), legs[1]]
    sil = union([p[0] for p in parts])
    draw_form(cv, parts, L, sil=sil, texture=0.35 * detail, tex_scale=0.05, size=420)
    hx, hy = piv
    ex, ey = rot_pt((hx + 118, hy - 84), (hx, hy), hang)
    boss = xform(ellipse_path(116, -106, 40, 16, -0.1), hx, hy, hang)
    cv.drawPath(boss, skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(RX_COL, 0.7)))))
    ek = _get(pose, "eye_k", 1.0)
    cv.drawCircle(ex, ey, 12, skia.Paint(AntiAlias=True, Color4f=c4((0.02, 0.02, 0.01))))
    cv.drawCircle(ex, ey, 8, skia.Paint(AntiAlias=True, Color4f=c4((1.1 * ek, 0.75 * ek, 0.2 * ek))))
    cv.drawRect(skia.Rect(ex - 1.6, ey - 7, ex + 1.6, ey + 7), skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0))))
    cv.drawCircle(ex - 3, ey - 3, 2.2, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.7 * ek)))
    nf = _get(pose, "nostril", 0.0)
    nx_, ny_ = rot_pt((hx + 362, hy - 44), (hx, hy), hang)
    cv.drawOval(skia.Rect(nx_ - 10 - 4 * nf, ny_ - 5 - 2 * nf, nx_ + 10 + 4 * nf, ny_ + 5 + 2 * nf),
                skia.Paint(AntiAlias=True, Color4f=c4((0.03, 0.03, 0.02))))
    tp = skia.Paint(AntiAlias=True, Color4f=c4(L.base((0.85, 0.80, 0.65))))
    for k in range(10):
        tx, ty = rot_pt((hx + 70 + 28 * k, hy + 48 - 1.4 * k), (hx, hy), hang)
        tri = skia.Path()
        tri.moveTo(tx - 5, ty)
        tri.lineTo(tx + 5, ty)
        tri.lineTo(tx, ty + 12 + (k % 3) * 2)
        tri.close()
        cv.drawPath(tri, tp)
    cv.restore()
    return {"eye": (x + facing * scale * ex, y + scale * ey), "sil": sil}


# =====================================================================
#                             AZHDARCHID
# =====================================================================
def azhdarchid(cv, t, light, x, y, scale, facing=1):
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    flex = 0.12 * math.sin(t * 1.4)
    wing = catmull([(-10, 0), (-160, -30 - 60 * flex), (-330, 10 - 80 * flex), (-200, 20), (-40, 22),
                    (40, 22), (200, 20), (330, 10 - 80 * flex), (160, -30 - 60 * flex), (10, 0)], closed=True)
    body = ellipse_path(0, 10, 40, 14)
    neck = tube([(30, 6), (90, -30), (130, -40)], [8, 6, 5], n=12)
    head = catmull([(120, -52), (140, -60), (260, -30), (140, -34)], closed=True)
    crest = catmull([(126, -50), (100, -84), (146, -58)], closed=True)
    parts = [(wing, (0.30, 0.26, 0.24), 0.85), (body, (0.30, 0.26, 0.24)), (neck, (0.3, 0.26, 0.24)),
             (head, (0.3, 0.26, 0.24)), (crest, (0.6, 0.3, 0.2))]
    draw_form(cv, parts, L, size=200, ao=False)
    cv.restore()


# =====================================================================
#                         HUMANS (epilogue only)
# =====================================================================
def human_silhouette(cv, x, y, h, color, kind="adult", arm_up=0.0, lean=0.0, t=0.0):
    """Simple elegant silhouette: grandmother (with shawl) or child."""
    cv.save()
    cv.translate(x, y)
    s = h / 100.0
    cv.scale(s, s)
    p = skia.Paint(AntiAlias=True, Color4f=c4(color))
    br = 0.6 * math.sin(t * 2 * math.pi / 4)
    if kind == "adult":
        body = catmull([(-14, 0), (-18, -40), (-20, -62), (-14, -74 + br), (0, -80 + br), (14, -74 + br),
                        (22, -60), (18, -40), (15, 0)], closed=True)
        head = ellipse_path(2 + lean * 4, -88 + br, 7.5, 8.5)
        bun = ellipse_path(-4 + lean * 4, -95 + br, 4, 3.5)
        arm = tube([(10, -70 + br), (14 - 6 * arm_up, -48 - 5 * arm_up), (10 - 12 * arm_up, -30 - 6 * arm_up)],
                   [5, 4, 3.5], n=10)
        cv.drawPath(union([body, head, bun, arm]), p)
    else:
        body = catmull([(-8, 0), (-9, -26), (-10, -38), (-6, -46), (0, -48), (6, -46), (10, -38), (9, -26),
                        (8, 0)], closed=True)
        head = ellipse_path(0, -56, 7, 7.5)
        arm = tube([(-6, -44), (-10 - 4 * arm_up, -32 - 22 * arm_up), (-12 - 4 * arm_up, -22 - 40 * arm_up)],
                   [3.5, 3, 2.6], n=10)
        cv.drawPath(union([body, head, arm]), p)
    cv.restore()


_DUMMY = None


def oh_anchor(pose, x, y, scale, facing=1):
    """World anchors of Old Horn for a pose, without drawing to the frame (for aiming cameras)."""
    global _DUMMY
    if _DUMMY is None:
        _DUMMY = skia.Surface(8, 8)
    return old_horn(_DUMMY.getCanvas(), pose, Light(), x, y, scale, facing, detail=0.0)
