"""ACT I — THE LAST MORNING (S3–S8)."""
import math

import numpy as np
import skia

import timeline as TL
import world as Wd
from creatures import burrower, edmonto, old_horn, pebble, wisp
from foxfolly.anim import Track, clamp, ease_in_out_sine, ease_out_cubic, smoothstep, window
from rig import c4, catmull, contact_shadow, mix, scl
from shotkit import CAMP, SHORE, Cam, camp_bg, camp_fg, lake, lake_foreground, pov_rings, shore
from world import LOOKS, W, H, blend_look, light_of

EV = TL.EV


def pulses(t, times, dur=0.28):
    v = 0.0
    for t0 in times:
        v = max(v, math.sin(math.pi * clamp((t - t0) / dur)))
    return v


def blinks(t, period=4.7, off=0.0, dur=0.2):
    ph = (t + off) % period
    return math.sin(math.pi * clamp(ph / dur)) if ph < dur else 0.0


def spring(t, t0, amp=1.0, freq=7.0, damp=4.0):
    """Overshooting settle for follow-through (0 before t0, -> 1)."""
    if t < t0:
        return 0.0
    x = t - t0
    return 1 - math.exp(-damp * x) * math.cos(freq * x) * amp


def star_k(t):
    return Track(TL.STAR_KEYS)(t)


# ======================================================================
def S03(F, u, dur, t):
    """THE LAKE — dawn. Overwhelmingly, abundantly alive."""
    crest = EV["sun_crest"]
    k = smoothstep(17.0, crest + 3, t)
    lk = dict(LOOKS["dawn"])
    sy = 610 - 110 * ease_in_out_sine(clamp((t - 18.5) / 9.0))
    lk["sun"] = (230, sy)
    lk["sun_k"] = 0.35 + 0.65 * smoothstep(crest - 1.0, crest + 1.5, t)
    lk["glow_k"] = 0.6 + 0.6 * k
    st = {"herd": "drink", "azhd": clamp((u - 1.0) / 9.5), "dflies": True, "oh": "lying",
          "oh_pose": {"crouch": 1.0, "breath": t, "head_pitch": 0.12}, "wi_pose": {"t": t, "curl": 1.0, "crouch": 1.0}}
    lake(F, t, lk, st)
    lake_foreground(F, t, lk, st)
    rays = 0.75 * smoothstep(crest - 0.6, crest + 2.0, t)
    F.post = {"grade": "act1", "bloom": (0.6, 0.55), "rays": (230, sy, rays), "ray_thr": 0.6,
              "black": 1 - smoothstep(17.0, 18.2, t)}


# ======================================================================
def S04(F, u, dur, t):
    """Wisp wakes in the curve of the frill; pull back to reveal Old Horn's clouded eyes."""
    lk = blend_look(LOOKS["dawn"], LOOKS["morning"], 0.35)
    lk = dict(lk, sun=None)
    pull = ease_in_out_sine(clamp((u - 5.6) / 3.4))
    cam = Cam(1080 - 30 * pull, 905 - 55 * pull, 4.2 - 2.45 * pull)
    camp_bg(F, t, lk, cam, {})
    wake = spring(t, EV["wisp_wake_tuft"], amp=1.0, freq=12, damp=5)
    curl = 1 - 0.45 * smoothstep(EV["wisp_wake_tuft"] + 0.2, EV["wisp_yawn"], t)
    yawn = window(t, EV["wisp_yawn"], EV["wisp_yawn"] + 0.9, 0.3, 0.35)
    shake = window(t, 33.2, 34.1, 0.1, 0.2)
    wi = {"t": t, "curl": curl, "crouch": 1.0, "tuft": 0.15 + 0.85 * wake, "yawn": yawn, "shake": shake,
          "blink": 1.0 if t < EV["wisp_wake_tuft"] - 0.1 else blinks(t, 3.1, 0.7),
          "head_pitch": 0.35 * (1 - smoothstep(31.0, 32.0, t)) - 0.1 * yawn}
    oh = {"crouch": 1.0, "breath": t, "head_pitch": 0.12, "blink": blinks(t, 5.3, 1.2), "listen": 0.08 * math.sin(t * 0.4)}
    L = light_of(lk)
    cv = F.cv
    cam.apply(cv, 1.0)
    a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    nx, ny = a["frill_nest"]
    w = wisp(cv, wi, L, nx + 4, ny + 40, 0.42, 1)
    cv.restore()
    # the first sunlight touches his face
    sun = smoothstep(29.6, 31.0, t)
    ex, ey = cam.to_screen(*w["eye"])
    Wd.glow(cv, ex - 30, ey, 380 * (0.5 + 0.5 * sun), (1.0, 0.8, 0.5), 0.35 * sun)
    camp_fg(F, t, lk, cam, {}, blur=10)
    F.post = {"grade": "act1", "bloom": (0.6, 0.5), "rays": (-200, 300, 0.4 * sun), "ray_thr": 0.6}


# ======================================================================
OH_RISE = Track([(38.6, 1.0), (39.4, 0.92), (40.2, 0.55), (41.0, 0.08), (41.4, 0.0)], mode="ease")


def S05(F, u, dur, t):
    lk = LOOKS["morning"]
    L = light_of(lk)
    if t < 41.2:                                               # a) Wisp hops down; she rises
        cam = Cam(1060, 820, 1.35)
        camp_bg(F, t, lk, cam, {})
        cr = OH_RISE(t)
        shud = window(t, 39.4, 40.6, 0.3, 0.3)
        listen = 0.28 * smoothstep(38.4, 39.2, t)
        oh = {"crouch": cr, "breath": t, "head_pitch": 0.12 * cr - 0.05 * (1 - cr), "listen": listen,
              "shudder": shud, "blink": blinks(t, 5.1, 0.3), "s": 0.0}
        cv = F.cv
        cam.apply(cv, 1.0)
        a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
        nx, ny = a["frill_nest"]
        hop = clamp((t - 37.15) / 0.85)
        # he hops from the frill to the ground in front of her face
        x0, y0, x1, y1 = nx + 4, ny + 40, 1330, CAMP["oh_y"] - 2
        e = ease_in_out_sine(hop)
        wx, wy = x0 + (x1 - x0) * e, y0 + (y1 - y0) * e - 90 * math.sin(math.pi * hop)
        chirp = pulses(t, [EV["chirp_s5"][0]], 0.35)
        turn = -1 if t > 38.6 else 1
        wi = {"t": t, "crouch": 0.35 * (1 - math.sin(math.pi * hop)) if hop < 1 else 0.0,
              "tuft": 0.6 + 0.4 * chirp, "beak_open": chirp, "head_turn": turn,
              "head_pitch": -0.15 * chirp, "blink": blinks(t, 2.9, 0.5)}
        if hop >= 1:
            contact_shadow(cv, wx, wy + 2, 34, 6, 0.35)
        wisp(cv, wi, L, wx, wy, 0.42, 1 if t < 38.4 else -1)
        cv.restore()
        camp_fg(F, t, lk, cam, {})
        F.post = {"grade": "act1", "bloom": (0.62, 0.45)}
        return
    if t < 44.2:                                               # b) her POV: warm blur; his chirp is light
        cam = Cam(1150, 760, 1.2)
        camp_bg(F, t, lk, cam, {})
        cv = F.cv
        cam.apply(cv, 1.0)
        hop = ((t - 41.2) / 0.8) % 1.0
        wisp(cv, {"t": t, "hop": hop, "hop_len": 0, "hop_h": 30, "tuft": 0.8}, L, 1180 + 40 * math.sin(t), 1000, 0.9, -1)
        cv.restore()
        F.defocus(26)
        wx, wy = cam.to_screen(1180 + 40 * math.sin(t), 960)
        Wd.glow(cv, wx, wy, 150, (1.0, 0.75, 0.45), 0.7)
        Wd.glow(cv, 1420, 560, 700, (1.0, 0.92, 0.75), 0.25)
        pov_rings(cv, wx, wy, t, EV["chirp_s5"][1], warm=True, a=1.0, n=4)
        pov_rings(cv, wx, wy, t, EV["chirp_s5"][1] + 1.3, warm=True, a=0.7, n=3)
        F.post = {"grade": "act1", "pov": 0.4, "bloom": (0.45, 0.9), "vignette": 0.65}
        return
    # c) the water: she drinks; he copies her                  (44.2 – 49)
    cam = Cam(960, 760, 1.45)
    walk = ease_in_out_sine(clamp((t - 44.2) / 2.6))
    from creatures import OH_GAIT
    s_end = OH_GAIT.settle(0.0)
    s = -330 * (1 - walk) + s_end * walk
    drink = ease_in_out_sine(clamp((t - 46.9) / 1.3))
    wdrink = ease_in_out_sine(clamp((t - 47.6) / 0.9))
    chirp = pulses(t, [EV["chirp_s5"][2]], 0.35)

    def chars(cv):
        oh = {"s": s, "crouch": 0.12 * drink, "breath": t, "head_pitch": -0.05 + 0.95 * drink,
              "listen": 0.22 * (1 - drink), "blink": blinks(t, 4.4, 2.0)}
        old_horn(cv, oh, L, 820, SHORE["ground"], 0.46, 1)
        hop = (t - 44.2) / 0.9
        if hop < 3:
            k = int(hop)
            ph = hop - k
            wx = 880 + 110 * k + 110 * ease_in_out_sine(ph)
            wi = {"t": t, "hop": ph, "hop_len": 0, "hop_h": 36, "tuft": 0.6 + 0.4 * chirp, "beak_open": chirp}
        else:
            wx = 1210
            wi = {"t": t, "head_pitch": 0.9 * wdrink, "crouch": 0.25 * wdrink, "tuft": 0.5, "blink": blinks(t, 3.3)}
        contact_shadow(cv, wx, SHORE["ground"] + 2, 30, 5, 0.3)
        wisp(cv, wi, L, wx, SHORE["ground"], 0.38, 1)

    shore(F, t, lk, cam, {}, draw_chars=chars)
    F.post = {"grade": "act1", "bloom": (0.62, 0.45)}


# ======================================================================
def S06(F, u, dur, t):
    """The Burrower — a comic beat that plants the burrow under the Split Tree roots."""
    lk = LOOKS["morning"]
    L = light_of(lk)
    cam = Cam(470, 850, 2.1 - 0.1 * ease_in_out_sine(clamp(u / 10)))
    bx, by = SHORE["burrow"]
    # burrower path: dart in from the right, pause, dodge the pounce, dash into the burrow
    bu_x = Track([(49.2, 900), (50.9, 560), (51.5, 540), (51.8, 470), (53.3, 330), (54.4, bx + 8)], mode="pchip")(t)
    wi_x = Track([(49.0, 760), (51.2, 740), (51.6, 700), (52.2, 545), (54.4, 360), (55.0, 336)], mode="pchip")(t)
    pounce = clamp((t - 51.55) / 0.65)
    ind = pulses(t, EV["indignant"], 0.3)

    def chars(cv):
        if t < EV["burrow_dive"] + 0.15:
            k = clamp((t - (EV["burrow_dive"] - 0.2)) / 0.35)
            burrower(cv, {"t": t, "run": 0.0 if 50.9 < t < 51.5 else 1.0, "sniff": 1.0 if 50.9 < t < 51.5 else 0.2},
                     L, bu_x, by + 4 + 10 * k, 1.0 - 0.3 * k, -1)
        if 0 < pounce < 1:
            wi = {"t": t, "hop": pounce, "hop_len": 0, "hop_h": 70, "tuft": 1.0}
        elif t < 54.6:
            wi = {"t": t, "gait": "run", "s": (760 - wi_x) * 2.2, "tuft": 0.9}
        else:
            wi = {"t": t, "tuft": 0.7 + 0.3 * ind, "beak_open": ind, "head_pitch": 0.25 - 0.3 * ind,
                  "crouch": 0.25, "blink": blinks(t, 2.7, 1.1)}
        s_off = wi.get("s", 0.0) * 0.44     # body travels by s in local units; keep it at wi_x
        contact_shadow(cv, wi_x, by + 6, 32, 6, 0.3)
        wisp(cv, wi, L, wi_x + s_off, by + 4, 0.44, -1)

    def front(cv):
        # the lip of the burrow in front of him, and the peeking Burrower
        if t >= EV["burrow_dive"] + 0.8:
            peek = smoothstep(55.0, 55.6, t)
            cv.save()
            cv.clipRect(skia.Rect(bx - 60, by - 60, bx + 60, by + 4))
            burrower(cv, {"t": t, "sniff": 1.0, "run": 0.0}, L, bx + 18, by + 18 - 16 * peek, 1.0, -1)
            cv.restore()
        cv.drawOval(skia.Rect(bx - 30, by + 2, bx + 30, by + 14),
                    skia.Paint(AntiAlias=True, Color4f=c4(scl(lk["plant"], 0.3))))

    shore(F, t, lk, cam, {}, draw_chars=chars, draw_front=front)
    F.post = {"grade": "act1", "bloom": (0.62, 0.45)}


# ======================================================================
TREASURES = [("beetle", (-0.35, 0.25)), ("feather", (0.05, 0.1)), ("seed", (0.4, 0.3))]


def knot_hole(cv, kx, ky, r, lk, t, with_pebble, glint=0.0):
    """Inside of the knot-hole: his treasures (and the bough stub he perches on)."""
    L = light_of(lk)
    from rig import draw_form, tube as _tube
    stub = _tube([(kx - r * 0.2, ky + r * 1.55), (kx + r * 1.6, ky + r * 1.50), (kx + r * 3.1, ky + r * 1.62)],
                 [r * 0.34, r * 0.24, r * 0.14], n=16)
    draw_form(cv, [(stub, (0.34, 0.25, 0.18), 1.0)], L, texture=0.3, tex_scale=0.06, size=r * 1.2, ao=True)
    cv.save()
    cv.clipPath(Wd.ellipse_path(kx, ky, r, r * 1.38))
    cv.drawRect(skia.Rect(kx - r, ky - r * 1.4, kx + r, ky + r * 1.4), skia.Paint(Color4f=c4((0.05, 0.03, 0.02))))
    Wd.glow(cv, kx, ky + r * 0.5, r * 1.2, (1.0, 0.8, 0.5), 0.15)
    # beetle shell (iridescent green), a banded feather, a seed
    bxx, byy = kx - r * 0.45, ky + r * 0.55
    cv.drawOval(skia.Rect(bxx - r * 0.2, byy - r * 0.14, bxx + r * 0.2, byy + r * 0.14),
                skia.Paint(AntiAlias=True, Color4f=c4(L.base((0.1, 0.55, 0.35)))))
    Wd.glow(cv, bxx - r * 0.05, byy - r * 0.05, r * 0.2, (0.4, 1.0, 0.7), 0.3)
    fp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=r * 0.06,
                    Color4f=c4(L.base((0.85, 0.8, 0.7))))
    cv.drawLine(kx - r * 0.1, ky + r * 0.75, kx + r * 0.25, ky + r * 0.05, fp)
    cv.drawOval(skia.Rect(kx + r * 0.3, ky + r * 0.55, kx + r * 0.55, ky + r * 0.75),
                skia.Paint(AntiAlias=True, Color4f=c4(L.base((0.55, 0.36, 0.18)))))
    if with_pebble:
        pebble(cv, kx + r * 0.05, ky + r * 0.52, r * 0.24, L, rot=0.4, glint=glint)
    cv.restore()


def S07(F, u, dur, t):
    lk = LOOKS["morning"]
    L = light_of(lk)
    if t < 67.4:
        cam = Cam(1040, 800, 1.55)
        glint = window(t, EV["pebble_glint"] - 0.2, EV["pebble_glint"] + 1.2, 0.2, 0.8)
        pick = 61.8
        drop = EV["pebble_drop"]
        from creatures import OH_GAIT
        oh_s = OH_GAIT.settle(0.0)
        # Old Horn standing at the edge; she lowers her head to meet him
        lower = ease_in_out_sine(clamp((t - 63.2) / 1.2)) * (1 - 0.3 * ease_in_out_sine(clamp((t - 67.0) / 0.4)))
        sniff = window(t, 65.0, 66.3, 0.3, 0.3)
        nudge = window(t, EV["pebble_nudge"] - 0.3, EV["pebble_nudge"] + 0.35, 0.25, 0.3)
        wi_x = Track([(59.0, 1175), (61.4, 1180), (62.2, 1170), (64.2, 1082), (64.8, 1080), (67.0, 1060)])(t)
        peb_x = Track([(drop, 1063), (EV["pebble_nudge"] - 0.1, 1063), (EV["pebble_nudge"] + 0.4, 1046)])(t)
        carry = pick <= t < drop
        wonder = smoothstep(60.8, 61.1, t) * (1 - smoothstep(61.3, 61.6, t))
        delight = window(t, 66.9, 67.4, 0.1, 0.2)

        def chars(cv):
            oh = {"s": oh_s, "breath": t, "head_pitch": -0.02 + 0.62 * lower + 0.05 * sniff - 0.04 * nudge,
                  "listen": 0.2 * (1 - lower), "blink": blinks(t, 4.1, 1.0), "crouch": 0.05 * lower}
            a = old_horn(cv, oh, L, 820 - 60 * nudge * 0, SHORE["ground"], 0.46, 1)
            # the pebble: in the shallows, in his beak, then at her beak
            if t < pick:
                pebble(cv, 1214, SHORE["ground"] + 18, 7, L, glint=glint)
            elif t >= drop:
                pebble(cv, peb_x, SHORE["ground"] - 4, 7, L, glint=0.3 * nudge)
            peck = window(t, 61.3, 61.9, 0.15, 0.25)
            hopping = 62.2 <= t < 64.2
            if hopping:
                ph = ((t - 62.2) / 0.66) % 1.0
                wi = {"t": t, "hop": ph, "hop_len": 0, "hop_h": 26, "carry": True, "tuft": 0.8}
                fc = -1
            else:
                fc = 1 if t < 62.2 else -1 if t < 64.8 else 1
                wi = {"t": t, "head_pitch": 0.8 * peck + 0.5 * window(t, 64.3, 64.9, 0.15, 0.2),
                      "crouch": 0.3 * peck, "carry": carry, "tuft": 0.4 + 0.6 * max(wonder, delight, glint * 0.5),
                      "beak_open": 0.6 * window(t, 64.45, 64.75, 0.05, 0.1), "blink": blinks(t, 3.0, 0.2)}
                if t >= 64.8:
                    fc = -1
                    wi["head_pitch"] = 0.2
                if t > 66.9:
                    wi["hop"] = clamp((t - 66.9) / 0.5)
                    wi["hop_h"] = 30
                    wi["hop_len"] = 0
            contact_shadow(cv, wi_x, SHORE["ground"] + 2, 30, 5, 0.3)
            wisp(cv, wi, L, wi_x, SHORE["ground"], 0.38, fc)

        shore(F, t, lk, cam, {}, draw_chars=chars)
        F.post = {"grade": "act1", "bloom": (0.62, 0.5)}
        return
    # knot-hole close-up: he stores his best treasure
    kx, ky, kr = CAMP["tree_x"] + 0.15 * CAMP["tree_h"] * 0.11, CAMP["tree_y"] - 0.29 * CAMP["tree_h"], 0.16 * CAMP["tree_h"] * 0.11
    cam = Cam(kx + 40, ky + 30, 3.4 + 0.15 * ease_in_out_sine(clamp((t - 67.4) / 4.6)))
    camp_bg(F, t, lk, cam, {})
    cv = F.cv
    cam.apply(cv, 0.9)
    stored = t >= EV["knot_store"]
    knot_hole(cv, kx, ky, kr, lk, t, stored, glint=window(t, 70.3, 71.8, 0.4, 0.8))
    cv.restore()
    cam.apply(cv, 0.9)
    # he lands on the lip of the hole, leans in, places it, then admires it
    land = clamp((t - 67.5) / 0.8)
    lx = kx + kr * 1.6
    ly = ky + kr * 1.3 + kr * 0.05
    x = lx + 60 * (1 - ease_out_cubic(land))
    y = ly + 120 * (1 - land) - 60 * math.sin(math.pi * land)
    lean = window(t, 69.2, 70.4, 0.4, 0.4)
    wi = {"t": t, "head_pitch": 0.55 * lean, "crouch": 0.3 * lean + 0.3 * (1 - land), "carry": t < EV["knot_store"],
          "tuft": 0.5 + 0.5 * smoothstep(70.3, 70.6, t), "blink": blinks(t, 3.5, 1.4), "eye_dir": 3.0}
    wisp(cv, wi, L, x, y, 0.36, -1)
    cv.restore()
    F.post = {"grade": "act1", "bloom": (0.6, 0.55)}


# ======================================================================
def nest_scene(F, t, lk, cam):
    cv = F.cv
    L = light_of(lk)
    cam.apply(cv, 0.1)
    Wd.sky(cv, lk, t, horizon=600)
    Wd.the_star(cv, 1500, 150, 0.06, t)   # the faint daytime dot (sharp-eyed viewers only)
    cv.restore()
    cam.apply(cv, 0.3)
    r = Wd.ridge_path(560, 40, seed=51, saddle_x=1700)
    rc = Wd.fogged(scl(lk["plant"], 0.35), lk, lk["fog_far"])
    Wd.vgrad(cv, r, 500, 640, rc, rc)
    band = skia.Path()
    band.addRect(skia.Rect(-400, 600, W + 400, 700))
    Wd.fill(cv, band, Wd.fogged(scl(lk["water"], 0.9), lk, 0.3))
    cv.restore()
    cam.apply(cv, 0.7)
    g = catmull([(-400, 700), (800, 712), (2400, 700), (2400, 1400), (-400, 1400)])
    Wd.vgrad(cv, g, 700, 1080, Wd.fogged(scl(lk["plant"], 0.5), lk, 0.2), scl(lk["plant"], 0.3))
    for i in range(22):
        Wd.horsetail(cv, -200 + i * 110, 760 + (i % 3) * 8, 170 + 40 * (i % 4), Wd.fogged(scl(lk["plant"], 0.8), lk, 0.3),
                     t, seed=500 + i)
    cv.restore()
    cam.apply(cv, 1.0)
    # the mound nest
    mound = catmull([(760, 900), (840, 840), (980, 826), (1100, 846), (1170, 900)], closed=True)
    Wd.vgrad(cv, mound, 826, 900, (0.40, 0.30, 0.20), (0.24, 0.18, 0.12))
    for i in range(10):
        a = math.pi + i * math.pi / 9
        cv.drawOval(skia.Rect(960 + 140 * math.cos(a) - 18, 870 + 40 * math.sin(a) - 6, 960 + 140 * math.cos(a) + 18,
                              870 + 40 * math.sin(a) + 6), skia.Paint(AntiAlias=True, Color4f=c4((0.36, 0.30, 0.18))))
    # mother nuzzling: head lowered to the nest
    edmonto(cv, {"t": t, "head": 0.85 + 0.1 * math.sin(t * 1.8), "s": 0}, L, 520, 905, 0.55, 1)
    # hatchlings clambering out and over the rim
    for i, (x0, ph, sc) in enumerate([(930, 0.0, 0.085), (1000, 1.3, 0.075), (880, 2.4, 0.08)]):
        k = clamp((t - 72.4 - ph * 0.9) / 2.5)
        x = x0 + 70 * ease_in_out_sine(k) * (1 if i != 2 else -1.4)
        y = 845 + 50 * ease_in_out_sine(k) - 20 * math.sin(math.pi * k)
        wob = 0.3 * math.sin(t * 7 + i)
        edmonto(cv, {"t": t * 1.7 + i, "head": 0.3 + 0.3 * wob, "s": 40 * k}, L, x, y, sc, 1 if i != 2 else -1, detail=0.5)
    cv.restore()


def S08(F, u, dur, t):
    lk = LOOKS["morning"]
    L = light_of(lk)
    if t < 77.4:
        cam = Cam(900 + 30 * u, 760, 1.25 + 0.03 * u)
        nest_scene(F, t, lk, cam)
        camp_fg(F, t, lk, cam, {}, blur=8)
        F.post = {"grade": "act1", "bloom": (0.62, 0.45)}
        return
    if t < 79.2:                          # over his shoulder: he watches, head tilted
        cam = Cam(930, 780, 1.4)
        nest_scene(F, t, lk, cam)
        F.defocus(7)
        cv = F.cv
        look_back = smoothstep(78.5, 78.8, t)
        wi = {"t": t, "head_pitch": -0.2 + 0.1 * math.sin(t * 2), "tuft": 0.4, "head_turn": -1 if look_back > 0.5 else 1,
              "blink": blinks(t, 2.2, 0.4)}
        wisp(cv, wi, L, 330, 1150, 1.9, 1)
        F.post = {"grade": "act1", "bloom": (0.62, 0.45)}
        return
    # he runs to her and nestles between her horns; she hums
    cam = Cam(1060, 740, 1.5)
    camp_bg(F, t, lk, cam, {"star_k": 0.05, "star_pos": (1250, 190)})
    cv = F.cv
    cam.apply(cv, 1.0)
    hum = window(t, EV["hum_s8"], EV["hum_s8"] + 1.6, 0.3, 0.8)
    oh = {"breath": t, "head_pitch": 0.25, "listen": 0.15, "blink": blinks(t, 5.0, 3.0), "mouth": hum, "s": 0.0}
    a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    hx, hy = a["head_top"]
    run = clamp((t - 79.2) / 1.0)
    climb = clamp((t - 80.2) / 0.8)
    if run < 1:
        x = 1500 - (1500 - (hx + 140)) * ease_in_out_sine(run)
        wi = {"t": t, "gait": "run", "s": (1500 - x) * 2.0, "tuft": 0.9}
        wisp(cv, wi, L, x + wi["s"] * 0.4, CAMP["oh_y"], 0.4, -1)
    else:
        e = ease_in_out_sine(climb)
        x = (hx + 140) + (hx - 10 - (hx + 140)) * e
        y = CAMP["oh_y"] + (hy + 20 - CAMP["oh_y"]) * e - 80 * math.sin(math.pi * climb)
        settle = smoothstep(80.9, 81.4, t)
        wi = {"t": t, "hop": climb if climb < 1 else None, "hop_len": 0, "hop_h": 0, "crouch": 0.7 * settle,
              "tuft": 0.5 - 0.2 * settle, "blink": max(blinks(t, 3.0), 0.9 * window(t, 81.6, 83.0, 0.4, 0.4)),
              "head_pitch": 0.2 * settle}
        if climb >= 1:
            wi.pop("hop")
        wisp(cv, wi, L, x, y, 0.4, -1 if climb < 0.5 else 1)
    cv.restore()
    camp_fg(F, t, lk, cam, {})
    F.post = {"grade": "act1", "bloom": (0.62, 0.45)}


SHOTS = {"S03": S03, "S04": S04, "S05": S05, "S06": S06, "S07": S07, "S08": S08}
