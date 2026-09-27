"""SECOND SUN — single source of truth for timing (24 fps).

Shot boundaries follow the brief; the epilogue is stretched by ~9 s so every
end card can be read twice (brief allows ±10 s and a 4:50–5:10 runtime).
Every picture event that makes a sound is listed here (or computed from the
rigs, e.g. footsteps), so animation, sound design and score stay frame-locked.
"""

FPS = 24
W, H = 1920, 1080
TITLE = "SECOND SUN"
SUBTITLE = "the last day of the Cretaceous"

# (id, start, end, name)
SHOTS = [
    ("S01", 0.0, 7.0, "Black · Hell Creek card"),
    ("S02", 7.0, 17.0, "Night sky · the warm star"),
    ("S03", 17.0, 28.0, "THE LAKE · dawn"),
    ("S04", 28.0, 37.0, "Wisp wakes in the frill"),
    ("S05", 37.0, 49.0, "Morning walk · Old Horn's POV"),
    ("S06", 49.0, 59.0, "The Burrower"),
    ("S07", 59.0, 72.0, "The crescent pebble"),
    ("S08", 72.0, 83.0, "Hatchlings · between her horns"),
    ("S09", 83.0, 90.0, "Midday · she lies down"),
    ("S10", 90.0, 101.0, "The dragonfly · the trembling print"),
    ("S11", 101.0, 110.0, "The Hunter"),
    ("S12", 110.0, 123.0, "The standoff"),
    ("S13", 123.0, 130.0, "The rex leaves"),
    ("S14", 130.0, 136.0, "Walking home"),
    ("S15", 136.0, 145.0, "THE LAKE · dusk"),
    ("S16", 145.0, 160.0, "Counting stars"),
    ("S17", 160.0, 173.0, "The gift"),
    ("S18", 173.0, 180.0, "Silence"),
    ("S19", 180.0, 191.0, "THE HEART SHOT · second sunrise"),
    ("S20", 191.0, 199.0, "The ground heaves"),
    ("S21", 199.0, 215.0, "The meteor shower"),
    ("S22", 215.0, 225.0, "Together · cut to white"),
    ("S23", 225.0, 230.0, "White to grey · ash"),
    ("S24", 230.0, 242.0, "THE LAKE · after"),
    ("S25", 242.0, 248.0, "The mound"),
    ("S26", 248.0, 254.0, "The Burrower lives"),
    ("S27", 254.0, 261.0, "Deep time"),
    ("S28", 261.0, 272.0, "Found together"),
    ("S29", 272.0, 291.0, "Badlands · evening star"),
    ("S30", 291.0, 305.0, "The museum"),
    ("S31", 305.0, 309.0, "Title"),
]
DURATION = 309.0

# On-screen text cards: (start, end, text, style)
CARDS = [
    (0.9, 6.2, "Hell Creek  ·  66 million years ago", "small"),
    (266.2, 271.4, "They were found together.", "card"),
    (273.6, 282.2, "The stone that ended their world did not choose them.\nIt did not know their names.", "card"),
    (282.8, 290.6, "The universe sends no warnings.\nNot to stars. Not to species. Not to us.", "card"),
    (292.4, 304.6, "Nothing is promised beyond this breath.\nSo stay a little longer by the water.\nHold the ones you love while the light is still soft.", "card"),
    (305.4, 308.6, "SECOND SUN", "title"),
]
CARD_FADE = 1.1

# Narration captions (added after the owner's review: the film must be followable
# from the start). (start, text); end = start + read time, see caption_dur().
_NARRATION = [
    (8.8, "Some nights, one star burns warmer than the rest."),
    (18.6, "The last morning of the Cretaceous began like any other."),
    (23.6, "The lake. The herd. The mist. A world overflowing with life."),
    (29.0, "Wisp always slept in the curve of Old Horn's frill."),
    (34.6, "She was very old. And she was almost blind."),
    (40.2, "She found her way by his voice. Every chirp was a small light in her dark."),
    (45.6, "Where she drank, he drank."),
    (50.2, "The Burrower: a small furry mammal, and Wisp's oldest rival."),
    (56.0, "It always got away."),
    (59.8, "In the shallows, a white pebble caught the light."),
    (64.4, "He offered it to her. She nudged it back: it is yours."),
    (69.4, "His best treasure went into the old tree."),
    (73.0, "A mother Edmontosaurus with her hatchlings."),
    (77.0, "Wisp had no mother. He had Old Horn."),
    (80.1, "In the daylight sky, a pale new star. No one noticed."),
    (84.5, "The midday heat was hard on old bones."),
    (90.4, "A dragonfly led him deeper into the ferns than he had ever gone."),
    (97.5, "Then the forest went silent."),
    (101.8, "A young Tyrannosaurus. Patient. Hungry."),
    (107.2, "Wisp called for help."),
    (110.8, "Old Horn could not see the hunter. She came anyway."),
    (116.0, "She tracked it by sound alone, turning her broken horn to every step."),
    (123.3, "The hunter chose easier prey."),
    (126.8, "Her old legs gave way. He did not leave her side."),
    (130.8, "They walked home together, as close as shadows."),
    (137.0, "At dusk, the new star hung over the Saddle, brighter than any planet."),
    (145.2, "Every night, they counted stars. He chirped. She hummed."),
    (153.7, "Then he found the new star, and remembered: she could not see it."),
    (160.1, "So he brought her his best treasure."),
    (164.9, "This time, she kept it."),
    (168.8, "They slept beneath the burning star."),
    (173.8, "Before dawn, the world went silent. Every head turned south."),
    (181.0, "A second sun rose, in the wrong part of the sky."),
    (185.8, "And for the first time in years, Old Horn saw light."),
    (191.9, "Then the ground heaved, and the lake rose."),
    (199.6, "The sky rained glass: rock melted by an asteroid impact"),
    (203.9, "three thousand kilometres to the south."),
    (208.6, "Wisp could have hidden. He ran back to her."),
    (215.2, "She sheltered him beneath her great head."),
    (219.1, "One chirp. One hum."),
    (233.5, "Afterwards, nothing moved but the ash."),
    (242.6, "Where they lay, the ash lay deepest."),
    (248.6, "But something small had survived."),
    (254.6, "Sixty-six million years of stone buried them."),
    (261.4, "Montana. Today."),
]


def caption_dur(text):
    return round(max(2.4, len(text) / 15.0) + 0.9, 2)


def _build_narration():
    out = []
    for i, (a, t) in enumerate(_NARRATION):
        b = a + caption_dur(t)
        if i + 1 < len(_NARRATION):
            b = min(b, _NARRATION[i + 1][0] - 0.25)
        out.append((a, round(b, 2), t))
    return out


NARRATION = _build_narration()
CAPTION_FADE = 0.5

# Star brightness (0..1 visual scale) — its escalation must be trackable.
STAR_KEYS = [(7, 0.10), (17, 0.12), (72, 0.18), (136, 0.45), (145, 0.62), (160, 0.75),
             (173, 0.80), (180, 0.85)]

# Tempo map ------------------------------------------------------------
# M4 "Counting Stars" duet: the score is written around these exact beats.
DUET_BPM = 72.0
DUET_T0 = 146.4           # first chirp
DUET_BEAT = 60.0 / DUET_BPM
# chirp on the beat, hum on the next beat; four pairs (two beats apart)
DUET = [(DUET_T0 + 2 * k * DUET_BEAT, DUET_T0 + (2 * k + 1) * DUET_BEAT) for k in range(4)]
NEW_STAR_TRILL = 153.6

# Key sync events (seconds) shared by picture and sound
EV = {
    "star_tone": 9.0,
    "sun_crest": 23.5,
    "wisp_wake_tuft": 31.2,
    "wisp_yawn": 32.0,
    "chirp_s5": [38.2, 41.6, 44.8],
    "pounce": 51.6,
    "burrow_dive": 54.4,
    "indignant": [56.3, 56.8],
    "pebble_glint": 60.6,
    "pebble_drop": 64.6,
    "pebble_nudge": 66.6,
    "knot_store": 70.0,
    "hum_s8": 81.3,
    "lie_down": 86.2,
    "dragonfly_catch": 96.4,
    "silence_s10": 97.3,
    "rex_boom": [102.4, 106.8],
    "broken_call": 107.9,
    "crash": 111.2,
    "rex_steps": [113.4, 114.6, 115.8, 117.0, 118.2, 119.4, 120.6],
    "rex_leave": 124.2,
    "buckle": 126.3,
    "hum_shaky": 127.6,
    "trill": NEW_STAR_TRILL,
    "pebble_give": 164.8,
    "hum_gift": 166.2,
    "flash": 181.2,
    "seismic": 191.8,
    "beads_start": 199.4,
    "burrow_hesitate": 207.0,
    "turn_back": 208.4,
    "final_hum": 219.2,
    "final_chirp": 220.8,
    "final_hum2": 221.6,
    "white": 225.0,
    "life_note": 250.2,
    "brush": [264.6, 266.0, 267.4, 268.8],
    "hand_take": 298.0,
    "end_chirp": 307.6,
    "end_hum": 308.2,
}


def shot_at(t):
    for sid, s, e, name in SHOTS:
        if s <= t < e:
            return sid, t - s, e - s
    return SHOTS[-1][0], t - SHOTS[-1][1], SHOTS[-1][2] - SHOTS[-1][1]


def check():
    probs = []
    for (a, b) in zip(SHOTS, SHOTS[1:]):
        if abs(a[2] - b[1]) > 1e-6:
            probs.append(f"gap {a[0]}->{b[0]}")
    if not (290 <= DURATION <= 310):
        probs.append("runtime outside 4:50–5:10")
    for s, e, txt, st in CARDS:
        words = len(txt.split())
        need = max(3.0, words / 2.2)          # time to read it twice
        if e - s < need and st == "card":
            probs.append(f"card too short: {txt[:30]}")
    prev = 0.0
    for a, b, t in NARRATION:
        if a < prev + 0.2:
            probs.append(f"caption overlap: {t[:30]}")
        if b - a < max(2.0, len(t) / 17.0 + 0.6):
            probs.append(f"caption too short to read: {t[:30]} ({b - a:.2f}s)")
        prev = b
        for ca, cb, ct, cs in CARDS:
            if cs == "card" and a < cb and b > ca:
                probs.append(f"caption over card: {t[:30]}")
    return probs


if __name__ == "__main__":
    for sid, s, e, n in SHOTS:
        print(f"{sid} {s:6.1f}-{e:6.1f} {n}")
    print("duet:", [(round(a, 2), round(b, 2)) for a, b in DUET], "trill", round(NEW_STAR_TRILL, 2))
    print("problems:", check() or "none")
