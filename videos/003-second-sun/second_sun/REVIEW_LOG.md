# SECOND SUN — Review log

## Pass 0: style frames (pre-animatic)

Style frames were rendered for S3, S16, S19, S21 and S24, and for every other shot, then inspected.

Fixes:
- Old Horn redesigned: a hand-drawn body outline in place of the tube, pillar legs with thigh masses, a lower frill, the V-notch, a broken horn, a cheek.
- Wisp redesigned: rounder, fluffier, with a fan tail of individual vanes and the one pale band.
- The rex redesigned: deep skull, massive thighs, horizontal tail. The first version read as a lizard.
- Edmontosaurus made bulkier.
- The bead shower went from uniform rain to a storm radiating from the south with fireballs.
- Detailed cataract eye for the S22 extreme close-up.
- S19 flash look re-balanced; it had washed out to flat white.
- Split Tree foliage clumps and a rim-lit trunk.
- S24 drain order corrected: sky first, foreground last.
- The ash mound rebuilt from her real silhouette.
- Fossils, brush and museum staging redesigned.
- Text cards given explicit line breaks.

## Pass 1: full animatic (quarter resolution, with mix), 309 frames at 1 fps

| Issue | Fix |
|---|---|
| S7/S17: Wisp stood in mid-air beside the knot-hole | Added a rim-lit bough stub under the hole; he lands and perches on it |
| S12/S13: the circling rex's tail crossed Old Horn's head (it read as interpenetration) | Rex pushed deeper (scale 0.62 → 0.5) and farther right |
| S17: the gift was unreadable (pebble a few px, Wisp hidden behind a foreground fern, too dark) | Camera push-in to the beak (z 1.75 → 3.0), pebble twice the size with a glint, foreground cleared, moonlight rim on Wisp |
| S5: her POV was a featureless blur, and the chirp rings weren't readable | Real scene defocused (26 px), Wisp's warm shape, four expanding warm rings on the chirp |
| Mix: S14/S15 nearly silent (−25 / −32 LUFS), limiter overshoot (TP +0.57 dBTP) | Added cello, strings and harp under S14–S15; true-peak (4× oversampled) look-ahead limiter; section-gain automation for the dynamic arc |
| Mix: sound-design top end harsh | 11 kHz low-pass on the SFX bus |

## Pass 2: final render (1080p24), technical QC

| Check | Result |
|---|---|
| Container / codecs | MP4, H.264 **High**, yuv420p, 1920×1080, 24/1 fps, CRF 16 (26.6 Mb/s), AAC-LC 48 kHz stereo at 320 kb/s nominal (288 kb/s average) ✔ |
| Duration | Video 309.000 s = audio 309.000 s = container **5:09.0** (window 4:50–5:10) ✔ |
| blackdetect | 0–8.2 s (the black cold open and card, then the slow fade-up into the star field), 17.0–17.2 (fade into S3), 261.0–261.2 (fade into S28), 291.0–291.25 (fade into the museum), 305.0–309 (the title card on near-black). All intentional ✔ |
| freezedetect (1.5 s) | None. No character is ever frozen; breathing, blinking, wind and particles run everywhere ✔ |
| Loudness (ebur128) | **−14.0 LUFS integrated, −1.3 dBTP true peak**, LRA 13.2 LU ✔ |
| Clipping | 0 samples ≥ 0 dBFS ✔ |
| True silence at the cut to white | 225.000–230.000 s is exactly 0.0 in the mix ✔ |
| A/V sync | All sounds are placed from `timeline.EV` / `DUET` / gait contact times, the same values that drive the picture. Spot-checked at the rex booms (102.4, 106.8), the rex steps, the seismic hit (191.8), the cut to white (225.0), the hand-take (298.0) and the end chirp and hum (307.6, 308.2) ✔ |
| THE LAKE match | S3, S15 and S24 come from one function with fixed geometry. Tree and Saddle edges coincide (1–6 px differences are wind sway only). The first S24 frame differs from S3 at 22 s by a mean of 3.2/255 (grain and animation) ✔ |
| Text cards | All five cards and the title were checked for spelling; each holds ≥ its words ÷ 2.2 s (read-twice rule) with 1.1 s fades ✔ |

## Pass 2: per-shot loudness (the dynamic arc)

The cold open is −25 LUFS. Act I sits around −15 to −13, and the POV drops back. The fern forest runs −17 to −18, the Hunter −14 and the standoff −10. The walk home is −13 and the dusk lock-off −15. Counting stars is −16, building to −11.5 for the gift. S18 is quiet at −26. The second sunrise is −14, carried by the pure tone, her breath and a choir bloom. The meteor shower peaks at −9.7. After the cut to white there is digital silence, then the ash at −23 to −24. The epilogue sits at −17 to −14.

## Scores (honest, final pass)

| Category | Score | Note |
|---|:-:|---|
| Story clarity | 9 | Every beat reads without words. Blindness is clear by S5, the rescue by S12, and the pebble lands by S17 |
| Emotional impact | 8 | The S19→S22→white→S24 run and the museum resolution work. It is limited by how much the simplified faces can act |
| Character animation | 7 | Zero foot sliding (distance-locked gaits), breathing, blinks, secondary tail and feather motion. But limbs are 2-bone IK tubes and there is no squash or skin sliding; poses are functional rather than virtuosic |
| Acting | 7 | Head tilts, the tuft, and the eye and body timing carry intent. There is no facial rig beyond eyes, lids and beak |
| Lighting and colour | 9 | The colour script is followed act by act, with rim light, god rays and per-act grades. Act IV is at 8% saturation |
| FX | 8 | Radiant bead storm, steam, fire, ash, water reflections and surge, fireflies, heat shimmer |
| Composition | 8 | The lock-off and the Saddle thread work. Some mid shots are functional |
| Music | 8 | Leitmotifs are clear (Together, the fifth, the chirp, the G♯ Star), cut to picture, and the D-major resolution lands on the hand-take. It is synthesised, not sampled, so it is warm but not a real orchestra |
| Sound design | 8 | Frame-locked, mass-scaled footfalls, a felt infrasonic boom, true silences |
| Mix | 9 | On target, real dynamic range, quiet moments truly quiet |
| Technical polish | 9 | Specs, loudness, no banding, no clipping |

## Harsh juror pass: the five weakest moments

These remain after the fixes above.

1. **Character anatomy up close** (S4, S19d, S22). Old Horn reads as a stylised cut-paper puppet, not a sculpted creature.
2. **Wisp's locomotion.** The run cycle is a 2-leg IK loop with a body bob. It reads as a small theropod running, but without the bird-like head-stabilisation.
3. **S27 deep time.** The strata fill and the erosion read clearly but diagrammatically.
4. **S28 fossils.** The skull design is readable (the broken horn, the small skeleton, the crescent) but graphic rather than naturalistic.
5. **The herd in the lock-off** is small and simple in silhouette. It is animated (drinking, alarm, flight) but crowd variety is limited.

## Final statement

The loop stopped here. The brief asks for 9+ in every category and a juror pass with nothing left to improve, and that bar is **not** met in character animation, acting, emotional impact, FX, composition, music or sound design (7–8).

The remaining gap is the craft ceiling of the chosen code-only 2D pipeline in this environment. The alternative, sculpted and rigged 3D creatures, was measured in the bake-off at 18–28 h of CPU render time with no denoiser, before any sculpting or rigging. Further gains would need a GPU renderer or hand-painted and sculpted character assets. Every issue the review could fix within this pipeline has been fixed.
