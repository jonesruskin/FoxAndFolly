"""ACT II — THE AFTERNOON (S9–S14)."""
import math

import numpy as np
import skia

import timeline as TL
import world as Wd
from creatures import OH_GAIT, RX_GAIT, old_horn, rex, wisp
from foxfolly.anim import Track, clamp, ease_in_out_sine, smoothstep, window
from rig import Light, c4, cast_shadow, contact_shadow, mix, scl
from shotkit import CAMP, FOREST, Cam, camp_bg, camp_fg, footprint, forest_bg, forest_fg, pov_rings
from shots_act1 import blinks, pulses, spring
from world import LOOKS, W, H, blend_look, light_of

EV = TL.EV
FAR_STEPS = [97.9, 99.1, 100.3]           # distant footfalls that make the puddle tremble


def shade_light(lk, k=0.65):
    L = light_of(lk)
    return Light(tuple(v * k for v in L.ambient), L.key, L.key_dir, (0.8, 0.9, 1.0), L.rim_w, 0.35, 0.5)


# ======================================================================
S9_S = Track([(83.0, -560.0), (84.6, -160.0), (85.8, 0.0)], mode="pchip")


def S09(F, u, dur, t):
    """Harsh midday. She slows, breathing hard, and lies down in the shade."""
    lk = LOOKS["midday"]
    cam = Cam(1020, 800, 1.3)
    camp_bg(F, t, lk, cam, {})
    cv = F.cv
    cam.apply(cv, 1.0)
    # the pool of shade under the canopy
    cv.drawOval(skia.Rect(420, 930, 1500, 1070), skia.Paint(AntiAlias=True, Color4f=c4((0.05, 0.08, 0.04), 0.45),
                                                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
    L = shade_light(lk)
    s_end = OH_GAIT.settle(0.0)
    s = S9_S(t) * (s_end / 1.0 if False else 1.0)
    s = min(s, s_end)
    lie = ease_in_out_sine(clamp((t - EV["lie_down"]) / 1.8))
    oh = {"s": s, "crouch": lie, "breath": t * 1.6, "head_pitch": 0.1 + 0.1 * lie, "blink": blinks(t, 3.6, 0.2),
          "listen": 0.1}
    a = old_horn(cv, oh, L, CAMP["oh_x"], CAMP["oh_y"], CAMP["oh_s"], 1)
    # Wisp: restless, then nudging her cheek
    cx, cy = a["chin"]
    if t < 88.2:
        ph = ((t - 83.0) / 0.7) % 1.0
        x = 1350 + 60 * math.sin(t * 1.3)
        wi = {"t": t, "hop": ph if t > 85.0 else None, "hop_len": 0, "hop_h": 22, "tuft": 0.5, "blink": blinks(t, 2.5),
              "head_turn": -1 if math.sin(t * 1.3) > 0 else 1}
        if wi["hop"] is None:
            wi.pop("hop")
            wi.update({"gait": "walk", "s": (t - 83.0) * 40})
        wisp(cv, wi, L, x, CAMP["oh_y"], 0.42, -1)
    else:
        nudge = max(0.0, math.sin((t - 88.2) * 7.5)) * window(t, 88.2, 90.0, 0.2, 0.2)
        x = cx + 70 - 22 * nudge
        wi = {"t": t, "head_pitch": 0.35 * nudge, "crouch": 0.2 + 0.2 * nudge, "tuft": 0.35, "blink": blinks(t, 2.2, 0.7),
              "beak_open": 0.3 * pulses(t, [89.2], 0.3)}
        contact_shadow(cv, x, CAMP["oh_y"] + 2, 30, 6, 0.35)
        wisp(cv, wi, L, x, CAMP["oh_y"], 0.42, -1)
    cv.restore()
    camp_fg(F, t, lk, cam, {})
    F.post = {"grade": "act2", "bloom": (0.7, 0.5), "vignette": 0.3}


# ======================================================================
def dragonfly_path(t):
    x = Track([(90.0, 700), (92.5, 1250), (94.5, 1700), (94.6, 980), (95.6, 1080), (96.4, 1085)])(t)
    y = 700 + 60 * math.sin(t * 3.1) + 26 * math.sin(t * 7.3)
    return x, y


WS = 0.78      # Wisp scale in the forest (he must read clearly)
OS = 0.74      # Old Horn scale in the forest


def S10(F, u, dur, t):
    if t < 94.5:                                  # into the horsetails, away from home
        k = smoothstep(90.0, 94.5, t)
        lk = blend_look(LOOKS["midday"], LOOKS["fern"], 0.5 * k)
        cam = Cam(900 + 160 * k, 720, 1.0)
        forest_bg(F, t, lk, cam, {"shafts": 0.6})
        cv = F.cv
        L = light_of(lk)
        cam.apply(cv, 1.0)
        dx, dy = dragonfly_path(t)
        Wd.dragonfly(cv, dx, dy, t, s=3.2, col=(0.15, 0.45, 1.0), heading=0.0)
        Wd.glow(cv, dx, dy, 40, (0.4, 0.7, 1.0), 0.25)
        wx = 260 + 1150 * ease_in_out_sine(k)
        run_s = (t - 90) * 300
        wisp(cv, {"t": t, "gait": "run", "s": run_s, "tuft": 1.0, "head_pitch": -0.3}, L,
             wx - run_s * WS, FOREST["ground"], WS, 1)
        cv.restore()
        forest_fg(F, t, lk, cam, {})
        F.post = {"grade": "act2", "bloom": (0.65, 0.45)}
        return
    lk = LOOKS["fern"]
    L = light_of(lk)
    if t < 97.4:                                  # the catch — triumph
        cam = Cam(1000, 760, 1.25)
        forest_bg(F, t, lk, cam, {"shafts": 0.9})
        cv = F.cv
        cam.apply(cv, 1.0)
        catch = EV["dragonfly_catch"]
        pounce = clamp((t - (catch - 0.5)) / 0.7)
        if t < catch:
            dx, dy = dragonfly_path(t)
            Wd.dragonfly(cv, dx, dy, t, s=3.0, col=(0.15, 0.45, 1.0))
            Wd.glow(cv, dx, dy, 40, (0.4, 0.7, 1.0), 0.25)
        if 0 < pounce < 1:
            wi = {"t": t, "hop": pounce, "hop_len": 0, "hop_h": 170, "tuft": 1.0, "head_pitch": -0.5 * (1 - pounce),
                  "beak_open": 1.0 - pounce}
            x = 860 + 150 * ease_in_out_sine(pounce)
        elif t < catch - 0.5:
            wi = {"t": t, "crouch": 0.55, "tuft": 0.8, "head_pitch": -0.35, "tail": 0.2 * math.sin(t * 9)}
            x = 860
        else:
            trium = spring(t, catch + 0.1, freq=10, damp=5)
            wi = {"t": t, "tuft": 0.6 + 0.4 * trium, "head_pitch": -0.2, "blink": blinks(t, 2.0, 0.3)}
            x = 1010
        w = wisp(cv, wi, L, x, FOREST["ground"], WS, 1)
        cv.restore()
        if t >= catch:
            bx, by = cam.to_screen(*w["beak"])
            Wd.dragonfly(cv, bx + 8, by + 4, t, s=1.4 * cam.z, col=(0.15, 0.45, 1.0), heading=0.6)
        forest_fg(F, t, lk, cam, {})
        F.post = {"grade": "act2", "bloom": (0.65, 0.5)}
        return
    # silence. the print beside him, the water trembling
    v = t - 97.4
    z = 1.25 + 0.55 * ease_in_out_sine(clamp(v / 3.4))
    cam = Cam(1080 + 40 * v, 800 + 16 * v, z)
    forest_bg(F, t, lk, cam, {"shafts": 0.6, "gust": 0.15})
    cv = F.cv
    cam.apply(cv, 1.0)
    trem = max(pulses(t, FAR_STEPS, 0.9), 0.25 * smoothstep(97.6, 98.4, t))
    footprint(cv, 1300, FOREST["ground"] + 26, t, lk, tremble=trem, t0=97.6)
    freeze = smoothstep(97.3, 97.7, t)
    look = math.sin(max(0, t - 97.8) * 2.2) * (1 - smoothstep(99.5, 100.2, t))
    wi = {"t": t * (1 - 0.9 * freeze), "tuft": 0.9 - 0.7 * freeze, "crouch": 0.35 * freeze, "head_pitch": 0.15,
          "eye_dir": 3.14 * (look < 0), "blink": 0.0, "head_turn": -1 if look < -0.3 else 1}
    w = wisp(cv, wi, L, 1010, FOREST["ground"], WS, 1)
    cv.restore()
    bx, by = cam.to_screen(*w["beak"])
    Wd.dragonfly(cv, bx + 8, by + 4, t, s=1.4 * cam.z, col=(0.15, 0.45, 1.0), heading=0.6)
    forest_fg(F, t, lk, cam, {"gust": 0.15})
    F.post = {"grade": "act2", "bloom": (0.65, 0.5), "vignette": 0.5}


# ======================================================================
def rex_pose(t, low=0.85):
    boom = pulses(t, EV["rex_boom"], 0.9)
    return {"t": t, "head_low": low, "nostril": 0.5 + 0.5 * math.sin(t * 2.2) + 0.5 * boom, "jaw": 0.05 * boom, "s": 0.0}


def rex_light(lk):
    L = light_of(lk)
    return Light(tuple(v * 0.8 for v in L.ambient), L.key, -1.3, (0.75, 0.95, 0.6), 0.07, 0.9, 0.6)


def S11(F, u, dur, t):
    lk = LOOKS["fern"]
    L = light_of(lk)
    Lr = rex_light(lk)
    if t < 104.0:                                 # reveal: the head slides out of the ferns
        v = t - 101.0
        cam = Cam(1000, 640, 1.0 + 0.04 * v)
        forest_bg(F, t, lk, cam, {"shafts": 0.4, "gust": 0.3})
        cv = F.cv
        cam.apply(cv, 0.95)
        emerge = ease_in_out_sine(clamp(v / 2.4))
        rex(cv, rex_pose(t), Lr, 1900 - 260 * emerge, 1010, 0.9, -1)
        cv.restore()
        cam.apply(cv, 1.0)
        wisp(cv, {"t": t * 0.1, "crouch": 0.35, "tuft": 0.2, "blink": 0.0}, L, 470, FOREST["ground"], WS, 1)
        cv.restore()
        forest_fg(F, t, lk, cam, {"gust": 0.3}, part=lambda i: (200 * emerge if i in (1, 3) else 0))
        F.post = {"grade": "act2", "bloom": (0.7, 0.45), "vignette": 0.55}
        return
    if t < 108.8:                                 # rack focus between his eye and the rex's
        focus = smoothstep(105.5, 106.3, t) * (1 - smoothstep(107.1, 107.6, t))
        cam = Cam(1100, 560, 1.2)
        forest_bg(F, t, lk, cam, {"shafts": 0.3, "gust": 0.2})
        with F.layer(blur=16 * (1 - focus)) as c2:
            rex(c2, rex_pose(t, 1.0), Lr, 2010, 1010, 1.25, -1)
        F.defocus(2.0)
        broken = pulses(t, [EV["broken_call"]], 0.5)
        with F.layer(blur=16 * focus) as c3:
            wisp(c3, {"t": t * 0.1 + broken * math.sin(t * 60) * 0.02, "tuft": 0.15, "beak_open": 0.7 * broken,
                      "blink": 0.0, "head_pitch": -0.1, "crouch": 0.3}, L, 230, 1110, 2.9, 1)
        F.post = {"grade": "act2", "bloom": (0.7, 0.45), "vignette": 0.6}
        return
    cam = Cam(1000, 700, 1.05)                    # the Hunter takes one slow step
    forest_bg(F, t, lk, cam, {"shafts": 0.3, "gust": 0.2})
    cv = F.cv
    cam.apply(cv, 0.95)
    step = ease_in_out_sine(clamp((t - 108.8) / 1.2))
    rex(cv, dict(rex_pose(t), s=110 * step), Lr, 1640 + 110 * step * 0.9, 1010, 0.9, -1)
    cv.restore()
    cam.apply(cv, 1.0)
    wisp(cv, {"t": t * 0.1, "crouch": 0.4, "tuft": 0.1, "blink": 0.0}, L, 470, FOREST["ground"], WS, 1)
    cv.restore()
    forest_fg(F, t, lk, cam, {"gust": 0.2})
    F.post = {"grade": "act2", "bloom": (0.7, 0.45), "vignette": 0.55}


# ======================================================================
OH12_S = Track([(110.0, -1100.0), (111.2, -560.0), (112.4, -60.0), (112.9, 0.0)], mode="pchip")
REX_CIRCLE = Track([(113.0, 1900), (116.0, 1420), (118.0, 1620), (121.0, 1950), (123.0, 2000)], mode="pchip")


def S12(F, u, dur, t):
    lk = LOOKS["fern"]
    L = light_of(lk)
    Lr = rex_light(lk)
    if 113.2 <= t < 118.0:                        # her POV: the rex exists only as dark rings
        cam = Cam(1000, 620, 1.1)
        forest_bg(F, t, dict(lk, ambient=scl(lk["ambient"], 1.6)), cam, {"shafts": 1.0})
        cv = F.cv
        Wd.glow(cv, 700, 360, 700, (0.75, 0.95, 0.6), 0.35)
        Wd.glow(cv, 1400, 420, 600, (0.8, 1.0, 0.7), 0.3)
        Wd.glow(cv, 960, 940, 120, (1.0, 0.75, 0.45), 0.8)      # the small warm shape beneath her: him
        for k, ts in enumerate(EV["rex_steps"]):
            if ts > 118:
                break
            rx = REX_CIRCLE(ts)
            pov_rings(cv, (rx - 1000) * 1.1 + 300, 720, t, ts, warm=False, a=1.0, n=3, speed=340)
        F.post = {"grade": "act2", "pov": 0.55, "bloom": (0.5, 0.6), "vignette": 0.6}
        return
    cam = Cam(1000, 700, 1.0) if t < 113.2 else Cam(1040, 730, 1.1)
    gust = 1.0 + 3.0 * window(t, 110.8, 112.6, 0.2, 0.6)
    forest_bg(F, t, lk, cam, {"shafts": 0.35, "gust": gust})
    cv = F.cv
    if t >= 113.2:
        cam.apply(cv, 0.8)
        rx = REX_CIRCLE(t)
        fac = -1 if (REX_CIRCLE(t + 0.05) - rx) < 0 else 1
        rs = (t - 113.0) * 200
        rex(cv, dict(rex_pose(t, 0.7), s=rs), Lr, rx - fac * rs * 0.5, 960, 0.5, fac, detail=0.7)
        cv.restore()
    cam.apply(cv, 1.0)
    s = OH12_S(t)
    rx = REX_CIRCLE(t) if t >= 113.2 else 1700
    track = clamp((rx - 1400) / 450, -1, 1)          # her broken horn follows every step
    oh = {"s": s, "breath": t * 1.8, "head_pitch": 0.34 - 0.12 * track, "listen": 0.25 * track,
          "blink": 0.0, "crouch": 0.08}
    a = old_horn(cv, oh, L, 560, FOREST["ground"], OS, 1)
    wisp(cv, {"t": t * 0.3, "crouch": 0.55, "tuft": 0.1, "blink": 0.0, "head_pitch": 0.2}, L, 900, FOREST["ground"],
         WS, 1)
    cv.restore()
    forest_fg(F, t, lk, cam, {"gust": gust}, part=lambda i: (-300 * window(t, 110.9, 112.4, 0.3, 0.8) if i in (0, 2) else 0))
    F.post = {"grade": "act2", "bloom": (0.7, 0.45), "vignette": 0.5,
              "shake": 6 * window(t, 111.0, 111.9, 0.1, 0.5)}


# ======================================================================
def S13(F, u, dur, t):
    lk = LOOKS["fern"]
    L = light_of(lk)
    Lr = rex_light(lk)
    cam = Cam(1000, 730, 1.1) if t < 126 else Cam(840, 800, 1.55)
    forest_bg(F, t, lk, cam, {"shafts": 0.4})
    cv = F.cv
    if t < 128.5:
        cam.apply(cv, 0.8)
        leave = ease_in_out_sine(clamp((t - EV["rex_leave"]) / 3.5))
        rs = 460 * leave * 2.0
        rex(cv, dict(rex_pose(t, 0.6 + 0.3 * leave), s=rs), Lr, 1950 - rs * 0.5, 960, 0.5, 1, detail=0.6)
        cv.restore()
    cam.apply(cv, 1.0)
    buckle = EV["buckle"]
    sink = Track([(buckle - 0.1, 0.08), (buckle + 0.35, 0.55), (buckle + 0.6, 0.48), (buckle + 1.6, 1.0)], mode="pchip")(t)
    hum = window(t, EV["hum_shaky"], EV["hum_shaky"] + 2.0, 0.3, 0.6) * (0.7 + 0.3 * math.sin(t * 23))
    oh = {"s": 0.0, "breath": t * 2.0, "crouch": sink, "head_pitch": 0.34 - 0.14 * sink,
          "shudder": window(t, buckle - 0.4, buckle + 1.0, 0.2, 0.5), "blink": blinks(t, 3.3, 0.9), "mouth": hum}
    a = old_horn(cv, oh, L, 560, FOREST["ground"], OS, 1)
    if t < 126.8:
        wisp(cv, {"t": t, "crouch": 0.5, "tuft": 0.2, "blink": blinks(t, 2.0)}, L, 900, FOREST["ground"], WS, 1)
    else:
        cx, cy = a["chin"]
        press = ease_in_out_sine(clamp((t - 126.8) / 0.8))
        x = 980 + (cx + 45 - 980) * press
        wisp(cv, {"t": t, "crouch": 0.45, "tuft": 0.1, "blink": 0.85 * smoothstep(128.0, 128.5, t), "head_pitch": 0.35 * press},
             L, x, FOREST["ground"] - 8 * press, WS, -1)
    cv.restore()
    forest_fg(F, t, lk, cam, {})
    F.post = {"grade": "act2", "bloom": (0.7, 0.45), "vignette": 0.55}


# ======================================================================
def S14(F, u, dur, t):
    """Walking home at golden hour; he walks right under her chin, chirping constantly."""
    lk = LOOKS["golden"]
    cv = F.cv
    cam = Cam(820 + 60 * u, 700, 1.3)
    cam.apply(cv, 0.1)
    Wd.sky(cv, lk, t, horizon=820)
    cv.restore()
    cam.apply(cv, 0.3)
    r = Wd.ridge_path(740, 60, seed=71, saddle_x=1560)
    Wd.vgrad(cv, r, 640, 820, Wd.fogged(scl(lk["plant"], 0.4), lk, 0.55), Wd.fogged(scl(lk["plant"], 0.4), lk, 0.3))
    cv.restore()
    cam.apply(cv, 1.0)
    g = Wd.catmull([(-500, 830), (600, 815), (1300, 828), (2500, 812), (2500, 1400), (-500, 1400)])
    Wd.vgrad(cv, g, 815, 1080, scl(lk["plant"], 0.5), scl(lk["plant"], 0.12))
    rng = np.random.default_rng(81)
    for i in range(24):
        Wd.fern(cv, -400 + i * 120 + rng.random() * 50, 850 + rng.random() * 20, 110 + rng.random() * 50,
                scl(lk["plant"], 0.55), t, seed=900 + i, n_fronds=7)
    L = light_of(lk)
    s = (t - 130.0) * 110.0
    ground = 880
    oh_x = 420
    shadow_path = skia.Path()
    shadow_path.addOval(skia.Rect(oh_x + s * 0.5 - 300, ground - 250, oh_x + s * 0.5 + 330, ground))
    cast_shadow(cv, shadow_path, ground, 1.8, 3.0, alpha=0.65, blur=6)
    a = old_horn(cv, {"s": s, "breath": t * 1.3, "head_pitch": 0.2, "listen": 0.2, "blink": blinks(t, 4.0)}, L, oh_x, ground, 0.5, 1)
    cx, cy = a["chin"]
    chirps = [130.3 + 0.78 * k for k in range(8)]
    ch = pulses(t, chirps, 0.25)
    wisp(cv, {"t": t, "gait": "walk", "s": s * 2.2, "tuft": 0.5 + 0.3 * ch, "beak_open": ch, "head_pitch": -0.3 * ch,
              "head_turn": 1}, L, cx - 30 - s * 2.2 * 0.36, ground, 0.36, 1)
    cv.restore()
    with F.layer(blur=6) as c2:
        cam.apply(c2, 1.3)
        Wd.fern(c2, 1700, 1180, 380, scl(lk["plant"], 0.25), t, seed=990, n_fronds=10)
        c2.restore()
    F.post = {"grade": "act2_gold", "bloom": (0.55, 0.7), "rays": (1560, 600, 0.7), "ray_thr": 0.55}


SHOTS = {"S09": S09, "S10": S10, "S11": S11, "S12": S12, "S13": S13, "S14": S14}
