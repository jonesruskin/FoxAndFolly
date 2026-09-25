# Production notes — *Facing East* (Fox & Folly #002)

## 1. Concept brainstorm

Scores run 1–10. **Fit** means fit with the channel: fable form, emotional maturity, a real-science anchor, and suitability for the glowing, atmospheric look.

| # | Concept | Logline | Real anchor | Orig. | Emotion | Visuals | Fit | **Total** |
|---|---------|---------|-------------|:-:|:-:|:-:|:-:|:-:|
| 1 | **Facing East** | A young sunflower chases the sun and pities the old flowers frozen facing east, until she blooms, can't turn, and the dawn finds her. | Heliotropism; mature heads face east and get ~5× pollinator visits (Atamian 2016) | 8 | 9 | 9 | 9 | **35** |
| 2 | The Strip-Bark Pine | An ancient bristlecone survives five millennia by letting whole limbs die while the lush young trees below fall in storms. | Strip-bark growth; Methuselah (~4,800 yrs), location kept secret | 8 | 8 | 7 | 9 | 32 |
| 3 | The Eel Who Went Home | An eel crosses an ocean toward a birthplace no one has ever witnessed. | European eels spawn in the Sargasso Sea; spawning never directly observed | 8 | 7 | 6 | 8 | 29 |
| 4 | The Pearl's Confession | An oyster hides a wound and turns it into the most beautiful thing in the sea. | Natural pearls rarely form around sand, usually around a parasite or tissue intrusion | 7 | 7 | 8 | 7 | 29 |
| 5 | The Firefly Out of Time | One firefly can't keep the rhythm of the swarm, until the swarm finds it. | Synchronous fireflies (*Photinus carolinus*) | 6 | 7 | 9 | 6 | 28 |
| 6 | The Stone the Ice Forgot | A boulder carried 500 km by a glacier is left behind when the ice melts away. | Glacial erratics (Okotoks "Big Rock", ~16,500 t) | 7 | 7 | 6 | 7 | 27 |

**Why #1 won.** It has the strongest *reversal*: the image that reads as surrender in Act 1 (old flowers frozen facing east) becomes the image of wisdom in Act 3, and the science is what makes that reversal true. It also speaks to teens and adults: youthful striving, the fear of growing older and slowing down, and learning that patience isn't defeat. Visually it keeps the channel's glow-in-the-dark palette (night field, stars, fireflies, dawn light) while being clearly *not* space and *not* a love story. Firefly (#5) scored lower on fit because "communicating in light" would echo episode 001 too closely.

## 2. Story decisions and self-review

- **Hook:** "Every night, when no one was watching, Hesper turned around." It's a mystery (why?) that the fact section finally answers (young sunflowers really do reset east each night).
- **Name:** *Hesper* = Hesperus, the evening star, the West. A flower named for the west who learns to face east. It's saved for the pinned comment.
- **The twist is earned twice:** emotionally (the old ones were right) and factually (east-facing heads warm first and draw more pollinators).
- **The moral is stated once,** as the last story line: *Not all stillness is surrender.* The fact lines that follow ground it without preaching.
- **Northern-hemisphere assumption:** "South at noon" is correct for mid-northern latitudes, where most sunflowers are grown.
- **Pronoun for the Sun:** "it", deliberately. The Sun is a force, not a love interest (avoiding a repeat of 001).
- **Pacing:** 28 lines over 4:37. Every hold is ≥ max(2.5 s, chars ÷ 12 s), enforced by `story.check()`. The longest line (86 characters) is held 7.2 s fully visible, 8.6 s in total.
- **Revision history.**
  - v1 fact line: "they get five times more visits from bees." Rejected as imprecise: the study compared east- against west-facing heads and counted *pollinators*.
  - v2: "…five times more pollinators than west-facing ones." While verifying it I found a 2024 study in commercial plantations that reports visits independent of head orientation.
  - v3 (final) attributes the claim to its study: "In a 2016 study, east-facing heads warmed faster and drew five times more pollinators." It's accurate and still lands the point.
- Self-review table: see the end of `script.md`. All items pass.

## 3. Fact sources

| Claim (as shown on screen) | Source | Status |
|---|---|---|
| Young sunflowers track the sun and turn back east each night | Atamian, H. S., Creux, N. M., Brown, E. A., Garner, A. G., Blackman, B. K., & Harmer, S. L. (2016). *Circadian regulation of sunflower heliotropism, floral orientation, and pollinator visits.* **Science 353**(6299), 587–590. doi:[10.1126/science.aaf9793](https://www.science.org/doi/10.1126/science.aaf9793) | ✔ Core finding: daytime east→west tracking, nightly reorientation east, clock-regulated |
| Grown ones stop, and face east for good | Same paper: tracking ceases at maturity (anthesis) and most heads face east | ✔ |
| In a 2016 study, east-facing heads warmed faster and drew five times more pollinators | Same paper: east-facing heads warm faster in the morning, with a fivefold increase in pollinator visits vs west-facing heads (confirmed via the abstract and indexed summaries while producing) | ✔ Attributed to the study on screen |
| (Counterpoint, not shown) | Horváth et al. (2024). *The all-day pollinator visits of sunflower inflorescences in Helianthus annuus plantations are independent of head orientation: testing a widespread hypothesis.* **The Plant Journal.** doi:10.1111/tpj.17070 | Reason the fact line is attributed rather than stated as universal |
| Golden-angle floret arrangement (hidden detail) | Vogel, H. (1979). *A better way to construct the sunflower head.* **Mathematical Biosciences 44**, 179–189. Floret *k* at radius ∝ √k and angle k × 137.508°. | ✔ Implemented literally in `flora.make_disc_image` |
| Hesper = Hesperus, the evening star / the West | Greek *Hesperos*, "evening; western" | ✔ |

Only the abstract and indexed summaries were reachable from the production environment; the full texts were not. Please spot-check the two DOIs above before publishing.

## 4. Tools and why

| Need | Choice | Reason |
|---|---|---|
| Frame rendering | **Python + skia-python** (Skia CPU raster, float16 surfaces) + **NumPy/OpenCV** post | Skia gives anti-aliased vector paths, gradients, blend modes, blur filters and high-quality text, drawn directly in a 3D-projected head's local coordinates. Float16 surfaces avoid banding in the dark night skies. NumPy/OpenCV handle bloom, god rays, grading and grain quickly. Deterministic and headless, with no GPU needed. Chosen over Remotion/Chromium, which would need a headless GPU/WebGL path and slower per-frame screenshots in this container. |
| Encoding | **FFmpeg / libx264**, `preset slow`, `profile high`, `yuv420p`, 18 Mbps ABR (max 28), `-tune grain`, BT.709 tags, `+faststart` | Meets the ≥ 12 Mbps target with headroom for film grain, which survives YouTube's re-encode better at high bitrate. |
| Parallelism | `multiprocessing` fork pool (4 workers) → ordered raw RGB pipe → ffmpeg | About 0.9 s per frame per core; the full film renders in about 60 min. |
| Music | **NumPy/SciPy additive synthesis** + synthetic convolution reverb + custom look-ahead limiter; loudness via **pyloudnorm** (ITU-R BS.1770) and FFmpeg `ebur128` | No samples or soundfonts at all, so there's zero licensing or Content ID risk. Full control over sync (60 BPM = 1 beat per second of timeline). |
| Font | **Cormorant Garamond** (Italic, Medium Italic, Regular, Medium), from Google Fonts | SIL Open Font License 1.1; the license is in `shared/fonts/OFL.txt`. |
| Everything else | No external images, footage, audio or data | Every pixel and sample is generated by `src/`. |

**Environment notes.** ffmpeg, git-lfs and libEGL were installed with apt; skia-python, opencv-python-headless, pyloudnorm, numpy, scipy and fonttools with pip. GitHub raw downloads were blocked, so the fonts were fetched from fonts.gstatic.com (the same OFL files Google Fonts serves). The OFL text was written from the canonical license, with the copyright line read from the font's own `name` table.

## 5. Visual design decisions

- **One continuous world instead of cuts.** The film is a single sunflower field whose clock (time of day), camera and characters are keyframed. Transitions are motivated by light: time-lapse nights, dawns, and the sunrise flare that carries us into the macro shot. The only "cut" is hidden inside a warm flare at 3:58.
- **The field is the twist.** Hundreds of background flowers are pre-rendered facing east, with a separate "face" layer that is added in proportion to how directly the sun hits east-facing faces. At dawn the whole field ignites face-first. In the afternoon (Scene 3) the same faces sit in shadow with their backs to the sun.
- **Hesper is the only flower that moves.** Her yaw follows the sun's azimuth by day and swings back east by night until 2:01. After that it's locked, with two visible straining attempts (2:05, 2:09).
- **Depth:** sky → stars/moon/sun → 2 hill ridges → far field → mist → mid field → 5 old ones (depth 0.62–0.84) → Hesper → blurred foreground foliage (depth 1.45). Parallax comes from per-layer zoom and pan.
- **Look:** screen-space god rays when the sun is low, multi-scale bloom, a hue-preserving highlight shoulder (fixes the lemon-yellow petal clipping seen in early tests), lifted blue blacks, warm highlights, vignette, paper texture, per-frame film grain, and triangular dither.

### Style-frame review log (every issue found and fixed before the final render)

| Frame(s) | Problem found | Fix |
|---|---|---|
| All, v1 | Hesper indistinguishable from the old flowers | Re-staged: Hesper moved to the foreground (base below frame, height 820→995 px, head radius 92→178). Old ones pushed back to depth 0.62–0.84. |
| 0:08, 0:20 | Rotated star layer showed its rectangular edge | Pole of rotation moved so the star texture always covers the frame |
| 0:44, 1:15 | Noon sky blown out to white; petals clipping to lemon | Smaller sun glow; lower daytime ambient light; hue-preserving tone curve |
| 1:15 | Old ones' faces lit although the sun was behind them | Scene 3 moved to afternoon (sun in the west); face lighting driven by the sun–face angle |
| Night | Silhouettes unreadable | Brighter night horizon and ambient, a crescent moon, and a moonlit boost on Hesper only (a clear focal point) |
| 3:08–3:14 | Sunrise sun off-screen at the key reveal | Sun path remapped so the rising sun sits inside the frame on the left, just above the hills |
| 3:58 | Cross-fade to the macro left a ghosted double exposure | Replaced with a light-based transition: the dawn swells into a warm flare that hides the switch |
| 4:00+ | Macro petals flat and neon | Petals shaded root→tip, amber palette, darker key light, depth-of-field blur toward the edges |
| 1:57 | Bloom halo drawn in the tilted face plane, reading as a foggy sheath | Halo moved to screen space, behind the head |
| 4:15 | Two-line fact wrapped with an orphan word | Balanced line-breaking in `shared/foxfolly/text.py` |
| 2:05 | Strain attempts too subtle | Amplitude raised from 9° to 14° |

## 6. Music

- **Form:** follows the script's cues scene by scene (see the Music column of the scene table). 60 BPM, so cues are placed in seconds straight from the timeline.
- **Leitmotifs:** SUN (rising D–E–F♯–A) lands on the sunrise at 0:26, the promise at 1:28, the bloom at 1:55 and the dawn at 3:06. NIGHT (falling A–F♯–E–D) plays for the secret turn (0:03), dusk (0:55) and "would not turn anymore" (2:04).
- **Instruments (all synthesised):** detuned additive pads, celesta-like bells with inharmonic partials, a four-voice detuned string ensemble with vibrato, a D/A drone, wind (band-passed noise, two decorrelated channels), star sparkles, and soft sub-and-whoosh swells into the two peaks. A 4.5 s synthetic stereo hall reverb darkens over its tail.
- **Mastering:** high-pass at 45 Hz and gentle low-pass at 10 kHz (no harshness), 2.5 s fade-in and 6 s fade-out, integrated loudness normalised to −14 LUFS, and a smoothed look-ahead limiter at −1.5 dBFS.
- **Verification:** results are in the checklist below. An earlier limiter switched gain too abruptly and showed as broadband vertical lines in the spectrogram at the peaks. It was rebuilt with smoothed attack and release, and the lines are gone. The per-section loudness matches the intended arc (quiet opening → build → bloom peak → quietest point under "so this is giving up" → largest peak at dawn → warm resolution → quiet card).
- ⚠️ **Please listen to the final track yourself** (on headphones and speakers). All verification here is analytical (loudness, peaks, spectrogram, waveform, section loudness); I can't hear the audio.

## 7. Deliverables and repository decisions

- The deliverables are in `output/`. Media files (`.mp4`, `.wav`, output `.png`) are tracked by **Git LFS** via the root `.gitattributes`.
- Source isn't duplicated into `output/`. It lives next to it (`../build.py`, `../src/`, plus the shared toolkit in `/shared/foxfolly`), and `python build.py` regenerates everything in `output/`. `output/README.md` points to it.
- Intermediates (`build/`: raw video, stills, QA frames) are git-ignored.

## 8. Final quality checklist

*(Filled in after the final render and review; see below.)*
