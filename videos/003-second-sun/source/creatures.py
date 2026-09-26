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
OH_BODY = (0.47, 0.40, 0.34)
OH_BELLY = (0.62, 0.54, 0.45)
OH_FRILL = (0.76, 0.56, 0.53)
OH_BONE = (0.87, 0.81, 0.69)
OH_BEAK = (0.24, 0.21, 0.19)
OH_GAIT = Gait(L=250, duty=0.8, phases=(0.0, 0.5, 0.25, 0.75),
               offsets=(-80, -60, 235, 255), lift=26)   # near-hind, far-hind, near-front, far-front


def _frill_path(notch=True):
    # shield rising up and back from the back of the skull
    pts = []
    n = 26
    for i in range(n + 1):
        a = math.radians(-215 + 150 * i / n)
        r = 235 + 14 * math.cos(i * math.pi * 2.2)
        x = -70 + r * math.cos(a) * 1.05
        y = -40 + r * math.sin(a) * 0.86
        # epoccipital scallops along the rim
        bump = 13 * (0.5 + 0.5 * math.cos(i * 2 * math.pi / 2.0))
        x += bump * math.cos(a)
        y += bump * math.sin(a)
        pts.append((x, y))
    pts += [(80, -40), (30, 30), (-80, 40), (-250, 0)]
    p = catmull(pts, closed=True, tension=0.45)
    if notch:
        v = skia.Path()
        # the V-shaped notch in the upper-front edge of the frill
        v.moveTo(-10, -262)
        v.lineTo(30, -170)
        v.lineTo(70, -250)
        v.close()
        r = skia.Op(p, v, skia.PathOp.kDifference_PathOp)
        if r is not None:
            p = r
    return p


_FRILL = None


def old_horn(cv, pose, light, x, y, scale, facing=1, detail=1.0):
    """pose keys: s (walk distance), crouch 0..1, head_pitch (rad, + = nose down),
    listen (rad head tilt), breath (phase, seconds), blink 0..1, eye_glow (rgb or None),
    shudder (0..1 leg tremble), mouth (0..1 hum throat pulse)."""
    global _FRILL
    if _FRILL is None:
        _FRILL = _frill_path()
    L = mirrored(light, facing)
    place(cv, x, y, scale, facing)
    s = _get(pose, "s", 0.0)
    cr = _get(pose, "crouch", 0.0)
    t = _get(pose, "breath", 0.0)
    br = math.sin(t * 2 * math.pi / 3.6)      # slow, heavy breathing
    shud = _get(pose, "shudder", 0.0)
    drop = 150 * cr
    bob = 0.0
    # body bob follows the gait (lowest just after each front footfall)
    if cr < 0.5:
        bob = 5 * math.sin(2 * math.pi * (s / OH_GAIT.L) * 2)
    oy = drop + bob + shud * 3 * math.sin(t * 40)
    tail_sw = 6 * math.sin(t * 0.9) + 34 * cr
    bb = 1 + 0.025 * br           # breathing swells the ribcage
    tip_y = min(-14 - oy, -52 + tail_sw)          # the tail rests on the ground when she lies down
    top = [(-500, tip_y - 6), (-420, -112 + tail_sw * 0.6), (-300, -210 + tail_sw * 0.3), (-190, -310), (-60, -420),
           (90, -405), (230, -365), (330, -335)]
    bot = [(345, -190), (250, -150 * bb), (80, -128 * bb), (-110, -150 * bb), (-220, -196),
           (-320, -128 + tail_sw * 0.3), (-430, -64 + tail_sw * 0.6), (-515, tip_y + 12)]
    outline = [(px + s, py + oy) for px, py in top + bot]
    body = catmull(outline, closed=True, tension=0.5)
    sp = [(335 + s, -282 + oy)]
    parts_back, parts_front = [], []
    # ---- legs
    hips = [(-90, -250), (-60, -254), (225, -215), (248, -219)]
    lens = [(128, 118), (126, 116), (108, 96), (106, 94)]
    widths = [(120, 78, 64), (112, 74, 60), (92, 68, 60), (88, 64, 56)]
    for i in range(4):
        hx, hy = hips[i][0] + s, hips[i][1] + oy
        if cr < 0.999:
            (fx, fy), sw = OH_GAIT.foot(i, s)
            # folded legs tuck under the body as she lies down
            fx = fx + (hx - fx) * 0.35 * cr
            fy = fy - 10 * cr
        else:
            fx, fy = hx + (40 if i < 2 else -30), -8
        l1, l2 = lens[i]
        bend = 1 if i < 2 else -1          # hind knee forward, front elbow back
        kx, ky = ik2((hx, hy), (fx, fy - 18), l1, l2, bend)
        w0, w1, w2 = widths[i]
        leg = limb_path([(hx, hy), (kx, ky), (fx, fy - 18), (fx + 6, fy)], [w0, w1, w2, w2 * 1.2])
        foot = ellipse_path(fx + 8, fy - 8, w2 * 0.8, 12)
        pp = union([leg, foot])
        if i < 2:  # heavy thigh muscle blending into the body
            pp = union([pp, ellipse_path(hx - 10, hy + 10, 95 if i == 0 else 88, 120, 0.25)])
        else:
            pp = union([pp, ellipse_path(hx + 5, hy + 5, 62, 80, -0.2)])
        (parts_back if i % 2 == 1 else parts_front).append((pp, OH_BODY, 0.62 if i % 2 else 1.0))
        if i % 2 == 0 and cr < 0.5:
            contact_shadow(cv, fx + 6, fy + 2, w2 * 1.2, 9, 0.35 * (1 - cr))
    if cr > 0.3:
        contact_shadow(cv, s - 20, 4, 380, 28, 0.45 * cr)

    # ---- head
    nx, ny = sp[-1]
    hp = _get(pose, "head_pitch", 0.0) + 0.25 * cr + 0.02 * br
    tilt = _get(pose, "listen", 0.0)
    piv = (nx + 25, ny - 8)
    ang = hp + tilt * 0.6

    def H(path):
        return xform(path, piv[0], piv[1], ang, 1.0, 1.0 - 0.08 * abs(tilt), 0, 0)

    skull = catmull([(10, -40), (60, -74), (112, -66), (205, -22), (275, 42), (288, 66),
                     (246, 96), (150, 112), (60, 100), (20, 50)], closed=True)
    cheek = catmull([(20, 20), (70, 30), (96, 96), (40, 112), (0, 80)], closed=True)
    far_horn = limb_path([(96, -72), (150, -140), (212, -212), (236, -238)], [30, 22, 10, 2])
    near_horn = catmull([(92, -58), (124, -66), (158, -112), (172, -140), (163, -136),
                         (158, -150), (147, -141), (139, -148), (122, -106), (98, -64)],
                        closed=True)  # broken off halfway, jagged (the left brow horn)
    nose_horn = catmull([(196, -18), (214, -58), (222, -62), (226, -24)], closed=True)
    frill = H(_FRILL)
    head_parts = [(frill, OH_FRILL, 0.95), (H(far_horn), OH_BONE, 0.5), (H(skull), OH_BODY, 1.0), (H(cheek), OH_BODY, 0.92),
                  (H(nose_horn), OH_BONE, 0.9), (H(near_horn), OH_BONE, 1.0)]
    parts = parts_back + [(body, OH_BODY, 1.0)] + parts_front + head_parts
    sil = union([pt[0] for pt in parts])
    draw_form(cv, parts, L, sil=sil, texture=0.22 * detail, tex_scale=0.035, size=320)

    # frill markings: faded rose centre with bone rim and radial stripes
    cv.save()
    cv.clipPath(frill, doAntiAlias=True)
    fc = rot_pt((-60, -190), (0, 0), 0)
    fcx, fcy = rot_pt((piv[0] - 60, piv[1] - 190), piv, ang)
    g = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (fcx, fcy), 250, [c4(L.base(mix(OH_FRILL, (0.8, 0.45, 0.45), 0.3)), 0.55),
                          c4(L.base(OH_BONE), 0.0), c4(L.base(OH_BONE), 0.7)], [0, 0.6, 1.0]))
    cv.drawCircle(fcx, fcy, 300, g)
    sp_ = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                     Color4f=c4(L.base(scl(OH_FRILL, 0.8)), 0.35))
    for k in range(7):
        a = math.radians(-200 + 20 * k) + ang
        cv.drawLine(piv[0] - 40, piv[1] - 50, piv[0] - 40 + 260 * math.cos(a), piv[1] - 50 + 260 * math.sin(a), sp_)
    cv.restore()
    # beak, nostril, mouth line
    p = skia.Paint(AntiAlias=True, Color4f=c4(L.base(OH_BEAK)))
    beak = catmull([(236, 20), (282, 50), (290, 70), (250, 96), (228, 70)], closed=True)
    cv.drawPath(H(beak), p)
    ln = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                    Color4f=c4(L.base(scl(OH_BODY, 0.5)), 0.8), StrokeCap=skia.Paint.kRound_Cap)
    mouth = skia.Path()
    mouth.moveTo(236, 82)
    mouth.quadTo(170, 84, 120, 70)
    cv.drawPath(H(mouth), ln)
    nost = ellipse_path(212, 8, 12, 7, -0.4)
    cv.drawPath(H(nost), skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(OH_BODY, 0.35)))))
    # throat pulse when humming
    hum = _get(pose, "mouth", 0.0)
    if hum > 0:
        tp = skia.Paint(AntiAlias=True, Color4f=c4(L.base(OH_BELLY), 0.35 * hum))
        cv.drawPath(H(ellipse_path(70, 80, 50 + 6 * hum, 26 + 8 * hum)), tp)
    # the milky, clouded eye (detailed enough for extreme close-ups)
    ex, ey = rot_pt((piv[0] + 96, piv[1] - 28), piv, ang)
    blink = _get(pose, "blink", 0.0)
    glow = _get(pose, "eye_glow", None)
    eye_col = (0.80, 0.84, 0.86) if glow is None else glow
    # wrinkled skin around the socket
    wp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                    Color4f=c4(L.base(scl(OH_BODY, 0.55)), 0.35), StrokeCap=skia.Paint.kRound_Cap)
    for k_ in range(3):
        r_ = 23 + 5 * k_
        cv.drawArc(skia.Rect(ex - r_, ey - r_ * 0.8, ex + r_, ey + r_ * 0.8), 205 + 6 * k_, 100 - 12 * k_, False, wp)
    cv.drawCircle(ex, ey, 17.5, skia.Paint(AntiAlias=True, Color4f=c4(L.base(scl(OH_BODY, 0.38)))))
    eg = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (ex - 2, ey - 2), 14, [c4(scl(eye_col, 1.05)), c4(scl(eye_col, 0.82)), c4(scl(eye_col, 0.5))], [0, 0.55, 1.0]))
    cv.drawCircle(ex, ey, 13.5, eg)
    # iris ring faintly visible under the cataract, and the clouded pupil
    ir = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=c4(scl(eye_col, 0.55), 0.45))
    for k_ in range(10):
        a_ = k_ * math.pi / 5
        cv.drawLine(ex + math.cos(a_) * 5, ey + math.sin(a_) * 5, ex + math.cos(a_) * 10, ey + math.sin(a_) * 10, ir)
    cv.drawCircle(ex + 1, ey + 1, 5, skia.Paint(AntiAlias=True, Color4f=c4(scl(eye_col, 0.55), 0.55),
                                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.5)))
    # milky film + sky reflection arc + wet specular
    cv.drawCircle(ex, ey, 12, skia.Paint(AntiAlias=True, Color4f=c4((0.95, 0.97, 1.0), 0.18)))
    arc = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0, Color4f=c4(scl(eye_col, 1.5), 0.5),
                     StrokeCap=skia.Paint.kRound_Cap)
    cv.drawArc(skia.Rect(ex - 10, ey - 10, ex + 10, ey + 10), 200, 70, False, arc)
    cv.drawCircle(ex - 4.5, ey - 5, 2.6, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.85)))
    cv.drawCircle(ex + 4, ey + 4, 1.1, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.5)))
    if blink > 0:  # heavy eyelid
        lid = skia.Path()
        lid.addRect(skia.Rect(ex - 20, ey - 20, ex + 20, ey - 20 + 40 * blink))
        cv.save()
        cv.clipPath(ellipse_path(ex, ey, 17.5, 17.5))
        cv.drawPath(lid, skia.Paint(AntiAlias=True, Color4f=c4(L.base(OH_BODY))))
        cv.restore()
    rim_lid = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.0,
                         Color4f=c4(L.base(scl(OH_BODY, 0.3))))
    cv.drawCircle(ex, ey, 16.5, rim_lid)
    brow = skia.Path()
    brow.moveTo(ex - 22, ey - 12)
    brow.quadTo(ex, ey - 26, ex + 24, ey - 12)
    cv.drawPath(brow, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7,
                                 Color4f=c4(L.base(scl(OH_BODY, 0.6))), StrokeCap=skia.Paint.kRound_Cap))
    cv.restore()
    # world-space anchors for other shots (head top / frill curve / eye / beak)
    def W(pt):
        return (x + facing * scale * pt[0], y + scale * pt[1])
    return {
        "eye": W((ex, ey)),
        "beak": W(rot_pt((piv[0] + 280, piv[1] + 70), piv, ang)),
        "head_top": W(rot_pt((piv[0] + 60, piv[1] - 90), piv, ang)),
        "frill_nest": W(rot_pt((piv[0] - 70, piv[1] - 40), piv, ang)),
        "chin": W(rot_pt((piv[0] + 160, piv[1] + 125), piv, ang)),
        "sil_bounds": sil.getBounds(),
    }


# =====================================================================
#                                WISP
# =====================================================================
WI_BODY = (0.66, 0.42, 0.24)
WI_BELLY = (0.90, 0.80, 0.62)
WI_DARK = (0.32, 0.21, 0.13)
WI_BAND = (0.94, 0.90, 0.80)
WI_EYE = (1.0, 0.66, 0.16)
WI_GAIT_WALK = Gait(L=70, duty=0.6, phases=(0.0, 0.5), offsets=(-2, 4), lift=16)
WI_GAIT_RUN = Gait(L=150, duty=0.32, phases=(0.0, 0.5), offsets=(-2, 4), lift=34)


def wisp(cv, pose, light, x, y, scale, facing=1, detail=1.0):
    """pose keys: s (distance), gait ('walk'|'run'|None), hop (0..1 phase of a hop, with
    hop_len/hop_h), crouch 0..1, head_pitch, head_turn (-1 looks back), tuft 0..1,
    tail (rad), blink, breath, yawn 0..1, shake 0..1, curl 0..1 (sleep), t (seconds),
    beak_open 0..1, eye_dir (rad), carry (bool: pebble in beak), glow_eye (0..1)."""
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
    ox, oy = s, 0.0
    lean = 0.0
    if hop is not None:
        hl, hh = _get(pose, "hop_len", 60), _get(pose, "hop_h", 40)
        # anticipation squat, launch, arc, land, settle
        e = 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, (hop - 0.15) / 0.7)))
        ox = s + hl * e
        air = math.sin(math.pi * min(1, max(0, (hop - 0.15) / 0.7)))
        oy = -hh * air
        squat = 0.6 * math.exp(-((hop - 0.08) / 0.07) ** 2) + 0.5 * math.exp(-((hop - 0.92) / 0.07) ** 2)
        cr = max(cr, squat)
        lean = 0.25 * air
    if gait == "run":
        lean = 0.35
        oy -= 6 * abs(math.sin(2 * math.pi * s / G.L))
    sh = shake * math.sin(t * 55) * 5
    body_y = -72 + 30 * cr + 40 * curl + oy + 1.5 * br
    bx = ox + sh * 0.3
    body = ellipse_path(bx, body_y, 44 + 6 * curl, 35 - 4 * curl + 1.4 * br, -0.18 - lean + 0.2 * curl)
    # neck + head
    hp = _get(pose, "head_pitch", 0.0) + lean * 0.5
    turn = _get(pose, "head_turn", 0.0)
    neck_base = (bx + 22, body_y - 14)
    head_c = (bx + 58 - 16 * curl + sh, body_y - 58 + 44 * curl + 30 * cr * 0.5)
    head_c = rot_pt(head_c, neck_base, hp * 0.6)
    neck = tube([neck_base, ((neck_base[0] + head_c[0]) / 2 + 4, (neck_base[1] + head_c[1]) / 2 - 6),
                 (head_c[0] - 6, head_c[1] + 6)], [21, 16, 14], n=16)
    hd = 1 if turn >= 0 else -1
    yawn = _get(pose, "yawn", 0.0)
    bo = max(_get(pose, "beak_open", 0.0), yawn)

    def hpt(px, py):
        return rot_pt((head_c[0] + hd * px, head_c[1] + py), head_c, hp)

    upper = catmull([hpt(-16, -8), hpt(-4, -18), hpt(12, -16), hpt(34, -4 - 2 * bo), hpt(36, 2 - 3 * bo),
                     hpt(14, 4), hpt(-10, 10)], closed=True)
    lower = catmull([hpt(6, 4), hpt(32, 4 + 10 * bo), hpt(30, 8 + 11 * bo), hpt(4, 12)], closed=True)
    # tail with a feathered fan
    ta = _get(pose, "tail", 0.0) + 0.12 * math.sin(t * 2.3) + lean * 0.3
    tb = (bx - 30, body_y + 2)
    straight = []
    for k in range(5):
        u = k / 4
        straight.append((tb[0] - 150 * u, tb[1] - 6 * u + 26 * u * u * math.sin(ta) - 60 * u * math.sin(ta)))
    curled = []
    for k in range(5):  # wraps under and around the front of the body when asleep
        a_ = math.radians(170 - 150 * k / 4)
        curled.append((bx + 52 * math.cos(a_) * 1.1, body_y + 8 + 38 * math.sin(a_) * 0.9 + 16))
    tail_pts = [(sx_ + (cx_ - sx_) * curl, sy_ + (cy_ - sy_) * curl) for (sx_, sy_), (cx_, cy_) in zip(straight, curled)]
    tail = tube(tail_pts, [17, 12, 8, 5, 3], n=24)
    # feather fan: individual vanes splayed from the outer half of the tail
    fan = []
    for k in range(12):
        u = 0.3 + 0.7 * k / 11
        i0 = min(3, int(u * 4))
        fu = u * 4 - i0
        px_ = tail_pts[i0][0] + (tail_pts[i0 + 1][0] - tail_pts[i0][0]) * fu
        py_ = tail_pts[i0][1] + (tail_pts[i0 + 1][1] - tail_pts[i0][1]) * fu
        dx_ = tail_pts[i0 + 1][0] - tail_pts[i0][0]
        dy_ = tail_pts[i0 + 1][1] - tail_pts[i0][1]
        ang_ = math.atan2(dy_, dx_)
        for side in (-1, 1):
            spread = side * (0.75 - 0.4 * u) + 0.04 * math.sin(t * 3 + k)
            ln = 20 + 26 * u
            fa = ang_ + spread
            vane = catmull([(px_, py_), (px_ + math.cos(fa - 0.42) * ln * 0.55, py_ + math.sin(fa - 0.42) * ln * 0.55),
                            (px_ + math.cos(fa) * ln, py_ + math.sin(fa) * ln),
                            (px_ + math.cos(fa + 0.42) * ln * 0.55, py_ + math.sin(fa + 0.42) * ln * 0.55)],
                           closed=True)
            fan.append((vane, u))
    fan_path = union([f[0] for f in fan])
    # legs
    legs = []
    for i in (1, 0):
        hip = (bx - 2 + (4 if i else -2), body_y + 12)
        if curl > 0.5 or cr > 0.85:
            foot = (hip[0] + 18, -2)
        elif hop is not None:
            fx = ox + (4 if i else -2)
            foot = (fx, min(0.0, oy * 0.7 + 0))
        elif gait:
            (fx, fy), _ = G.foot(i, s)
            foot = (fx, fy)
        else:
            foot = (bx + (8 if i else -4), 0.0)
        ank = (foot[0] - 8, foot[1] - 22 + 10 * cr)
        knee = ik2(hip, ank, 30, 34, 1)
        lp = limb_path([hip, knee, ank, (foot[0] + 2, foot[1] - 2)], [18, 9, 6, 5])
        toes = skia.Path()
        toes.moveTo(foot[0] - 2, foot[1] - 2)
        toes.lineTo(foot[0] + 14, foot[1] - 1)
        toes.lineTo(foot[0] + 14, foot[1] + 1)
        toes.lineTo(foot[0] - 2, foot[1] + 1)
        toes.close()
        claw = catmull([(foot[0] + 2, foot[1] - 3), (foot[0] + 6, foot[1] - 11), (foot[0] + 10, foot[1] - 9),
                        (foot[0] + 5, foot[1] - 3)], closed=True)
        legs.append((union([lp, toes, claw]), WI_BODY, 0.6 if i == 1 else 1.0))
    arm = tube([(bx + 18, body_y - 4), (bx + 30, body_y + 8), (bx + 40, body_y + 6)], [7, 5, 3], n=14)
    chest = ellipse_path(bx + 26, body_y - 6, 24, 20, -0.5)
    parts = [legs[0], (fan_path, scl(WI_BODY, 0.7), 1.0), (tail, WI_BODY, 0.95), (chest, WI_BODY, 1.0), (body, WI_BODY, 1.0), (neck, WI_BODY, 1.0),
             (upper, WI_BODY, 1.0), (lower, WI_BODY, 0.9), legs[1], (arm, WI_BODY, 0.9)]
    sil = union([p[0] for p in parts])
    # downy fuzz first, so the fill hides the inner half of each stroke
    if detail > 0.3:
        fuzz(cv, sil, L.base(mix(WI_BODY, WI_BELLY, 0.2)), 4.2 + 3 * shake, n=700, seed=4,
             jitter_t=t + shake * 10, width=1.5, alpha=0.65)
    draw_form(cv, parts, L, sil=sil, texture=0.12 * detail, tex_scale=0.09, size=90)
    # belly cream + tail bars + the one pale band
    cv.save()
    cv.clipPath(body, doAntiAlias=True)
    cv.drawOval(skia.Rect(bx - 30, body_y + 2, bx + 34, body_y + 34),
                skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_BELLY), 0.8),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    cv.restore()
    cv.save()
    cv.clipPath(fan_path, doAntiAlias=True)
    for fp_, u in fan:
        if 0.62 < u < 0.78:  # the single pale band
            cv.drawPath(fp_, skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_BAND), 0.95)))
    vp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                    Color4f=c4(L.base(scl(WI_DARK, 0.6)), 0.6))
    for k in range(len(tail_pts) - 1):
        cv.drawLine(*tail_pts[k], *tail_pts[k + 1], vp)
    cv.restore()
    # the tuft: springs upright when excited
    tu = _get(pose, "tuft", 0.3)
    tp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.6,
                    StrokeCap=skia.Paint.kRound_Cap, Color4f=c4(L.base(scl(WI_BODY, 1.15))))
    base = hpt(-2, -17)
    for k in range(5):
        a = math.radians(-170 + 70 * tu + 12 * k * (0.4 + tu)) + hp
        a = a if hd > 0 else math.pi - a
        wob = math.sin(t * 9 + k) * 0.05 * tu
        ln = 12 + 5 * tu - abs(k - 2) * 1.5
        pth = skia.Path()
        pth.moveTo(*base)
        pth.quadTo(base[0] + math.cos(a + wob - 0.3 * hd) * ln * 0.6, base[1] + math.sin(a + wob) * ln * 0.6,
                   base[0] + math.cos(a + wob) * ln, base[1] + math.sin(a + wob) * ln)
        cv.drawPath(pth, tp)
    # the big amber night-eye
    ex, ey = hpt(6, -6)
    blink = _get(pose, "blink", 0.0)
    cv.drawCircle(ex, ey, 7.8, skia.Paint(AntiAlias=True, Color4f=c4((0.08, 0.05, 0.03))))
    ge = _get(pose, "glow_eye", 0.0)
    eg = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (ex, ey), 6.8, [c4(scl(WI_EYE, 1.1 + ge)), c4(scl(WI_EYE, 0.75 + ge * 0.5))], [0.3, 1.0]))
    cv.drawCircle(ex, ey, 6.6, eg)
    ed = _get(pose, "eye_dir", 0.0)
    cv.drawCircle(ex + 1.8 * hd * math.cos(ed), ey + 1.8 * math.sin(ed), 3.4,
                  skia.Paint(AntiAlias=True, Color4f=c4((0.03, 0.02, 0.02))))
    cv.drawCircle(ex - 2 * hd, ey - 2.4, 1.6, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), 0.95)))
    if blink > 0:
        cv.save()
        cv.clipPath(ellipse_path(ex, ey, 8.2, 8.2))
        cv.drawRect(skia.Rect(ex - 9, ey - 9, ex + 9, ey - 9 + 18 * blink),
                    skia.Paint(AntiAlias=True, Color4f=c4(L.base(WI_BODY))))
        cv.restore()
    if _get(pose, "carry", False):
        bxp, byp = hpt(30, 4)
        pebble(cv, bxp, byp + 3, 11, L, glint=0.2)
    cv.restore()

    def Wp(pt):
        return (x + facing * scale * pt[0], y + scale * pt[1])
    return {"eye": Wp((ex, ey)), "beak": Wp(hpt(34, 2)), "head": Wp(head_c), "body": Wp((bx, body_y))}


def pebble(cv, x, y, r, light, rot=0.3, glint=0.0):
    """The white quartz crescent-moon pebble."""
    outer = ellipse_path(x, y, r, r)
    inner = ellipse_path(x + r * 0.45, y - r * 0.25, r * 0.78, r * 0.78)
    cres = skia.Op(outer, inner, skia.PathOp.kDifference_PathOp) or outer
    cres = xform(cres, 0, 0, rot, 1, 1, x, y)
    g = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - r * 0.3, y - r * 0.3), r * 1.4,
        [c4(light.base((1.3, 1.3, 1.25))), c4(light.base((0.8, 0.8, 0.78)))], [0, 1]))
    cv.drawPath(cres, g)
    if glint > 0:
        gx, gy = x - r * 0.4, y - r * 0.3
        gp = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                        Shader=skia.GradientShader.MakeRadial((gx, gy), r * 1.2, [c4((1, 1, 0.95), glint), c4((1, 1, 1), 0)], [0, 1]))
        cv.drawCircle(gx, gy, r * 1.2, gp)
        sp = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Style=skia.Paint.kStroke_Style, StrokeWidth=max(0.8, r * 0.12))
        for ang in (0.0, math.pi / 2, math.pi / 4, -math.pi / 4):
            ln = r * (2.6 if ang in (0.0, math.pi / 2) else 1.3) * glint
            sp.setShader(skia.GradientShader.MakeLinear([(gx - ln * math.cos(ang), gy - ln * math.sin(ang)),
                                                         (gx + ln * math.cos(ang), gy + ln * math.sin(ang))],
                                                        [c4((1, 1, 1), 0), c4((1, 1, 1), glint), c4((1, 1, 1), 0)], [0, 0.5, 1]))
            cv.drawLine(gx - ln * math.cos(ang), gy - ln * math.sin(ang), gx + ln * math.cos(ang), gy + ln * math.sin(ang), sp)


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
    head = xform(catmull([(-24, -24), (30, -34), (96, -18), (140, 6), (136, 20 + 7 * bo), (94, 24), (20, 28),
                          (-22, 14)], closed=True), hx, hy, hang)
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
