"""ACT III — THE SECOND SUN (S15–S22)."""
import math

import numpy as np
import skia

import timeline as TL
import world as Wd
from creatures import old_horn, pebble, wisp
from foxfolly.anim import Track, clamp, ease_in_out_sine, smoothstep, window
from rig import Light, c4, cast_shadow, mix, scl
from shotkit import CAMP, LAKE, SHORE, Cam, camp_bg, camp_fg, lake, lake_foreground, pov_rings, shore
from world import LOOKS, W, H, blend_look, light_of
from shots_act1 import blinks, pulses, spring, knot_hole

EV = TL.EV


def star_k(t):
    return Track(TL.STAR_KEYS)(t)


def blink_curve(t, times, dur=0.22):
    b = 0.0
    for t0 in times:
        b = max(b, math.sin(math.pi * clamp((t - t0) / dur)))
    return b


def oh_lying_pose(t, **kw):
    p = {"s": 0.0, "crouch": 1.0, "breath": t, "head_pitch": 0.12, "blink": blink_curve(t, [t - (t % 5.3) + 2.1])}
    p.update(kw)
    return p


def draw_pair_camp(F, t, lk, cam, oh_pose, wi_pose, wisp_in_frill=True, wisp_xy=None, wisp_scale=0.46,
                   wisp_facing=1, shadow=None):
    """Old Horn lying under the Split Tree with Wisp (in her frill by default)."""
    cv = F.cv
    L = light_of(lk)
    cam.apply(cv, 1.0)
    if shadow is not None:
        # long shadow cast by the new light (dir_x < 0 = shadow falls to the left)
        tmp = skia.Path()
        tmp.addOval(skia.Rect(CAMP["oh_x"] - 330, CAMP["oh_y"] - 250, CAMP["oh_x"] + 360, CAMP["oh_y"]))
        cast_shadow(cv, tmp, CAMP["oh_y"] - 4, shadow[0], shadow[1], alpha=shadow[2], blur=14)
    a = old_horn(cv, oh_pose, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    w = None
    if wi_pose is not None:
        if wisp_in_frill:
            nx, ny = a["frill_nest"]
            w = wisp(cv, wi_pose, L, nx + 10, ny + 38, wisp_scale, wisp_facing)
        else:
            w = wisp(cv, wi_pose, L, wisp_xy[0], wisp_xy[1], wisp_scale, wisp_facing)
    cv.restore()
    return a, w


# ======================================================================
def S19(F, u, dur, t):
    """THE HEART SHOT — the second sunrise."""
    fl = ease_in_out_sine(clamp((t - EV["flash"]) / 1.8)) ** 0.8
    lk = blend_look(LOOKS["predawn"], LOOKS["flash"], fl)
    if u < 3.8:                                   # a) the lock-off: south turns white
        st = {"star_k": star_k(t) * (1 - fl), "herd": "alarm", "herd_t": 3 + u, "flash": fl,
              "shadow_k": fl, "oh": "lying"}
        lake(F, t, lk, st)
        lake_foreground(F, t, lk, st)
        F.post = {"grade": "act3_night", "grade_mix": ("act3_flash", fl), "bloom": (0.55, 0.6 + 0.5 * fl),
                  "rays": (Wd.SADDLE_X, 585, 0.9 * fl), "ray_thr": 0.5}
        return
    if u < 7.0:                                   # b) she opens her eyes
        v = u - 3.8
        cam = Cam(1070 + 8 * v, 880 - 4 * v, 1.85 + 0.08 * v)
        st = {"flash": 1.0, "star_k": 0.0}
        camp_bg(F, t, lk, cam, st)
        eye_open = smoothstep(0.5, 1.3, v)
        oh = oh_lying_pose(t, blink=1 - eye_open, head_pitch=0.14 - 0.06 * smoothstep(1.2, 3.2, v),
                           eye_glow=mix((0.80, 0.84, 0.86), (1.4, 1.3, 1.1), eye_open))
        wi = {"t": t, "crouch": 0.8, "head_pitch": -0.25, "tuft": 0.7, "blink": blink_curve(t, [185.9])}
        draw_pair_camp(F, t, lk, cam, oh, wi, shadow=(-1.3, 2.2, 0.35))
        camp_fg(F, t, lk, cam, {})
        F.post = {"grade": "act3_flash", "bloom": (0.6, 0.55), "rays": (1700, 620, 0.6), "ray_thr": 0.6}
        return
    if u < 9.4:                                   # c) her POV — the only real light she sees
        v = u - 7.0
        cam = Cam(1150, 700, 1.1)
        camp_bg(F, t, lk, cam, {"flash": 1.0})
        k = smoothstep(0.0, 1.6, v)
        Wd.glow(F.cv, 1400, 600, 900 + 700 * k, (1.0, 0.94, 0.80), 0.6 + 0.9 * k)
        Wd.glow(F.cv, 1400, 600, 320, (1.0, 1.0, 0.95), 1.2 * k)
        F.post = {"grade": "act3_flash", "pov": 1.0, "bloom": (0.4, 1.3), "vignette": 0.55}
        return
    v = u - 9.4                                   # d) she lifts her head toward it
    cam = Cam(1140 + 6 * v, 895 - 10 * v, 3.1 + 0.08 * v)
    camp_bg(F, t, lk, cam, {"flash": 1.0})
    lift = ease_in_out_sine(clamp(v / 1.5))
    oh = oh_lying_pose(t, blink=0.0, head_pitch=0.08 - 0.42 * lift, eye_glow=(1.5, 1.38, 1.15))
    wi = {"t": t, "crouch": 0.8, "head_pitch": -0.35, "tuft": 0.8}
    draw_pair_camp(F, t, lk, cam, oh, wi, shadow=(-1.3, 2.2, 0.35))
    camp_fg(F, t, lk, cam, {}, blur=9)
    F.post = {"grade": "act3_flash", "bloom": (0.6, 0.6), "rays": (1750, 560, 0.5), "ray_thr": 0.6}




# ======================================================================
def S15(F, u, dur, t):
    """THE LAKE — dusk. Identical lock-off. The star now hangs above the Saddle."""
    lk = LOOKS["dusk"]
    st = {"star_k": star_k(t), "herd": "settle", "ff": 0.8 * smoothstep(137.0, 143.0, t), "oh": "lying",
          "oh_pose": {"crouch": 1.0, "breath": t, "head_pitch": 0.1},
          "wi_pose": {"t": t, "crouch": 0.9, "curl": 0.4, "tuft": 0.4}}
    lake(F, t, lk, st)
    lake_foreground(F, t, lk, st)
    F.post = {"grade": "act3_dusk", "bloom": (0.55, 0.6)}


# ======================================================================
DUET_STARS = [(820, 250), (1010, 170), (1230, 260), (1400, 190)]
NEW_STAR = (1560, 330)


def night_camp(F, t, lk, cam, sk, extra_stars=True, fireflies=0.7):
    camp_bg(F, t, lk, cam, {"star_k": sk, "star_pos": NEW_STAR})
    cv = F.cv
    if extra_stars:
        cam.apply(cv, 0.08)
        for i, (x, y) in enumerate(DUET_STARS):
            tw = 0.0
            if i < len(TL.DUET):
                tw = pulses(t, [TL.DUET[i][0]], 0.9)
            Wd.glow(cv, x, y, 16 + 40 * tw, (0.85, 0.9, 1.0), 0.5 + 0.5 * tw)
            cv.drawCircle(x, y, 2.2 + 1.5 * tw, skia.Paint(AntiAlias=True, Color4f=c4((2.0, 2.0, 2.2))))
        cv.restore()
    cam.apply(cv, 0.6)
    Wd.fireflies(cv, t, fireflies, 0, W, 700, 1000)
    cv.restore()


def S16(F, u, dur, t):
    """Night: the star-counting duet. Then the new star — and she cannot see it."""
    lk = LOOKS["night"]
    cam = Cam(1110, 690, 1.55)
    night_camp(F, t, lk, cam, star_k(t))
    cv = F.cv
    L = light_of(lk)
    cam.apply(cv, 1.0)
    hum = max(pulses(t, [b for a, b in TL.DUET], 0.6), 0.0)
    trill = TL.NEW_STAR_TRILL
    lift = ease_in_out_sine(clamp((t - 154.5) / 2.0))
    oh = {"crouch": 1.0, "breath": t, "head_pitch": 0.12 - 0.42 * lift, "mouth": hum, "blink": blinks(t, 5.5, 2.0)}
    # the new star casts faint shadows
    if t > trill - 1:
        sh = skia.Path()
        sh.addOval(skia.Rect(CAMP["oh_x"] - 320, CAMP["oh_y"] - 240, CAMP["oh_x"] + 340, CAMP["oh_y"]))
        cast_shadow(cv, sh, CAMP["oh_y"] - 4, -0.7, 1.4, alpha=0.18 * smoothstep(trill - 1, trill + 1, t), blur=16)
    a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    hx, hy = a["head_top"]
    # which star is he pointing at?
    target = None
    for i, (c, h) in enumerate(TL.DUET):
        if c - 0.4 <= t < c + 1.2:
            target = DUET_STARS[i]
    chirp = pulses(t, [c for c, h in TL.DUET], 0.3)
    bounce = window(t, trill, trill + 1.4, 0.1, 0.3)
    fade = smoothstep(156.4, 157.6, t)
    think = smoothstep(158.0, 158.6, t)
    if t >= trill - 0.3:
        target = NEW_STAR
    pitch = -0.25
    if target is not None and fade < 0.5:
        sx, sy = cam.to_screen(*target, 0.08)
        wx, wy = cam.to_screen(hx, hy)
        pitch = -min(1.0, max(0.0, math.atan2(wy - sy, sx - wx))) * 0.9
    pitch = pitch * (1 - fade) + (0.35 - 0.15 * think) * fade
    hop = ((t - trill) / 0.35) % 1.0 if bounce > 0.3 else None
    wi = {"t": t, "crouch": 0.3 * (1 - bounce), "tuft": 0.4 + 0.3 * chirp + 0.6 * bounce - 0.5 * fade,
          "beak_open": max(chirp, 0.8 * pulses(t, [trill, trill + 0.25, trill + 0.5], 0.2)), "head_pitch": pitch,
          "head_turn": -1 if 157.0 < t < 158.2 else 1, "blink": blinks(t, 3.2, 0.4), "glow_eye": 0.25}
    if hop is not None:
        wi.update({"hop": hop, "hop_len": 0, "hop_h": 26})
    wisp(cv, wi, L, hx - 12, hy + 16, 0.4, 1)
    cv.restore()
    camp_fg(F, t, lk, cam, {})
    F.post = {"grade": "act3_night", "bloom": (0.5, 0.65)}


# ======================================================================
def S17(F, u, dur, t):
    """The gift: his best treasure, given to her. The warmest moment of the film."""
    lk = LOOKS["night"]
    L = light_of(lk)
    sk = star_k(t)
    if 161.3 <= t < 162.8:                        # at the knot-hole: he takes the crescent out
        kx, ky, kr = CAMP["tree_x"] + 0.15 * CAMP["tree_h"] * 0.11, CAMP["tree_y"] - 0.29 * CAMP["tree_h"], 0.16 * CAMP["tree_h"] * 0.11
        cam = Cam(kx + 40, ky + 30, 3.4)
        night_camp(F, t, lk, cam, sk, fireflies=0.3)
        cv = F.cv
        cam.apply(cv, 0.9)
        took = t >= 162.1
        knot_hole(cv, kx, ky, kr, lk, t, not took, glint=0.6)
        lean = window(t, 161.5, 162.4, 0.3, 0.3)
        wisp(cv, {"t": t, "head_pitch": 0.55 * lean, "crouch": 0.3 * lean, "carry": took, "tuft": 0.6,
                  "blink": blinks(t, 3.0), "glow_eye": 0.3}, L, kx + kr * 1.3, ky + kr * 1.35, 0.36, -1)
        cv.restore()
        F.post = {"grade": "act3_night", "bloom": (0.5, 0.65)}
        return
    if t < 168.4:
        close = ease_in_out_sine(clamp((t - 163.6) / 1.0))
        L = Light(tuple(v * (1 + 0.5 * close) for v in L.ambient), L.key, L.key_dir, (0.75, 0.85, 1.0), 0.09,
                  1.0, L.shade)
        cam = Cam(1090 + 110 * close, 800 + 130 * close, 1.75 + 1.25 * close)
        night_camp(F, t, lk, cam, sk)
        cv = F.cv
        cam.apply(cv, 1.0)
        rest = ease_in_out_sine(clamp((t - 165.1) / 0.9))
        hum = window(t, EV["hum_gift"], EV["hum_gift"] + 2.2, 0.3, 1.0)
        oh = {"crouch": 1.0, "breath": t, "head_pitch": 0.12 + 0.1 * rest, "mouth": hum,
              "blink": max(blinks(t, 6.0, 1.0), 0.8 * smoothstep(167.0, 168.2, t))}
        a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
        hx, hy = a["head_top"]
        bx, by = a["beak"]
        nx, ny = a["frill_nest"]
        if t < 161.3:                              # off her head, toward the tree
            k = clamp((t - 160.0) / 1.3)
            x = hx + (500 - hx) * ease_in_out_sine(k)
            y = hy + (CAMP["oh_y"] - hy) * k - 80 * math.sin(math.pi * k)
            wisp(cv, {"t": t, "hop": k, "hop_len": 0, "hop_h": 0, "tuft": 0.6}, L, x, y, 0.4, -1)
        elif t < 164.2:                            # back down with the pebble
            k = clamp((t - 162.8) / 1.4)
            x = 520 + (bx + 60 - 520) * ease_in_out_sine(k)
            wisp(cv, {"t": t, "hop": (k * 3) % 1.0, "hop_len": 0, "hop_h": 30, "carry": True, "tuft": 0.7}, L,
                 x, CAMP["oh_y"], 0.4, 1)
        else:
            push = window(t, 164.3, 165.6, 0.4, 0.4)
            curl_k = ease_in_out_sine(clamp((t - 166.8) / 1.4))
            if t < EV["pebble_give"]:
                wi = {"t": t, "carry": True, "head_pitch": 0.3 * push, "tuft": 0.6}
                wisp(cv, wi, L, bx + 60, CAMP["oh_y"], 0.4, -1)
            else:
                pebble(cv, bx + 14, by + 2, 7.0, L, glint=0.6 * window(t, 165.0, 166.8, 0.3, 0.8))
                if curl_k <= 0:
                    wisp(cv, {"t": t, "head_pitch": 0.4 * push, "crouch": 0.2, "tuft": 0.5 + 0.3 * smoothstep(165.5, 166.0, t),
                              "blink": blinks(t, 2.6)}, L, bx + 60, CAMP["oh_y"], 0.4, -1)
                else:
                    x = bx + 60 + (nx + 4 - bx - 60) * curl_k
                    y = CAMP["oh_y"] + (ny + 40 - CAMP["oh_y"]) * curl_k - 60 * math.sin(math.pi * curl_k)
                    wisp(cv, {"t": t, "curl": curl_k, "crouch": curl_k, "tuft": 0.4, "blink": curl_k}, L, x, y, 0.4, 1)
        cv.restore()
        if close < 0.5:
            camp_fg(F, t, lk, cam, {})
        F.post = {"grade": "act3_night", "bloom": (0.5, 0.65)}
        return
    # wide: two small silhouettes beneath the tree, fireflies, the star burning above
    v = t - 168.4
    cam = Cam(900 + 10 * v, 620, 1.0 + 0.01 * v)
    night_camp(F, t, lk, cam, sk, fireflies=1.0)
    cv = F.cv
    cam.apply(cv, 1.0)
    a = old_horn(cv, {"crouch": 1.0, "breath": t, "head_pitch": 0.22, "blink": 1.0}, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    nx, ny = a["frill_nest"]
    wisp(cv, {"t": t, "curl": 1.0, "crouch": 1.0, "blink": 1.0}, L, nx + 4, ny + 40, 0.4, 1)
    bx, by = a["beak"]
    pebble(cv, bx + 14, by + 2, 7.0, L, glint=0.35)
    cv.restore()
    camp_fg(F, t, lk, cam, {})
    F.post = {"grade": "act3_night", "bloom": (0.5, 0.7)}


# ======================================================================
def S18(F, u, dur, t):
    lk = LOOKS["predawn"]
    L = light_of(lk)
    if t < 176.0:                                 # his eye opens: something is wrong
        cam = Cam(1070, 900, 4.0)
        camp_bg(F, t, lk, cam, {"star_k": star_k(t), "star_pos": NEW_STAR})
        cv = F.cv
        cam.apply(cv, 1.0)
        a = old_horn(cv, {"crouch": 1.0, "breath": t, "head_pitch": 0.22, "blink": 1.0}, L, CAMP["oh_x"], CAMP["oh_y"],
                     CAMP["oh_s"], 1)
        nx, ny = a["frill_nest"]
        opn = smoothstep(173.6, 174.0, t)
        wisp(cv, {"t": t * (1 - opn * 0.9), "curl": 1.0 - 0.25 * smoothstep(174.6, 175.4, t), "crouch": 1.0,
                  "blink": 1 - opn, "eye_dir": 0.0 if t < 175.0 else 3.14, "tuft": 0.2 + 0.5 * smoothstep(174.8, 175.3, t),
                  "glow_eye": 0.2}, L, nx + 4, ny + 40, 0.4, 1)
        cv.restore()
        F.post = {"grade": "act3_night", "bloom": (0.5, 0.6)}
        return
    st = {"star_k": star_k(t), "herd": "alarm", "herd_t": t - 176.0, "oh": "lying", "wisp": True,
          "wi_pose": {"t": t, "crouch": 0.6, "tuft": 0.9, "curl": 0.0}}
    lake(F, t, lk, st)
    lake_foreground(F, t, lk, st)
    F.post = {"grade": "act3_night", "bloom": (0.55, 0.6)}


# ======================================================================
def S20(F, u, dur, t):
    """A beat of silence, then the ground heaves; the lake rises; the herd scatters."""
    k = smoothstep(191.0, 199.0, t)
    lk = blend_look(LOOKS["flash"], LOOKS["fire"], 0.25 * k)
    heave = EV["seismic"]
    shake = 14 * window(t, heave, 199.5, 0.15, 1.0) * (0.6 + 0.4 * math.sin(t * 3))
    if t < 195.2:
        surge = ease_in_out_sine(clamp((t - heave - 0.4) / 2.6))
        st = {"herd": "flee" if t > heave + 0.3 else "alarm", "herd_t": max(0.0, t - heave - 0.3), "flash": 0.6,
              "surge": surge, "shadow_k": 0.6, "oh": "lying", "oh_pose": {"crouch": 0.4, "breath": t, "head_pitch": -0.1}}
        lake(F, t, lk, st)
        lake_foreground(F, t, lk, st)
        F.post = {"grade": "act3_flash", "bloom": (0.6, 0.55), "shake": shake, "rays": (Wd.SADDLE_X, 585, 0.4)}
        return
    cam = Cam(1060, 830, 1.7)
    camp_bg(F, t, lk, cam, {"flash": 0.5, "surge": 1.0})
    cv = F.cv
    L = light_of(lk)
    cam.apply(cv, 1.0)
    brace = 0.35 + 0.1 * math.sin(t * 17)
    oh = {"crouch": brace, "breath": t * 2.5, "head_pitch": -0.05, "shudder": 1.0, "blink": 0.0, "listen": 0.2 * math.sin(t * 5)}
    a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    nx, ny = a["frill_nest"]
    wisp(cv, {"t": t, "crouch": 0.9, "tuft": 1.0, "shake": 0.4, "blink": 0.0, "head_pitch": 0.2}, L, nx + 4, ny + 36, 0.4, 1)
    cv.restore()
    Wd.ash(cv, t, 0.5, density=0.2, col=(0.6, 0.5, 0.4), wind_x=4, fall=160)     # dust shaken loose
    camp_fg(F, t, lk, cam, {})
    F.post = {"grade": "act3_flash", "grade_mix": ("act3_fire", 0.3), "bloom": (0.6, 0.5), "shake": shake}


# ======================================================================
STEAM = [(np.random.default_rng(5).random(), np.random.default_rng(6 + i).random(), 199.8 + i * 0.37) for i in range(40)]


def S21(F, u, dur, t):
    """The meteor shower: beautiful and wrong."""
    k = smoothstep(199.0, 206.0, t)
    lk = blend_look(LOOKS["flash"], LOOKS["fire"], 0.35 + 0.65 * k)
    beads = smoothstep(EV["beads_start"], 201.5, t)
    shake = 5 * (0.6 + 0.4 * math.sin(t * 2))
    if t < 204.0:
        st = {"beads": beads, "burn": 0.6 * smoothstep(200.5, 204, t), "herd": None, "oh": "lying",
              "oh_pose": {"crouch": 0.3, "breath": t, "head_pitch": -0.1}, "surge": 0.6}
        lake(F, t, lk, st)
        cv = F.cv
        Wd.bead_shower(cv, t, EV["beads_start"], beads, horizon=640)
        for i, (a_, b_, t0) in enumerate(STEAM):
            x = 200 + ((i * 0.618) % 1.0) * 1500
            y = LAKE["water_y0"] + 30 + ((i * 0.37) % 1.0) * 220
            Wd.steam(cv, x, y, t - t0, a=beads, s=0.6 + 0.6 * ((i * 0.37) % 1.0))
        lake_foreground(F, t, lk, st)
        F.post = {"grade": "act3_fire", "grade_mix": ("act3_flash", 1 - k), "bloom": (0.55, 0.7), "heat": 1.2 * k,
                  "shake": shake}
        return
    if t < 206.6:                                 # beads through the leaves; ferns catch
        cam = Cam(1060, 780, 1.35)
        camp_bg(F, t, lk, cam, {"beads": 1.0, "burn": 0.8})
        cv = F.cv
        L = light_of(lk)
        cam.apply(cv, 1.0)
        a = old_horn(cv, {"crouch": 0.25, "breath": t * 2.2, "head_pitch": -0.1 + 0.1 * math.sin(t * 2), "blink": 0.0,
                          "listen": 0.3 * math.sin(t * 1.7), "eye_glow": (1.2, 0.6, 0.3)}, L,
                     CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
        Wd.flames(cv, 1500, CAMP["oh_y"] + 10, 160, 60 * smoothstep(204.3, 205.5, t), t, a=1.0, seed=3)
        cv.restore()
        Wd.bead_shower(cv, t, EV["beads_start"], 1.0, horizon=1100)
        camp_fg(F, t, lk, cam, {})
        F.post = {"grade": "act3_fire", "bloom": (0.55, 0.7), "heat": 1.2, "shake": shake}
        return
    if t < 210.0:                                 # the burrow: safety far too small for him
        lk2 = dict(lk)
        cam = Cam(470, 850, 2.0)
        bx, by = SHORE["burrow"]
        L = light_of(lk2)
        hes = EV["burrow_hesitate"]
        turn = EV["turn_back"]

        def chars(cv):
            if t < 206.9:
                kx = Track([(206.6, 480), (206.9, bx + 8)])(t)
                burrower(cv, {"t": t, "run": 1.0}, L, kx, by + 4, 1.0, -1)
            if t < hes:
                wx = Track([(206.6, 820), (hes, 320)])(t)
                wisp(cv, {"t": t, "gait": "run", "s": (820 - wx) * 2.4, "tuft": 1.0}, L, wx + (820 - wx) * 2.4 * 0.44,
                     by + 4, 0.44, -1)
            elif t < turn:
                look = smoothstep(hes + 0.5, turn - 0.2, t)
                wisp(cv, {"t": t, "head_pitch": 0.5 * (1 - look), "crouch": 0.3, "tuft": 0.7, "head_turn": -1 if look > 0.5 else 1,
                          "blink": 0.0}, L, 320, by + 4, 0.44, -1)
            else:
                wx = Track([(turn, 320), (210.0, 1000)])(t)
                rs = (wx - 320) * 2.4
                wisp(cv, {"t": t, "gait": "run", "s": rs, "tuft": 1.0}, L, wx - rs * 0.44, by + 4, 0.44, 1)

        from creatures import burrower
        shore(F, t, lk2, cam, {"beads": 1.0}, draw_chars=chars)
        Wd.bead_shower(F.cv, t, EV["beads_start"], 0.8, horizon=1100)
        F.post = {"grade": "act3_fire", "bloom": (0.55, 0.7), "heat": 1.0, "shake": shake}
        return
    # running back to her through the falling light
    cam = Cam(960, 700, 1.05)
    camp_bg(F, t, lk, cam, {"beads": 1.0, "burn": 1.0})
    cv = F.cv
    L = light_of(lk)
    cam.apply(cv, 1.0)
    a = old_horn(cv, {"crouch": 0.3 + 0.7 * smoothstep(213.5, 215.0, t), "breath": t * 2.0, "head_pitch": 0.0,
                      "listen": 0.35, "blink": 0.0, "eye_glow": (1.2, 0.6, 0.3)}, L,
                 CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    cx, cy = a["chin"]
    wx = Track([(210.0, 1900), (215.0, cx + 60)])(t)
    rs = (1900 - wx) * 2.4
    wisp(cv, {"t": t, "gait": "run", "s": rs, "tuft": 1.0}, L, wx + rs * 0.4, CAMP["oh_y"], 0.4, -1)
    for i in range(5):
        Wd.flames(cv, 1250 + i * 180, CAMP["oh_y"] + 20, 120, 50 + 20 * (i % 2), t, a=0.9, seed=10 + i)
    cv.restore()
    Wd.bead_shower(cv, t, EV["beads_start"], 1.0, horizon=1100)
    camp_fg(F, t, lk, cam, {})
    F.post = {"grade": "act3_fire", "bloom": (0.55, 0.75), "heat": 1.3, "shake": shake}


# ======================================================================
def S22(F, u, dur, t):
    lk = LOOKS["fire"]
    L = light_of(lk)
    if t < 218.6:
        cam = Cam(1100, 860, 1.9 + 0.12 * (t - 215))
        camp_bg(F, t, lk, cam, {"beads": 1.0, "burn": 1.0})
        cv = F.cv
        cam.apply(cv, 1.0)
        roof = ease_in_out_sine(clamp((t - 216.6) / 1.6))
        a = old_horn(cv, {"crouch": 1.0, "breath": t * 1.6, "head_pitch": 0.12 + 0.28 * roof, "blink": 0.0,
                          "eye_glow": (1.3, 0.62, 0.3)}, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
        cx, cy = a["chin"]
        dive = clamp((t - 215.0) / 0.9)
        x = cx + 120 - 150 * ease_in_out_sine(dive)
        wisp(cv, {"t": t, "crouch": 0.8 * dive, "curl": 0.6 * roof, "tuft": 0.6, "blink": 0.0, "head_pitch": -0.2}, L,
             x, CAMP["oh_y"] - 4, 0.4, -1 if dive < 1 else 1)
        bx, by = a["beak"]
        pebble(cv, cx - 10, CAMP["oh_y"] - 8, 7.0, L, glint=0.35)
        cv.restore()
        Wd.bead_shower(cv, t, EV["beads_start"], 1.0, horizon=1100)
        F.post = {"grade": "act3_fire", "bloom": (0.55, 0.75), "heat": 1.0, "shake": 3}
        return
    # extreme close-up: her clouded eye glowing orange, his amber eye beside it
    v = t - 218.6
    from creatures import oh_anchor
    ex0, ey0 = oh_anchor({"crouch": 1.0, "breath": t * 1.2, "head_pitch": 0.4}, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"])["eye"]
    cam = Cam(ex0 + 34, ey0 + 4, 8.0 + 0.3 * v)
    camp_bg(F, t, lk, cam, {"beads": 1.0})
    cv = F.cv
    cam.apply(cv, 1.0)
    hum = max(pulses(t, [EV["final_hum"], EV["final_hum2"]], 1.2), 0.0)
    a = old_horn(cv, {"crouch": 1.0, "breath": t * 1.2, "head_pitch": 0.4, "blink": blinks(t, 4.0, 1.5) * 0.6,
                      "eye_glow": (1.35, 0.66, 0.32), "mouth": hum}, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    ex, ey = a["eye"]
    chirp = pulses(t, [EV["final_chirp"]], 0.35)
    wisp(cv, {"t": t, "crouch": 0.8, "tuft": 0.5 + 0.3 * chirp, "beak_open": chirp, "head_pitch": -0.05,
              "blink": blinks(t, 3.0, 0.6), "glow_eye": 0.5}, L, ex + 44 + 25.6, ey + 6 + 54.8, 0.4, -1)
    cv.restore()
    white = smoothstep(222.4, 225.0, t) ** 1.6
    F.post = {"grade": "act3_fire", "bloom": (0.5, 0.8 + 1.5 * white), "white": white, "white_col": (1.0, 0.97, 0.92)}


SHOTS = {"S15": S15, "S16": S16, "S17": S17, "S18": S18, "S19": S19, "S20": S20, "S21": S21, "S22": S22}
