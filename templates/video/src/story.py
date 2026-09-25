"""Facing East — single source of truth for timing.

Everything that depends on time (renderer, music, subtitles, script table,
QA checks) imports from here, so changing a line or a scene boundary here
keeps every deliverable in sync.
"""

FPS = 30
W, H = 1920, 1080

TITLE = "Facing East"
SUBTITLE = "The sunflower who stopped chasing the sun."
HOOK = "Next summer, find a sunflower field at dawn. Look east."

FADE = 0.7  # seconds of fade-in and of fade-out for every narration line

# (start_seconds, text). End times are derived from reading speed below.
_LINES = [
    # S1 — the secret turn (night)
    (3.0,   "Every night, when no one was watching, Hesper turned around."),
    (11.2,  "She did not know why."),
    # S2 — the chase (first day)
    (22.5,  "Hesper was born in a field of ten thousand flowers."),
    (30.0,  "From her first morning, she followed the Sun."),
    (38.0,  "East at dawn. South at noon. West at dusk."),
    (46.0,  "Every day, she turned to keep it in her eyes."),
    (54.0,  "Every evening, it left her anyway."),
    # S3 — the old ones
    (64.0,  "The old flowers did not follow anything."),
    (72.0,  "They stood heavy and still, their faces fixed on the east."),
    (81.0,  "Hesper thought they had given up."),
    (88.0,  "She promised herself she never would."),
    # S4 — summer, the bloom, the stiffening
    (99.0,  "All summer, she chased the light."),
    (106.0, "She grew tall. Her stem grew hard."),
    (115.0, "Then came the morning she bloomed."),
    (124.0, "And her body would not turn anymore."),
    # S5 — abandonment and the long night
    (139.0, "The Sun crossed the sky without her."),
    (147.0, "It set behind her, where she could not see."),
    (160.0, "In the dark, facing east, Hesper thought: so this is giving up."),
    # S6 — the revelation at dawn
    (180.0, "Then the east began to burn."),
    (188.0, "The Sun rose, and the first light in the world fell on her face."),
    (198.5, "The old ones had not given up."),
    (205.5, "They had learned where the light returns."),
    # S7 — resolution / moral
    (216.0, "Hesper never chased the Sun again."),
    (223.0, "Every dawn, it found her."),
    (230.0, "Not all stillness is surrender."),
    # S8 — the real-world anchor
    (240.0, "Young sunflowers really do track the sun, and turn back east each night."),
    (248.5, "Grown ones stop, and face east for good."),
    (255.0, "In a 2016 study, east-facing heads warmed faster and drew five times more pollinators."),
]


def line_duration(text: str) -> float:
    """Total on-screen time incl. fades.

    Fully-visible hold >= max(2.5 s, len/12 s), i.e. the slow end of the
    12–15 characters-per-second guideline, plus two fades.
    """
    hold = max(2.5, len(text) / 12.0)
    return round(hold + 2 * FADE, 2)


LINES = [(s, s + line_duration(t), t) for s, t in _LINES]

# Scene table: (id, start, end, name)
SCENES = [
    (1, 0.0,   22.0,  "The secret turn"),
    (2, 22.0,  62.0,  "The chase"),
    (3, 62.0,  97.0,  "The old ones"),
    (4, 97.0,  136.0, "The bloom"),
    (5, 136.0, 177.0, "The long night"),
    (6, 177.0, 214.0, "Where the light returns"),
    (7, 214.0, 238.0, "Every dawn"),
    (8, 238.0, 277.0, "Look east (facts + title card)"),
]

# Closing card timing (inside scene 8)
CARD_IN = 264.0
HOOK_IN = 268.0
FADE_OUT_START = 273.5
DURATION = 277.0  # 4:37


def check():
    problems = []
    prev_end = 0.0
    for s, e, t in LINES:
        if s < prev_end + 0.5:
            problems.append(f"overlap/too close: {t!r} starts {s} prev end {prev_end}")
        if e - s - 2 * FADE < 2.5:
            problems.append(f"too short: {t!r}")
        prev_end = e
    if not (20 <= len(LINES) <= 30):
        problems.append(f"line count {len(LINES)}")
    if DURATION >= 300:
        problems.append("duration >= 5:00")
    if not (210 <= DURATION <= 285):
        problems.append("duration outside 3:30–4:45")
    if prev_end > CARD_IN:
        problems.append("last narration overlaps title card")
    return problems


if __name__ == "__main__":
    for s, e, t in LINES:
        print(f"{s:7.2f} {e:7.2f} {e - s:5.2f}s {len(t):3d}ch  {t}")
    print("lines:", len(LINES), "duration:", DURATION)
    print("problems:", check() or "none")
