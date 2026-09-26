"""Reusable set-ups: THE LAKE lock-off, the Split Tree camp, POV language."""
import math

import numpy as np
import skia

import world as Wd
from creatures import azhdarchid, edmonto
from rig import c4, catmull, mix, scl, tube
from world import H, W

# ---------------------------------------------------------------- THE LAKE
# One camera, built once, reused in S3, S15, S18-S21 and S24.
LAKE = dict(ridge_base=548, water_y0=630, water_y1=905, tree_x=420, tree_y=940, tree_h=1180)
_RIDGE = None
_HILL = None
_BANK = None
HERD = [  # x, scale, facing, phase
    (720, 0.105, 1, 0.1), (812, 0.12, -1, 1.7), (905, 0.11, 1, 3.1), (1010, 0.125, 1, 0.6),
    (1110, 0.10, -1, 2.4), (1205, 0.115, 1, 4.2), (1275, 0.095, -1, 5.0),
]


def _geom():
    global _RIDGE, _HILL, _BANK
    if _RIDGE is None:
        _RIDGE = Wd.ridge_path(LAKE["ridge_base"], 62, seed=11)
        _HILL = Wd.ridge_path(608, 34, seed=12, saddle=False)
        _BANK = catmull([(-60, 900), (300, 918), (700, 912), (1100, 922), (1500, 915), (1980, 908),
                         (1980, 1200), (-60, 1200)], closed=True)
    return _RIDGE, _HILL, _BANK


def treeline(cv, lk, t, after=0.0, burn=0.0):
    rng = np.random.default_rng(31)
    col = Wd.fogged(scl(lk["plant"], 0.55), lk, lk["fog_mid"] + 0.12)
    col = mix(col, Wd.fogged((0.08, 0.08, 0.08), lk, 0.4), after)
    x = -20.0
    while x < W + 20:
        h = 40 + 70 * rng.random()
        kind = rng.random()
        if kind < 0.55:
            Wd.conifer(cv, x, 634, h, col, t, seed=int(x) + 1000, bare=after)
        elif kind < 0.8:
            Wd.palm(cv, x, 634, h * 0.7, col, t, seed=int(x) + 1000, burnt=after)
        else:
            Wd.fill(cv, Wd.ellipse_path(x, 630, 30 + 20 * rng.random(), 16), col) if after < 0.5 else None
        x += 18 + 30 * rng.random()
    band = skia.Path()
    band.addRect(skia.Rect(-10, 624, W + 10, 640))
    Wd.fill(cv, band, col)


def lake(F, t, lk, state):
    """Draw THE LAKE. state keys: star_k, herd ('drink'|'settle'|'alarm'|'flee'|None), herd_t,
    after (0..1 ash world), surge (0..1 water rising), azhd (x progress 0..1 or None),
    dflies (bool), ff (firefly amount), burn (0..1 ridge fires), flash (0..1), beads (0..1)."""
    cv = F.cv
    ridge, hill, bank = _geom()
    after = state.get("after", 0.0)
    Wd.sky(cv, lk, t, horizon=LAKE["water_y0"])
    if state.get("star_k", 0) > 0:
        Wd.the_star(cv, Wd.SADDLE_X + 8, 470, state["star_k"], t)
    if state.get("flash", 0) > 0:
        fk = state["flash"]
        Wd.glow(cv, Wd.SADDLE_X, 590, 700 * fk, (1.0, 0.92, 0.8), 0.45 * fk)
        Wd.glow(cv, Wd.SADDLE_X, 596, 180 * fk, (1.0, 1.0, 0.95), 1.3 * fk)
    if state.get("azhd") is not None:
        u = state["azhd"]
        azhdarchid(cv, t, Wd.light_of(lk, 0.5), -200 + (W + 400) * u, 250 - 60 * u, 0.28, 1)
    # the ridge with the Saddle, then the nearer hill
    rc = Wd.fogged(scl(lk["plant"], 0.35), lk, lk["fog_far"])
    rc = mix(rc, Wd.fogged((0.2, 0.2, 0.2), lk, lk["fog_far"]), after)
    Wd.vgrad(cv, ridge, 480, 640, rc, Wd.fogged(rc, lk, 0.2))
    if state.get("burn", 0) > 0:
        # fires spread along the ridge line
        for i, fx in enumerate(np.linspace(80, 1840, 14)):
            if (i * 0.37) % 1.0 < state["burn"]:
                Wd.flames(cv, fx, 604 + 8 * math.sin(i), 70, 26 + 10 * (i % 3), t, a=0.9, seed=i)
    hc = Wd.fogged(scl(lk["plant"], 0.45), lk, lk["fog_mid"])
    hc = mix(hc, Wd.fogged((0.16, 0.16, 0.16), lk, lk["fog_mid"]), after)
    Wd.vgrad(cv, hill, 580, 640, hc, Wd.fogged(hc, lk, 0.1))
    treeline(cv, lk, t, after=after)
    # the herd on the far shore
    mode = state.get("herd")
    if mode and after < 0.5:
        L = Wd.light_of(lk, 0.45)
        ht = state.get("herd_t", t)
        for i, (hx, sc, fc, ph) in enumerate(HERD):
            pose = {"t": t + ph, "s": 0.0}
            x = hx
            if mode == "drink":
                pose["head"] = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 0.5 + ph))
            elif mode == "settle":
                pose["head"] = 0.25 + 0.2 * math.sin(t * 0.3 + ph)
            elif mode == "alarm":
                pose["head"] = 0.0
                pose["alarm"] = min(1.0, max(0.0, (ht - ph * 0.12) * 1.5))
                fc = 1   # everyone turns to face the south-east (the Saddle side)
            elif mode == "flee":
                pose["s"] = ht * 520 * (1 + 0.2 * ph)
                pose["head"] = 0.0
                pose["alarm"] = 0.4
                pose["bellow"] = max(0, math.sin(ht * 3 + ph))
                fc = -1
            edmonto(cv, pose, L, x, 648, sc, fc, detail=0.3)
    # water: mirror everything above the far shore
    y0, y1 = LAKE["water_y0"], LAKE["water_y1"]
    surge = state.get("surge", 0.0)
    wy0 = int(y0 - 30 * surge)
    img = F.snapshot()
    if F.s != 1.0:
        sy0, sy1 = int(wy0 * F.s), int(y1 * F.s)
    else:
        sy0, sy1 = wy0, y1
    _reflect_scaled(img, sy0, sy1, t, F.s, lk, surge)
    F.put(img)
    Wd.water_glints(cv, wy0, y1, t, mix(lk["hor"], (1, 1, 1), 0.3), a=0.5 if after < 0.5 else 0.12)
    Wd.mist(cv, y0 + 30, 90, lk["mist_col"], lk["mist"] * (1 - 0.5 * after), t)
    if state.get("dflies"):
        for i, (a_, b_, c_, d_, e_, f_) in enumerate(Wd.DF):
            x = (a_ * W + t * (60 + 80 * b_) * (1 if c_ > 0.5 else -1)) % (W + 200) - 100
            y = y0 + 60 + 180 * d_ + 14 * math.sin(t * (3 + 3 * e_) + i)
            Wd.dragonfly(cv, x, y, t + i, s=0.8 + 0.5 * f_, col=mix((0.2, 0.55, 0.95), lk["key"], 0.2),
                         heading=math.pi if c_ <= 0.5 else 0.0)
    if state.get("ff", 0) > 0:
        Wd.fireflies(cv, t, state["ff"], 0, W, 640, 1000)
    return dict(sil=None)


def _reflect_scaled(img, y0, y1, t, s, lk, surge):
    Wd.reflect(img, y0, y1, t * 1.0, strength=0.78, tint=lk["water"], ripple=s, surge=surge)


def lake_foreground(F, t, lk, state):
    """Near bank, the Split Tree and foreground plants (drawn after characters on the far side)."""
    cv = F.cv
    _, _, bank = _geom()
    after = state.get("after", 0.0)
    bc = mix(scl(lk["plant"], 0.35), (0.12, 0.12, 0.12), after)
    Wd.vgrad(cv, bank, 900, 1080, Wd.fogged(bc, lk, 0.15), scl(bc, 0.5))
    char = state.get("char", after)
    sk = state.get("shadow_k", 0.0)
    if sk > 0:  # the second sun behind the Saddle throws every shadow north, toward us
        sh = skia.Path()
        sh.moveTo(LAKE["tree_x"] - 60, LAKE["tree_y"] - 10)
        sh.lineTo(LAKE["tree_x"] + 60, LAKE["tree_y"] - 10)
        sh.lineTo(LAKE["tree_x"] - 340, 1200)
        sh.lineTo(LAKE["tree_x"] - 620, 1200)
        sh.close()
        cv.drawPath(sh, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), 0.45 * sk),
                                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
    Wd.split_tree(cv, LAKE["tree_x"], LAKE["tree_y"], LAKE["tree_h"], (0.45, 0.33, 0.24), t, lk, char=char)
    oh = state.get("oh")
    if oh:
        from creatures import old_horn, wisp
        L = Wd.light_of(lk, 0.15)
        if oh == "mound":
            ash_mound(F, None, 600, 950, 0.19, lk)
        else:
            pose = state.get("oh_pose", {"crouch": 1.0, "breath": t, "head_pitch": 0.12})
            if sk > 0:
                shp = skia.Path()
                shp.addOval(skia.Rect(600 - 130, 950 - 70, 600 + 130, 950))
                from rig import cast_shadow
                cast_shadow(cv, shp, 948, -1.4, 2.4, alpha=0.4 * sk, blur=8)
            a = old_horn(cv, pose, L, state.get("oh_x", 600), 950, 0.19, 1, detail=0.5)
            if state.get("wisp", True):
                nx, ny = a["frill_nest"]
                wisp(cv, state.get("wi_pose", {"t": t, "crouch": 0.9, "curl": 0.8}), L, nx + 3, ny + 13, 0.16, 1,
                     detail=0.3)
    pc = mix(scl(lk["plant"], 0.8), (0.1, 0.1, 0.1), after)
    rng = np.random.default_rng(4)
    for i, (x, y, s) in enumerate([(80, 1010, 190), (250, 1060, 150), (640, 1040, 170), (1000, 1070, 160),
                                   (1380, 1050, 180), (1640, 1020, 210), (1860, 1070, 170)]):
        Wd.fern(cv, x, y, s, pc, t, seed=i, n_fronds=8, burnt=after)
    for i, (x, y, s) in enumerate([(820, 985, 150), (1200, 995, 170), (1760, 960, 180)]):
        Wd.magnolia(cv, x, y, s, mix(scl(lk["plant"], 0.7), (0.1, 0.1, 0.1), after), t, seed=10 + i, burnt=after,
                    flower=mix((1, 0.9, 0.88), lk["key"], 0.15))
    for i in range(9):
        Wd.horsetail(cv, 520 + i * 37 + rng.random() * 20, 1000 + rng.random() * 30, 120 + 80 * rng.random(), pc,
                     t, seed=40 + i, burnt=after)


# --------------------------------------------------------------- POV
def pov_rings(cv, x, y, t, t0, warm=True, a=1.0, n=3, speed=260.0):
    """Sound seen as light: concentric rings expanding from a sound source."""
    col = (1.0, 0.82, 0.55) if warm else (0.02, 0.02, 0.03)
    blend = skia.BlendMode.kPlus if warm else skia.BlendMode.kMultiply
    for k in range(n):
        age = t - t0 - k * 0.18
        if age < 0 or age > 2.2:
            continue
        r = 20 + speed * age
        al = a * (1 - age / 2.2) ** 1.2 * (0.55 if warm else 0.95)
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                       StrokeWidth=(10 + 18 * age) if warm else (26 + 30 * age),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, (8 + 10 * age) if warm else (5 + 6 * age)))
        if warm:
            p.setBlendMode(blend)
            p.setColor4f(c4(col, al))
        else:
            p.setColor4f(c4((0.0, 0.0, 0.0), al))
        cv.drawCircle(x, y, r, p)


# --------------------------------------------------------------- camera
class Cam:
    """2.5D camera: look-at (x, y) in design px and zoom; layers get parallax by depth."""

    def __init__(self, x=W / 2, y=H / 2, z=1.0):
        self.x, self.y, self.z = x, y, z

    def matrix(self, depth=1.0):
        s = 1 + (self.z - 1) * depth
        m = skia.Matrix()
        m.preTranslate(W / 2, H / 2)
        m.preScale(s, s)
        m.preTranslate(-(W / 2 + (self.x - W / 2) * depth), -(H / 2 + (self.y - H / 2) * depth))
        return m

    def apply(self, cv, depth=1.0):
        cv.save()
        cv.concat(self.matrix(depth))

    def to_screen(self, x, y, depth=1.0):
        s = 1 + (self.z - 1) * depth
        return (W / 2 + (x - (W / 2 + (self.x - W / 2) * depth)) * s,
                H / 2 + (y - (H / 2 + (self.y - H / 2) * depth)) * s)


# --------------------------------------------------------------- CAMP (under the Split Tree)
CAMP = dict(oh_x=900, oh_y=1000, oh_s=0.56, tree_x=250, tree_y=1030, tree_h=2500, saddle_x=1560,
            water_y0=660, water_y1=790)
_CRIDGE = None


def camp_bg(F, t, lk, cam, state):
    """Sky, star, ridge with the Saddle, lake glimpse, ground. state: star_k, star_pos, after, flash,
    burn, beads(k), surge."""
    global _CRIDGE
    cv = F.cv
    after = state.get("after", 0.0)
    if _CRIDGE is None:
        _CRIDGE = (Wd.ridge_path(600, 55, seed=21, saddle_x=CAMP["saddle_x"]),
                   Wd.ridge_path(640, 30, seed=22, saddle=False))
    cam.apply(cv, 0.08)
    lk2 = dict(lk)
    if lk2.get("sun") is not None and state.get("sun_pos"):
        lk2["sun"] = state["sun_pos"]
    Wd.sky(cv, lk2, t, horizon=CAMP["water_y0"])
    if state.get("star_k", 0) > 0:
        sx, sy = state.get("star_pos", (CAMP["saddle_x"] + 10, 420))
        Wd.the_star(cv, sx, sy, state["star_k"], t)
    if state.get("flash", 0) > 0:
        fk = state["flash"]
        Wd.glow(cv, CAMP["saddle_x"], 640, 800 * fk, (1.0, 0.92, 0.8), 0.45 * fk)
        Wd.glow(cv, CAMP["saddle_x"], 646, 220 * fk, (1.0, 1.0, 0.95), 1.3 * fk)
    cv.restore()
    if state.get("beads", 0) > 0:
        Wd.bead_shower(cv, t, 199.4, state["beads"], horizon=650)
    cam.apply(cv, 0.15)
    r1, r2 = _CRIDGE
    rc = mix(Wd.fogged(scl(lk["plant"], 0.35), lk, lk["fog_far"]), Wd.fogged((0.2, 0.2, 0.2), lk, 0.6), after)
    Wd.vgrad(cv, r1, 520, 680, rc, Wd.fogged(rc, lk, 0.2))
    if state.get("burn", 0) > 0:
        for i, fx in enumerate(np.linspace(-100, 2000, 16)):
            if (i * 0.37) % 1.0 < state["burn"]:
                Wd.flames(cv, fx, 648 + 6 * math.sin(i), 80, 30 + 12 * (i % 3), t, a=0.9, seed=i)
    hc = mix(Wd.fogged(scl(lk["plant"], 0.45), lk, lk["fog_mid"]), Wd.fogged((0.16, 0.16, 0.16), lk, 0.5), after)
    Wd.vgrad(cv, r2, 610, 670, hc, Wd.fogged(hc, lk, 0.1))
    cv.restore()
    # lake glimpse with reflections
    img = F.snapshot()
    s = F.s
    y0 = cam.to_screen(0, CAMP["water_y0"], 0.2)[1]
    y1 = cam.to_screen(0, CAMP["water_y1"], 0.3)[1]
    surge = state.get("surge", 0.0)
    y0 -= 25 * surge
    if y1 > y0 + 4:
        Wd.reflect(img, int(max(1, y0 * s)), int(min(img.shape[0], y1 * s)), t, strength=0.75, tint=lk["water"],
                   ripple=s, surge=surge)
        F.put(img)
        Wd.water_glints(cv, y0, y1, t, mix(lk["hor"], (1, 1, 1), 0.3), a=0.45 * (1 - 0.8 * after), n=80)
    # ground
    cam.apply(cv, 0.35)
    g = catmull([(-400, 770), (400, 780), (1000, 775), (1600, 785), (2400, 770), (2400, 1600), (-400, 1600)])
    gc = mix(scl(lk["plant"], 0.5), (0.35, 0.35, 0.35), after)
    Wd.vgrad(cv, g, 770, 1080, Wd.fogged(gc, lk, 0.3), scl(gc, 0.55))
    rng = np.random.default_rng(12)
    for i in range(10):
        x = -200 + i * 250 + rng.random() * 90
        Wd.fern(cv, x, 800 + rng.random() * 25, 70 + rng.random() * 40, Wd.fogged(scl(lk["plant"], 0.8), lk, 0.35),
                t, seed=100 + i, n_fronds=6, burnt=after, a=1.0)
    cv.restore()
    Wd.mist(cv, cam.to_screen(0, 740, 0.3)[1], 80, lk["mist_col"], lk["mist"] * 0.6, t)
    # the Split Tree
    cam.apply(cv, 0.9)
    knot = Wd.split_tree(cv, CAMP["tree_x"], CAMP["tree_y"], CAMP["tree_h"], (0.45, 0.33, 0.24), t, lk,
                         char=state.get("char", after), knot=0.29, detail=1.0)
    cv.restore()
    return knot


def camp_fg(F, t, lk, cam, state, blur=5.0):
    after = state.get("after", 0.0)
    pc = mix(scl(lk["plant"], 0.7), (0.12, 0.12, 0.12), after)
    with F.layer(blur=blur) as cv:
        cam.apply(cv, 1.25)
        for i, (x, y, s) in enumerate([(-40, 1120, 330), (1780, 1130, 360), (1450, 1150, 250), (380, 1160, 260)]):
            Wd.fern(cv, x, y, s, pc, t, seed=200 + i, n_fronds=9, burnt=after)
        cv.restore()


def mound(cv, x, y, scale, lk, frill=True):
    """Ash drift shaped unmistakably like a sleeping Triceratops, with a small curve at the frill."""
    body = catmull([(-440, 0), (-330, -120), (-120, -250), (80, -250), (240, -200), (330, -300), (420, -330),
                    (500, -300), (540, -200), (600, -60), (660, 0)], closed=True)
    m = skia.Matrix()
    m.setScaleTranslate(scale, scale, x, y)
    body.transform(m)
    c_top = mix(lk["ambient"], (0.8, 0.8, 0.8), 0.5)
    Wd.vgrad(cv, body, y - 330 * scale, y, scl(c_top, 1.05), scl(c_top, 0.7))
    if frill:  # the small curl of the frill, and a little curled shape within it
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.5, 14 * scale),
                       Color4f=c4(scl(c_top, 0.62), 0.9), StrokeCap=skia.Paint.kRound_Cap)
        arc = skia.Path()
        arc.addArc(skia.Rect(x + 250 * scale, y - 420 * scale, x + 560 * scale, y - 110 * scale), 200, 130)
        cv.drawPath(arc, p)
        small = catmull([(330, -210), (370, -250), (420, -240), (430, -205), (380, -190)], closed=True)
        small.transform(m)
        cv.drawPath(small, skia.Paint(AntiAlias=True, Color4f=c4(scl(c_top, 0.92))))


# --------------------------------------------------------------- SHORE (roots, burrow, shallows)
SHORE = dict(far_y=560, ground=880, near_axis=880, saddle_x=1560, burrow=(236, 896), tree_x=10)
_SGEOM = None


def _shore_geom():
    global _SGEOM
    if _SGEOM is None:
        bank = catmull([(-400, 790), (300, 796), (800, 812), (1080, 846), (1200, 900), (1290, 990), (1360, 1120),
                        (-400, 1120)])
        _SGEOM = dict(bank=bank, ridge=Wd.ridge_path(505, 50, seed=31, saddle_x=SHORE["saddle_x"]),
                      hill=Wd.ridge_path(545, 24, seed=32, saddle=False))
    return _SGEOM


def _mask_from_path(path, w, h, s):
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    c.scale(s, s)
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))
    return surf.makeImageSnapshot().toarray()[..., 0].astype(np.float32) / 255.0


def shore(F, t, lk, cam, state, draw_chars=None, draw_front=None):
    """Lake shore with Split Tree roots and the burrow. Characters (draw_chars(cv)) get
    real reflections in the water. state: after, star_k, star_pos, surge, beads, burn."""
    import cv2
    g = _shore_geom()
    cv = F.cv
    after = state.get("after", 0.0)
    cam.apply(cv, 0.1)
    Wd.sky(cv, lk, t, horizon=SHORE["far_y"])
    if state.get("star_k", 0) > 0:
        sx, sy = state.get("star_pos", (SHORE["saddle_x"] + 10, 360))
        Wd.the_star(cv, sx, sy, state["star_k"], t)
    rc = mix(Wd.fogged(scl(lk["plant"], 0.35), lk, lk["fog_far"]), Wd.fogged((0.2, 0.2, 0.2), lk, 0.6), after)
    Wd.vgrad(cv, g["ridge"], 440, 580, rc, Wd.fogged(rc, lk, 0.2))
    hc = mix(Wd.fogged(scl(lk["plant"], 0.45), lk, lk["fog_mid"]), Wd.fogged((0.16, 0.16, 0.16), lk, 0.5), after)
    Wd.vgrad(cv, g["hill"], 520, 575, hc, hc)
    cv.restore()
    cam.apply(cv, 0.25)
    treeline_band = skia.Path()
    treeline_band.addRect(skia.Rect(-400, 552, W + 400, 566))
    Wd.fill(cv, treeline_band, Wd.fogged(scl(lk["plant"], 0.5), lk, lk["fog_mid"] + 0.1))
    rng = np.random.default_rng(41)
    x = -300.0
    while x < W + 300:
        Wd.conifer(cv, x, 562, 30 + 50 * rng.random(), Wd.fogged(scl(lk["plant"], 0.55), lk, lk["fog_mid"] + 0.1), t,
                   seed=int(x) + 3000, bare=after)
        x += 22 + 40 * rng.random()
    cv.restore()
    # bank (near ground) + roots + burrow
    cam.apply(cv, 1.0)
    bc = mix(scl(lk["plant"], 0.42), (0.14, 0.14, 0.14), after)
    Wd.vgrad(cv, g["bank"], 790, 1080, Wd.fogged(bc, lk, 0.1), scl(bc, 0.55))
    edge = skia.Path()
    edge.moveTo(700, 808)
    edge.cubicTo(1000, 830, 1180, 880, 1250, 950)
    edge.cubicTo(1300, 1010, 1330, 1060, 1350, 1110)
    mp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                    Color4f=c4(mix(scl(lk["ambient"], 0.22), (0.1, 0.1, 0.1), after), 0.85),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
    cv.drawPath(edge, mp)
    rng2 = np.random.default_rng(77)
    for i in range(26):  # pebbles along the wet edge
        u_ = rng2.random()
        px_ = 760 + 560 * u_
        py_ = 812 + 300 * u_ ** 2.2 + rng2.normal() * 6
        cv.drawOval(skia.Rect(px_ - 5, py_ - 3, px_ + 5, py_ + 3),
                    skia.Paint(AntiAlias=True, Color4f=c4(scl(lk["ambient"], 0.3 + 0.3 * rng2.random()))))
    split = Wd.split_tree(cv, SHORE["tree_x"], 900, 2600, (0.45, 0.33, 0.24), t, lk, char=state.get("char", after),
                          knot=0.2)
    root_col = mix((0.30, 0.22, 0.16), (0.03, 0.03, 0.03), state.get("char", after))
    L = Wd.light_of(lk)
    from rig import draw_form
    for i, (x0, x1, y1, w) in enumerate([(120, 330, 912, 34), (140, 470, 880, 26), (90, 250, 950, 40), (150, 560, 860, 18)]):
        root = tube([(x0, 880), ((x0 + x1) / 2, y1 - 30), (x1, y1)], [w, w * 0.6, w * 0.2], n=16)
        draw_form(cv, [(root, root_col, 1.0)], L, texture=0.3, tex_scale=0.04, size=w * 1.5, ao=True)
    bx, by = SHORE["burrow"]
    cv.drawOval(skia.Rect(bx - 26, by - 16, bx + 26, by + 12), skia.Paint(AntiAlias=True, Color4f=c4((0.02, 0.015, 0.01))))
    cv.drawOval(skia.Rect(bx - 30, by + 4, bx + 30, by + 16), skia.Paint(AntiAlias=True, Color4f=c4(scl(bc, 0.7))))
    cv.restore()
    # characters into their own layer so the water can reflect them
    s = F.s
    img = F.snapshot()
    hh, ww = img.shape[:2]
    chars = None
    if draw_chars is not None:
        surf = F._new()
        c2 = surf.getCanvas()
        c2.clear(skia.ColorTRANSPARENT)
        c2.scale(s, s)
        cam.apply(c2, 1.0)
        draw_chars(c2)
        c2.restore()
        chars = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_F16_ColorType).astype(np.float32)
        a = chars[..., 3:4]
        comb = img * (1 - a) + chars[..., :3]
    else:
        comb = img
    # water mask = below the far shore, outside the bank (in screen space)
    bank_s = skia.Path(g["bank"])
    bank_s.transform(cam.matrix(1.0))
    far_y = cam.to_screen(0, SHORE["far_y"], 0.25)[1]
    wm = np.zeros((hh, ww), np.float32)
    wm[int(far_y * s):] = 1.0
    wm *= 1.0 - _mask_from_path(bank_s, ww, hh, s)
    ax_near = cam.to_screen(0, SHORE["near_axis"], 1.0)[1] * s
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    rip = (np.sin(xx * 0.05 / s + t * 1.6 + yy * 0.3 / s) * (1.5 + (yy - far_y * s) * 0.02)) * s
    axis = np.where(yy < ax_near, far_y * s, ax_near)
    my = np.clip(2 * axis - yy + rip * 0.6, 0, hh - 1).astype(np.float32)
    mx = np.clip(xx + rip, 0, ww - 1).astype(np.float32)
    refl = cv2.remap(comb, mx, my, cv2.INTER_LINEAR)
    tint = np.array(lk["water"], np.float32)
    depth = np.clip((yy - far_y * s) / (300 * s), 0, 1)[..., None]
    refl = refl * (0.78 - 0.25 * depth) + tint * (0.22 + 0.25 * depth)
    wm3 = wm[..., None]
    out = comb * (1 - wm3) + refl * wm3
    if chars is not None:
        out = out * (1 - chars[..., 3:4]) + chars[..., :3]
    F.put(out)
    Wd.water_glints(cv, cam.to_screen(0, 600, 0.3)[1], H, t, mix(lk["hor"], (1, 1, 1), 0.3), a=0.4 * (1 - 0.8 * after),
                    n=90, x0=1100, x1=W)
    Wd.mist(cv, cam.to_screen(0, 600, 0.3)[1], 70, lk["mist_col"], lk["mist"] * 0.5, t)
    if draw_front is not None:
        cam.apply(cv, 1.0)
        draw_front(cv)
        cv.restore()
    # foreground plants
    pc = mix(scl(lk["plant"], 0.7), (0.12, 0.12, 0.12), after)
    with F.layer(blur=6) as c3:
        cam.apply(c3, 1.3)
        for i, (x, y, sz) in enumerate([(-60, 1110, 300), (620, 1140, 240), (980, 1150, 200)]):
            Wd.fern(c3, x, y, sz, pc, t, seed=300 + i, n_fronds=9, burnt=after)
        c3.restore()
    return split


# --------------------------------------------------------------- FERN FOREST
FOREST = dict(ground=900)


def forest_bg(F, t, lk, cam, state):
    """Green-black fern forest: distant trunks, light shafts, big ferns and horsetails.
    state: shafts (0..1), silence (0..1 -> insects/fireflies stop), gust."""
    cv = F.cv
    cam.apply(cv, 0.05)
    Wd.sky(cv, lk, t, horizon=1200)
    cv.restore()
    rng = np.random.default_rng(61)
    for layer, (depth, n, col_k, fog_k, hmin) in enumerate(((0.2, 16, 0.25, 0.75, 900), (0.45, 11, 0.35, 0.45, 1100))):
        cam.apply(cv, depth)
        for i in range(n):
            x = -600 + i * (3200 / n) + rng.random() * 120
            w = 30 + 40 * rng.random() * (1 + layer)
            col = Wd.fogged(scl((0.16, 0.12, 0.08), 1.0 + col_k), lk, fog_k)
            trunk = skia.Path()
            trunk.addRect(skia.Rect(x - w / 2, -200, x + w / 2, FOREST["ground"] + 20))
            Wd.fill(cv, trunk, col)
            for k in range(3):
                Wd.foliage(cv, x + (rng.random() - 0.5) * 300, 80 + rng.random() * 260, 420, 150,
                           Wd.fogged(scl(lk["plant"], 0.8), lk, fog_k), t, seed=int(i * 10 + k + layer * 100), n=8)
        cv.restore()
    # god-ray shafts through the canopy
    sh = state.get("shafts", 0.8)
    if sh > 0:
        for i, (x, w_) in enumerate([(420, 90), (820, 50), (1240, 120), (1600, 70)]):
            beam = skia.Path()
            dx = 260
            beam.moveTo(x - w_ / 2, -50)
            beam.lineTo(x + w_ / 2, -50)
            beam.lineTo(x + w_ * 1.6 + dx, FOREST["ground"] + 40)
            beam.lineTo(x - w_ * 0.6 + dx, FOREST["ground"] + 40)
            beam.close()
            k = sh * (0.10 + 0.05 * math.sin(t * 0.7 + i * 2))
            cv.drawPath(beam, skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Color4f=c4(lk["key"], k),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
    cam.apply(cv, 0.7)
    g = catmull([(-600, FOREST["ground"] - 10), (900, FOREST["ground"]), (2600, FOREST["ground"] - 10), (2600, 1600),
                 (-600, 1600)])
    Wd.vgrad(cv, g, FOREST["ground"] - 10, 1080, Wd.fogged(scl(lk["plant"], 0.55), lk, 0.3), scl(lk["plant"], 0.25))
    for i in range(14):
        Wd.fern(cv, -500 + i * 220 + rng.random() * 80, FOREST["ground"] + 10, 260 + rng.random() * 160,
                Wd.fogged(scl(lk["plant"], 0.9), lk, 0.3), t, seed=600 + i, n_fronds=9, gust=state.get("gust", 1.0))
    for i in range(10):
        Wd.horsetail(cv, -400 + i * 300 + rng.random() * 100, FOREST["ground"] + 14, 260 + rng.random() * 120,
                     Wd.fogged(scl(lk["plant"], 1.1), lk, 0.25), t, seed=700 + i)
    cv.restore()


def forest_fg(F, t, lk, cam, state, blur=8.0, part=None):
    with F.layer(blur=blur) as cv:
        cam.apply(cv, 1.3)
        rng = np.random.default_rng(66)
        for i, bx in enumerate((-260, 2180, -60, 1980)):
            x = bx + rng.random() * 60
            if part is not None:
                x += part(i)
            Wd.fern(cv, x, 1200, 300 + rng.random() * 100, scl(lk["plant"], 0.6), t, seed=800 + i, n_fronds=10,
                    gust=state.get("gust", 1.0))
        cv.restore()


def footprint(cv, x, y, t, lk, tremble=0.0, t0=0.0):
    """A huge three-toed print, filled with water that trembles in rings."""
    p = skia.Path()
    for ang, ln in ((-0.5, 150), (0.0, 175), (0.5, 150)):
        toe = Wd.ellipse_path(x + math.sin(ang) * ln * 0.6, y - math.cos(ang) * ln * 0.18, 34, 18, ang * 0.6)
        p = skia.Op(p, toe, skia.PathOp.kUnion_PathOp) or p
    heel = Wd.ellipse_path(x, y + 22, 70, 30)
    p = skia.Op(p, heel, skia.PathOp.kUnion_PathOp) or p
    cv.drawPath(p, skia.Paint(AntiAlias=True, Color4f=c4(scl(lk["plant"], 0.18))))
    cv.save()
    cv.clipPath(p, doAntiAlias=True)
    cv.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x, y - 60), (x, y + 50)], [c4(mix(lk["hor"], (1, 1, 1), 0.2), 0.8), c4(scl(lk["water"], 0.6), 0.9)], [0, 1])))
    if tremble > 0:
        rp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0)
        for k in range(6):
            age = ((t - t0) * 1.4 + k / 6) % 1.0
            rp.setColor4f(c4((1, 1, 1), tremble * 0.5 * (1 - age)))
            cv.save()
            cv.translate(x, y + 5)
            cv.scale(1.0, 0.35)
            cv.drawCircle(0, 0, 10 + 140 * age, rp)
            cv.restore()
    cv.restore()


def ash_mound(F, cam, x, y, scale, lk, depth=1.0):
    """Her lying silhouette (and his small curl at the frill), buried under grey ash."""
    from creatures import old_horn, wisp
    from rig import Light
    lum = [0.30, 0.59, 0.11]
    k, off = 0.30, 0.34
    row = [lum[0] * k, lum[1] * k, lum[2] * k, 0, off]
    cf = skia.ColorFilters.Matrix(row + row + row + [0, 0, 0, 1, 0])
    L = Light(ambient=(1, 1, 1), key=(1, 1, 1), key_dir=-1.6, rim=(1, 1, 1), rim_k=0.5, shade=0.35)
    with F.layer(blur=2.0 * scale / 0.19 * 0.6, color_filter=cf) as c:
        if cam is not None:
            cam.apply(c, depth)
        a = old_horn(c, {"crouch": 1.0, "breath": 0.0, "head_pitch": 0.22, "blink": 1.0}, L, x, y, scale, 1, detail=0.0)
        nx, ny = a["frill_nest"]
        wisp(c, {"t": 0.0, "curl": 1.0, "crouch": 1.0, "blink": 1.0}, L, nx + 4 * scale / 0.56, ny + 40 * scale / 0.56,
             0.4 * scale / 0.56, 1, detail=0.0)
        # drifts of ash heaped against her flank
        c.drawOval(skia.Rect(x - 560 * scale, y - 50 * scale, x + 600 * scale, y + 26 * scale),
                   skia.Paint(AntiAlias=True, Color4f=c4((0.55, 0.55, 0.55)),
                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30 * scale)))
        if cam is not None:
            c.restore()


def mound(cv, *a, **k):   # legacy name kept for callers that only have a canvas
    return None
