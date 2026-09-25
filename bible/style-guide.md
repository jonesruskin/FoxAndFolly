# Fox & Folly — Style Guide

## Look
- **Cinematic and painterly.** Deep blacks, glowing light, drifting particles, slow camera moves.
- Layered parallax (at least 5 depth layers), soft bloom, volumetric light (screen-space god rays),
  low mist or haze, subtle film grain, a gentle vignette, and a faint paper texture.
- Grade: lifted blacks toward blue (`lift ≈ 0.010 / 0.013 / 0.024`), warm highlights,
  hue-preserving highlight roll-off (never clip to lemon or white).
- Motion: every value is keyframed with easing (`shared/foxfolly/anim.Track`). No linear moves.
  Prefer continuous worlds where *light* motivates the transitions (time-lapse, flares, dawns)
  over hard cuts.
- Characters without faces are expressive through **motion, light, colour and rhythm**:
  turning, drooping, straining, glowing, dimming.

## Typography
- Narration: **Cormorant Garamond Italic**, 56 px at 1080p, warm ivory `#F5EBD9`,
  wide soft dark shadow plus a faint gold glow, centred at y ≈ 952 (inside the 90% title-safe area).
- 0.7 s fade in and out with a 6 px upward drift on entry. A soft darkening band behind the text
  whenever a line is up.
- Title card: Cormorant Garamond Medium Italic 150 px; subtitle Italic 50 px; hook line Regular
  38 px (gold, slight tracking); channel mark Medium 30 px, tracked, low opacity.
- Fonts live in `shared/fonts/` (SIL OFL 1.1).

## Sound
- Cinematic ambient: additive pads, celesta or soft-piano bells, string swells, a low drone,
  noise textures (wind, sparkles), and a long convolution reverb.
- Leitmotifs per character. The music follows the script's cues, with swells landing on visual beats.
- Master: −14 LUFS integrated, ≤ −1 dBTP true peak, 48 kHz stereo, fades in and out.
- All audio is synthesised in code. No samples, so nothing for Content ID to match.

## Technical
1920×1080 · 30 fps · H.264 High · yuv420p · ≥ 12 Mbps (we use 18 Mbps ABR, `-tune grain`) ·
AAC 320 kbps · `+faststart`.
