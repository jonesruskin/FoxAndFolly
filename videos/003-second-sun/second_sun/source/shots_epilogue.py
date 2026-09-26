"""EPILOGUE — WHAT THE STONE REMEMBERS (S27–S31)."""
import math

import numpy as np
import skia

import timeline as TL
import world as Wd
from creatures import pebble
from foxfolly.anim import Track, clamp, ease_in_out_sine, smoothstep, window
from rig import Light, c4, catmull, ellipse_path, mix, scl, tube, union, xform
from shots_act1 import blinks
from world import LOOKS, W, H, light_of

EV = TL.EV
BONE = (0.84, 0.76, 0.62)


# ----------------------------------------------------------------- fossils
def fossils(cv, x, y, s, light, bone=BONE, glint=0.0, matrix=None):
    """The Triceratops skull with the broken brow horn, the small skeleton curled in
    the curve of its frill, and the white crescent pebble between its tiny claws."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    b = light.base(bone)
    stain = light.base(scl(bone, 0.72))
    rng = np.random.default_rng(11)
    frill = catmull([(-40, 0), (-200, -50), (-320, -170), (-330, -300), (-230, -380), (-90, -360), (20, -280),
                     (70, -150), (60, -60)], closed=True)
    skull = catmull([(20, -110), (110, -140), (220, -118), (300, -70), (338, -20), (350, 20), (322, 40),
                     (210, 50), (80, 44), (10, 0)], closed=True)
    rostral = catmull([(330, -20), (372, 8), (360, 42), (326, 40)], closed=True)
    far_horn = tube([(150, -128), (206, -226), (262, -318), (282, -352)], [34, 24, 11, 3], n=16)
    near_horn = catmull([(128, -110), (176, -118), (212, -170), (222, -198), (212, -190), (206, -206), (194, -194),
                         (186, -202), (168, -160), (138, -116)], closed=True)          # broken off halfway
    nose = catmull([(272, -66), (284, -112), (296, -114), (304, -60)], closed=True)
    jaw = catmull([(30, 34), (180, 58), (330, 46), (318, 82), (170, 98), (40, 76)], closed=True)
    parts = [frill, far_horn, skull, rostral, nose, near_horn, jaw]
    sil = union(parts)
    cv.drawPath(sil, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, -380), (0, 100)], [c4(scl(b, 1.08)), c4(scl(b, 0.8))], [0, 1])))
    cv.save()
    cv.clipPath(sil, doAntiAlias=True)
    # stains, vascular grooves and hairline cracks: bone, not a mask
    for i in range(26):
        cv.drawOval(skia.Rect(-340 + rng.random() * 700, -380 + rng.random() * 480, 0, 0).makeOutset(10 + 30 * rng.random(), 6 + 14 * rng.random()),
                    skia.Paint(AntiAlias=True, Color4f=c4(stain, 0.25)))
    gp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6, Color4f=c4(scl(b, 0.7), 0.25))
    for k in range(9):
        a_ = math.radians(195 + k * 12)
        cv.drawLine(-60, -120, -60 + 300 * math.cos(a_), -120 + 280 * math.sin(a_), gp)
    cp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4, Color4f=c4(scl(b, 0.35), 0.8))
    for i in range(7):
        px_, py_ = -300 + rng.random() * 600, -340 + rng.random() * 400
        path = skia.Path()
        path.moveTo(px_, py_)
        for j in range(4):
            px_ += (rng.random() - 0.3) * 50
            py_ += (rng.random() - 0.5) * 40
            path.lineTo(px_, py_)
        cv.drawPath(path, cp)
    cv.restore()
    # scalloped frill edge (epoccipitals), orbit, nostril, teeth row
    for k in range(13):
        a_ = math.radians(185 + k * 10.5)
        ex_, ey_ = -150 + 205 * math.cos(a_), -190 + 195 * math.sin(a_)
        cv.drawOval(skia.Rect(ex_ - 13, ey_ - 9, ex_ + 13, ey_ + 9), skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 0.95))))
    cv.drawCircle(160, -66, 24, skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 0.42))))
    cv.drawCircle(160, -66, 24, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                                           Color4f=c4(scl(b, 0.7))))
    cv.drawPath(ellipse_path(292, -24, 18, 12, -0.4), skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 0.45))))
    tp = skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 0.6)))
    for k in range(10):
        cv.drawRect(skia.Rect(90 + 20 * k, 44, 102 + 20 * k, 52), tp)
    # the small skeleton curled in the curve of the frill, by the neck
    cx, cy = -140, -70
    bp = skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 1.05)))
    sh = skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 0.45), 0.8))
    spine = []
    for k in range(24):
        a_ = math.radians(-40 + k * 14.5)
        r = 78 - k * 1.8
        spine.append((cx + r * math.cos(a_), cy + r * math.sin(a_) * 0.82))
    for k, (vx, vy) in enumerate(spine):
        cv.drawCircle(vx + 1.5, vy + 1.5, 6.2 - k * 0.2, sh)
        cv.drawCircle(vx, vy, 6.0 - k * 0.2, bp)
    rib = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4, Color4f=c4(scl(b, 1.0)),
                     StrokeCap=skia.Paint.kRound_Cap)
    for k in range(3, 10):
        vx, vy = spine[k]
        cv.drawLine(vx, vy, vx + (cx - vx) * 0.42, vy + (cy - vy) * 0.42, rib)
    hx, hy = spine[0][0] + 18, spine[0][1] - 12
    tiny = catmull([(hx - 16, hy - 8), (hx + 6, hy - 16), (hx + 34, hy - 4), (hx + 38, hy + 4), (hx + 4, hy + 9),
                    (hx - 14, hy + 5)], closed=True)
    cv.drawPath(tiny, bp)
    cv.drawCircle(hx + 2, hy - 3, 7.5, skia.Paint(AntiAlias=True, Color4f=c4(scl(b, 0.4))))   # the big night-eye socket
    lb = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.6, Color4f=c4(scl(b, 1.0)),
                    StrokeCap=skia.Paint.kRound_Cap)
    cv.drawLine(cx + 12, cy + 22, cx + 36, cy + 38, lb)
    cv.drawLine(cx + 36, cy + 38, cx + 28, cy + 58, lb)
    cv.drawLine(cx - 6, cy + 26, cx + 20, cy + 46, lb)
    pebble(cv, cx + 34, cy + 10, 10, light, rot=0.4, glint=glint)
    cv.drawLine(cx + 20, cy + 0, cx + 30, cy + 20, lb)
    cv.drawLine(cx + 26, cy - 2, cx + 40, cy + 20, lb)
    cv.restore()


# ======================================================================
LAYERS = [(5, (0.92, 0.90, 0.86))] + [(int(10 + 22 * (0.5 + 0.5 * math.sin(i * 2.3))), c) for i, c in enumerate(
    [(0.62, 0.50, 0.38), (0.72, 0.62, 0.48), (0.52, 0.44, 0.40), (0.78, 0.66, 0.50), (0.58, 0.40, 0.30),
     (0.70, 0.60, 0.46), (0.46, 0.40, 0.36), (0.80, 0.70, 0.54), (0.60, 0.46, 0.34), (0.74, 0.64, 0.50),
     (0.54, 0.46, 0.40), (0.68, 0.54, 0.40)])]


def S27(F, u, dur, t):
    """Deep time: the mound is buried, a thin pale boundary marks the impact; stars wheel;
    the land rises and erodes into badlands. The Saddle persists."""
    cv = F.cv
    base = 610.0
    dep = ease_in_out_sine(clamp((t - 254.3) / 3.9))
    total = sum(h for h, c in LAYERS)
    Hd = dep * total
    ero = ease_in_out_sine(clamp((t - 258.2) / 2.8))
    season = 0.5 + 0.5 * math.sin(t * 2.2)
    lk = dict(LOOKS["night"])
    lk["hor"] = mix((0.10, 0.12, 0.22), (0.18, 0.12, 0.16), season)
    Wd.sky(cv, dict(lk, stars=0.0), t, horizon=base)
    Wd.stars(cv, 1.0, t, rot=(t - 254) * 22, cx=W * 0.55, cy=-200, scale=1.2)
    ridge = Wd.ridge_path(360, 40, seed=91, saddle_x=1330)
    Wd.fill(cv, ridge, (0.08, 0.08, 0.12))
    xs = np.linspace(-20, W + 20, 200)
    rng_n = Wd.fractal_noise(1, 512, beta=2.4, seed=93)[0]
    prof = np.interp(np.linspace(0, 511, len(xs)), np.arange(512), rng_n)
    eroded = base - total + 60 + 170 * (prof - 0.5) + 90 * np.abs(np.sin(xs / 140.0))
    surf_y = (base - Hd) * (1 - ero) + eroded * ero
    surf = skia.Path()
    surf.moveTo(-20, H + 20)
    for x, y in zip(xs, np.broadcast_to(surf_y, xs.shape)):
        surf.lineTo(float(x), float(y))
    surf.lineTo(W + 20, H + 20)
    surf.close()
    cv.save()
    cv.clipPath(surf, doAntiAlias=True)
    cv.drawRect(skia.Rect(0, base, W, H), skia.Paint(Color4f=c4((0.30, 0.26, 0.24))))
    for k in range(9):
        cv.drawRect(skia.Rect(0, base + 20 + k * 52, W, base + 44 + k * 52), skia.Paint(Color4f=c4((0.26 + 0.03 * (k % 2), 0.22, 0.2))))
    fossils(cv, 900, base + 70, 0.5, Light(ambient=(0.55, 0.48, 0.42)))
    y = base
    for h, col in LAYERS:
        top = y - h
        vis = clamp((Hd - (base - y)) / max(1, h))
        if vis > 0:
            cv.drawRect(skia.Rect(0, y - h * vis, W, y + 0.5), skia.Paint(Color4f=c4(col)))
        y = top
    cv.restore()
    F.post = {"grade": "epi_bad", "bloom": (0.6, 0.4), "vignette": 0.45}


# ======================================================================
def badlands(cv, t, lk, cam_x=0.0, star=(1450, 210), star_k=1.0, horizon=640):
    Wd.sky(cv, lk, t, horizon=horizon)
    Wd.glow(cv, star[0], star[1], 70, (1.0, 0.95, 0.85), 0.45 * star_k)
    cv.drawCircle(star[0], star[1], 2.6, skia.Paint(AntiAlias=True, Color4f=c4((3, 2.9, 2.6), star_k)))
    for li, (base, amp, seed, par, col) in enumerate([(560, 50, 101, 0.1, (0.46, 0.40, 0.50)),
                                                       (640, 80, 102, 0.3, (0.62, 0.46, 0.38)),
                                                       (760, 110, 103, 0.6, (0.72, 0.52, 0.36))]):
        cv.save()
        cv.translate(-cam_x * par, 0)
        path = Wd.ridge_path(base, amp, seed=seed, saddle=(li == 0), saddle_x=1330 + cam_x * par, x0=-600, x1=W + 900)
        c = Wd.fogged(col, lk, 0.45 - 0.15 * li)
        Wd.vgrad(cv, path, base - amp, H, c, scl(c, 0.75))
        cv.save()
        cv.clipPath(path, doAntiAlias=True)
        for k in range(14):  # horizontal strata bands
            yy = base - amp + 22 * k + 6 * math.sin(k * 1.7 + li)
            cv.drawRect(skia.Rect(-600, yy, W + 900, yy + 7 + 4 * (k % 3)),
                        skia.Paint(Color4f=c4(scl(c, 0.82 + 0.3 * ((k * 0.37) % 1.0)), 0.55)))
        cv.restore()
        cv.restore()


def hands(cv, x, y, s, light, stroke_phase):
    """A soft brush in a gloved hand, entering from the top right."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    cv.rotate(-35 + 8 * math.sin(stroke_phase * math.pi * 2))
    handle = skia.Path()
    handle.addRoundRect(skia.Rect(-9, -420, 9, 20), 8, 8)
    cv.drawPath(handle, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-9, 0), (9, 0)], [c4(light.base((0.46, 0.28, 0.14))), c4(light.base((0.30, 0.18, 0.09)))], [0, 1])))
    fer = skia.Path()
    fer.addRoundRect(skia.Rect(-12, 14, 12, 40), 3, 3)
    cv.drawPath(fer, skia.Paint(AntiAlias=True, Color4f=c4(light.base((0.72, 0.68, 0.62)))))
    bp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8,
                    Color4f=c4(light.base((0.60, 0.46, 0.30))), StrokeCap=skia.Paint.kRound_Cap)
    bend = 10 * math.sin(stroke_phase * math.pi * 2)
    for k in range(11):
        u = k / 10
        cv.drawLine(-10 + 20 * u, 40, -14 + 28 * u + bend, 104, bp)
    glove = skia.Paint(AntiAlias=True, Color4f=c4(light.base((0.52, 0.44, 0.36))))
    cv.drawPath(catmull([(-40, -330), (30, -350), (46, -250), (20, -200), (-30, -210), (-52, -270)], closed=True), glove)
    for k in range(3):
        cv.drawPath(ellipse_path(-14 + 16 * k, -196 + 10 * k, 13, 22, 0.2), glove)
    cv.drawPath(ellipse_path(-44, -236, 12, 26, -0.6), glove)
    cv.restore()


def S28(F, u, dur, t):
    lk = LOOKS["badlands"]
    cv = F.cv
    if t < 264.0:                                  # present-day badlands, the same Saddle
        badlands(cv, t, lk, cam_x=20 * u, star_k=0.5)
        F.post = {"grade": "epi_bad", "bloom": (0.6, 0.45), "black": 1 - smoothstep(261.0, 262.0, t)}
        return
    # the dig: dust brushed away
    L = Light(ambient=(0.92, 0.80, 0.70), key=(1.0, 0.8, 0.6), key_dir=-2.6)
    cv.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (0, H)], [c4((0.70, 0.56, 0.42)), c4((0.52, 0.40, 0.30))], [0, 1])))
    rng = np.random.default_rng(5)
    for i in range(160):
        x, y, r = rng.random() * W, rng.random() * H, 2 + 8 * rng.random()
        cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=c4((0.45 + 0.2 * rng.random(), 0.36, 0.28), 0.5)))
    fx, fy, fs = 1080, 700, 1.25
    fossils(cv, fx, fy, fs, L, glint=window(t, 268.8, 271.5, 0.4, 1.0))
    # the dust layer, cleared where the brush has passed
    cv.saveLayer(None, None)
    cv.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=c4((0.66, 0.53, 0.40), 0.97)))
    for i in range(300):
        x, y, r = rng.random() * W, rng.random() * H, 3 + 10 * rng.random()
        cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=c4((0.58 + 0.15 * rng.random(), 0.46, 0.34), 0.8)))
    clear = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kDstOut,
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
    strokes = [(fx + 120, fy - 90, 330, 120), (fx - 150, fy - 300, 300, 170), (fx - 180, fy - 20, 260, 140),
               (fx + 300, fy - 330, 260, 150)]
    for (sx, sy, rx, ry), ts in zip(strokes, EV["brush"]):
        k = ease_in_out_sine(clamp((t - ts) / 1.3))
        if k > 0:
            cv.drawOval(skia.Rect(sx - rx * k, sy - ry * k, sx + rx * k, sy + ry * k), clear)
    cv.restore()
    # the hand and brush sweeping
    cur = None
    for (sx, sy, rx, ry), ts in zip(strokes, EV["brush"]):
        if ts - 0.3 <= t < ts + 1.4:
            cur = (sx, sy, rx, ts)
    if cur is not None:
        sx, sy, rx, ts = cur
        ph = (t - ts) / 0.45
        hands(cv, sx + rx * 0.6 * math.sin(ph * math.pi), sy - 40, 1.2, L, ph)
        Wd.ash(cv, t, 0.5, density=0.08, col=(0.8, 0.7, 0.55), wind_x=40, fall=-20)
    F.post = {"grade": "epi_bad", "bloom": (0.7, 0.35), "vignette": 0.45}


def S29(F, u, dur, t):
    """A slow drift across the badlands; one bright evening star, harmless now."""
    lk = dict(LOOKS["badlands"])
    lk["zen"] = mix(lk["zen"], (0.05, 0.07, 0.18), smoothstep(272, 291, t))
    badlands(F.cv, t, lk, cam_x=260 + 22 * u, star_k=1.0)
    F.post = {"grade": "epi_bad", "bloom": (0.55, 0.5), "vignette": 0.5}


# ======================================================================
def S30(F, u, dur, t):
    """The museum, evening. A grandmother and a child before the two fossils, displayed as found."""
    cv = F.cv
    cv.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (0, H)], [c4((0.05, 0.035, 0.03)), c4((0.10, 0.07, 0.05))], [0, 1])))
    # windows: evening blue beyond the hall
    for i in range(4):
        x = 180 + i * 440
        cv.drawRect(skia.Rect(x, 120, x + 220, 560), skia.Paint(Color4f=c4((0.10, 0.14, 0.26), 0.9)))
        Wd.glow(cv, x + 110, 300, 260, (0.2, 0.3, 0.55), 0.12)
    floor = skia.Path()
    floor.addRect(skia.Rect(0, 860, W, H))
    cv.drawPath(floor, skia.Paint(Color4f=c4((0.12, 0.08, 0.06))))
    # warm pools of light
    for (x, r, a) in [(1180, 520, 0.55), (420, 360, 0.22), (1780, 300, 0.2)]:
        cv.save()
        cv.translate(x, 920)
        cv.scale(1.0, 0.22)
        Wd.glow(cv, 0, 0, r, (1.0, 0.72, 0.4), a)
        cv.restore()
    Wd.glow(cv, 1180, 420, 560, (1.0, 0.70, 0.38), 0.18)
    # plinth and the fossils, displayed together just as they were found
    plinth = skia.Path()
    plinth.addRect(skia.Rect(900, 700, 1460, 880))
    cv.drawPath(plinth, skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, 700), (0, 880)], [c4((0.30, 0.22, 0.16)), c4((0.14, 0.10, 0.08))], [0, 1])))
    fossils(cv, 1200, 670, 0.8, Light(ambient=(1.0, 0.82, 0.6)), glint=0.35)
    glass = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, Color4f=c4((1, 0.9, 0.75), 0.25))
    cv.drawRect(skia.Rect(890, 330, 1470, 700), glass)
    cv.drawLine(930, 340, 1010, 690, skia.Paint(AntiAlias=True, StrokeWidth=6, Color4f=c4((1, 0.9, 0.8), 0.06)))
    # silhouettes, mirroring Old Horn and Wisp
    take = EV["hand_take"]
    reach = ease_in_out_sine(clamp((t - (take - 1.4)) / 1.4))
    squeeze = window(t, take + 0.4, take + 1.3, 0.2, 0.5)
    sil = (0.02, 0.015, 0.012)
    # a softly lit wall panel behind them so their silhouettes read
    Wd.glow(cv, 620, 600, 520, (0.55, 0.36, 0.2), 0.55)
    human(cv, 560, 880, 520, sil, "adult", hand_down=0.4 * reach + 0.05 * squeeze, t=t)
    human(cv, 720, 880, 400, sil, "child", reach=reach, t=t)
    F.post = {"grade": "epi_museum", "bloom": (0.55, 0.6), "vignette": 0.5,
              "black": 1 - smoothstep(291.0, 292.2, t)}


def human(cv, x, y, h, col, kind, reach=0.0, hand_down=0.0, t=0.0):
    """Elegant silhouettes: a grandmother (shawl, bun, slight stoop) and a small child."""
    cv.save()
    cv.translate(x, y)
    s = h / 100.0
    cv.scale(s, s)
    br = 0.5 * math.sin(t * 2 * math.pi / 4.2)
    p = skia.Paint(AntiAlias=True, Color4f=c4(col))
    if kind == "adult":
        coat = catmull([(-15, 0), (-17, -30), (-15, -58), (-13, -70 + br), (-7, -76 + br), (4, -78 + br),
                        (13, -73 + br), (16, -60), (19, -30), (18, 0)], closed=True)
        shawl = catmull([(-14, -72 + br), (0, -80 + br), (15, -72 + br), (19, -56), (8, -52), (-12, -54)], closed=True)
        head = ellipse_path(6, -87 + br, 7.0, 8.2, 0.15)
        bun = ellipse_path(0, -95 + br, 4.2, 3.6)
        neck = ellipse_path(4, -79 + br, 3.5, 4.0)
        hx, hy = 16 + 2 * hand_down, -42 + 6 * hand_down
        arm = tube([(12, -70 + br), (18, -56), (hx, hy)], [5.5, 4.5, 3.8], n=12)
        hand = ellipse_path(hx, hy + 2, 3.0, 3.6)
        cv.drawPath(union([coat, shawl, head, bun, neck, arm, hand]), p)
    else:
        body = catmull([(-9, 0), (-10, -22), (-11, -36), (-7, -44), (0, -46), (7, -44), (10, -36), (9, -22),
                        (8, 0)], closed=True)
        head = ellipse_path(0, -55, 7.5, 8.0)
        tail = ellipse_path(-7, -58, 3.2, 4.5, 0.4)
        # the child's arm rises to take her hand
        ex = -8 - 22 * reach
        ey = -30 - 18 * reach
        arm = tube([(-6, -42), (-8 - 10 * reach, -36 - 12 * reach), (ex, ey)], [3.6, 3.0, 2.6], n=10)
        cv.drawPath(union([body, head, tail, arm, ellipse_path(ex, ey, 2.4, 2.6)]), p)
    cv.restore()


def S31(F, u, dur, t):
    F.cv.clear(skia.Color4f(0.008, 0.008, 0.012, 1))
    Wd.glow(F.cv, 960, 300, 160, (1.0, 0.9, 0.75), 0.08 * (1 - smoothstep(307.0, 309.0, t)))
    F.post = {"grade": "cold_open", "bloom": (0.8, 0.2), "vignette": 0.3, "black": smoothstep(308.4, 309.0, t)}


SHOTS = {"S27": S27, "S28": S28, "S29": S29, "S30": S30, "S31": S31}
