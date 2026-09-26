# SECOND SUN — Production notes

**Fox & Folly #003** · 5:09 · 1920×1080 · 24 fps · wordless · original score
**Title card subtitle (chosen):** *the last day of the Cretaceous*

---

## 1. Pipeline: bake-off and decision

Full numbers and frames are in `source/bakeoff/RESULTS.md`.

| | A: Blender 4.0 headless | **B: 2.5D Skia + NumPy (chosen)** |
|---|---|---|
| S19 test frame | 13.5 s at 960×540, 64 spp Cycles, noisy (the distro build has no OIDN) | 1–2.5 s at 1920×1080 |
| Whole film (≈7,400 frames, 4 CPU cores) | ≈18–28 h, with no headless GPU | ≈1 h |
| Look | clay-toy skin-modifier forms; organic dinosaurs would need sculpting, retopology and rig work far past schedule | rim-lit sculpted silhouettes and painterly atmosphere, as the visual bible asks |
| Animation | armature rigs, slow to iterate | parametric poses, 2-bone IK, **distance-parameterised gaits (zero foot sliding by construction)** |

B's speed paid for more review iterations, and those are worth more to the finished film than raw 3D.

## 2. Look: "lantern luminism" as built

- **Characters** are unions of smooth shapes (Catmull-Rom outlines, tapered IK limbs) filled with albedo × shot ambient. Each gets a key-side gradient, belly occlusion, faint procedural skin, and a **blurred-offset rim light** on the light side, so every creature reads in backlight.
- **Silhouettes** are distinct: Old Horn (the broken left brow horn, the V-notch in the frill, dusty rose and bone frill, milky eye), Wisp (big amber eye, springing tuft, fan tail with one pale band), the rex (deep skull, massive thighs, horizontal tail), Edmontosaurus (the fleshy comb), and the Burrower (whiskers).
- **Depth** has 5–7 layers per setup with parallax: sky → star/sun → ridge with the Saddle → hills and treeline → water with real reflections → characters → blurred foreground plants (depth of field).
- **Post** per frame: screen-space god rays, multi-scale bloom, heat shimmer (S21), POV defocus, a per-act grade (the Act IV grade runs at 8% saturation), a vignette, camera shake only in S12/S20–S22, film grain, and a triangular dither (no banding). Everything renders on float16 surfaces.
- **Plants:** there is no grass. Ground cover is ferns (animated rachis and pinnae), horsetails (whorled nodes), magnolia shrubs with cupped flowers, conifers and palms, all swaying on one shared wind field.

## 3. Continuity devices

- **THE LAKE lock-off** is one function, `shotkit.lake()`, with fixed geometry (`LAKE` constants). S3, S15, S18, S19a, S20, S21 and S24 all call it, so the camera is identical **by construction**. S24 renders the S3 dawn world live (still moving) and the ash world, then dissolves between them through a noise-driven drain field. Life drains region by region, sky first and foreground last, with an ash-grey front.
- **The Saddle** is built into `ridge_path()` as two shoulders and a deep notch. It appears in S3, S8, S15, S16–S19, S24, S27 (it persists through deep time), S28 and S29.
- **The star's escalation** is keyed in `timeline.STAR_KEYS`: 0.10 (S2, a tremble) → 0.18 (S8, a faint daytime dot plus a faint G♯6) → 0.45 (S15, brighter than any planet, with haze and spikes) → 0.62–0.80 (S16/S17, casting faint shadows) → S19, the second sun.
- **The pebble** appears in S7 (found, offered, pushed back, stored), S17 (retrieved, given, kept), S22 (between them) and S28/S30 (between the tiny claws).

## 4. Director's choices (autonomous; the brief said not to ask)

1. **Runtime 5:09.** The shot timings follow the brief to within ±1 s through S26. The epilogue is stretched by about 9 s (within the brief's ±10 s tolerance and the 4:50–5:10 window) so every end card can be read twice (≥ words ÷ 2.2 s, checked by `timeline.check()`).
2. **Subtitle:** *the last day of the Cretaceous*. It is plain, factual and quietly devastating, and it lets the title carry the poetry.
3. **Wordless acting beats.** Blindness is established in S4 (clouded eyes), S5 (head tilted to listen, and a POV where his chirp is a ring of warm light) and S12 (POV where the rex exists only as dark rings). The meaning of the pebble is set up in S7 (she pushes it back: *it's yours*) and paid off in S17 (she keeps it).
4. **S19 POV:** the only frame in the film where real light floods her view. The music drops to a pure G♯5 and her breathing.
5. **The cut to white at 3:45 is digital silence.** 225.0–230.0 s is exactly zero in the mix (verified), then the ash wind begins.
6. **The mound (S24/S25)** is her actual lying silhouette and his curl, drawn through a grey colour filter and softened like ash. This makes the "unmistakably a sleeping Triceratops" read literal.
7. **The museum (S30):** the grandmother is tall with a slight stoop, and the child reaches up (a mirror of Wisp and Old Horn). The music resolves to **D major on the hand-take (4:58)**.
8. **Final sound:** his chirp note (A5, celesta) answered by her hum note (D3, cello), at 5:07.6 and 5:08.2.

## 5. Science grounding (what is real, what is licence)

- **Tanis / Hell Creek (North Dakota), about 3,000 km from Chicxulub.** Impact spherules (glass beads) fell within minutes to hours, seismic waves drove surges of water, and ejecta ignited fires. This is DePalma et al., 2019, *PNAS* 116(17):8190. Act III follows this order: flash → shaking and surge → bead shower → furnace sky and fires.
- **The new "star" in the days before** is artistic licence, as the brief states.
- ***Pectinodon*** is a troodontid from Hell Creek/Lance. Large eyes and inferred low-light vision in troodontids fit Wisp's love of stars.
- **Closed-mouth vocalisation** (booming rather than roaring) follows Riede et al., 2016, *Evolution* 70(8). Old Horn hums and the rex booms at about 18–35 Hz.
- ***Edmontosaurus* fleshy comb:** Bell et al., 2014, *Current Biology* 24(1).
- **No grass ground cover** (ferns, horsetails, flowering shrubs, conifers, palms, magnolias), per the brief.
- ***Purgatorius*** was an early primate-like mammal of the latest Cretaceous and early Paleocene. The Burrower survives.

## 6. Tempo map and sync

- The M4 duet runs at 72 bpm from 146.4 s (`timeline.DUET`). Chirps land on the beat and hums on the off-beat. Picture (star twinkles, beak and throat pulses) and sound read the same list.
- Old Horn's footfalls are computed from `OH_GAIT.contacts()` along the same distance curve that plants her feet on screen, so each thud lands on a touchdown frame. The rex's steps and booms and the seismic hit are listed in `timeline.EV`.
- Every other picture event with a sound (pebble drop, knot-hole click, chirps, squeaks, brush strokes, bead streaks) comes from `timeline.EV`.

## 7. Open issues and limitations (honest)

See `REVIEW_LOG.md` §Final for what remains after the review loop.
