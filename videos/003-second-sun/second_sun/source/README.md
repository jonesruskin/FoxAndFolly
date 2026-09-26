# SECOND SUN — source

Rebuild the whole film (score → sound → mix → 31 shots → assemble → deliver):

```bash
cd videos/003-second-sun/second_sun/source
make film            # or: python build.py
```

About 1 h on 4 CPU cores. Useful partial commands:

```bash
python build.py --shots S19 S22     # re-render single shots, re-assemble, re-deliver
python build.py --audio-only        # rebuild score/SFX/mix, re-mux onto the existing picture
python build.py --qc                # ffprobe / blackdetect / freezedetect / ebur128 report
python render.py stills 182.4 219.8 # style frames -> ../build/stills/
make animatic                       # quarter-res full timeline with the mix
```

| File | Role |
|---|---|
| `timeline.py` | Single source of truth: shots, cards, star escalation, duet tempo map, all sync events |
| `rig.py` | 2D rigging: Catmull-Rom forms, 2-bone IK, distance-locked gaits, rim-lit "lantern luminism" rendering |
| `creatures.py` | Old Horn, Wisp, the Burrower, Edmontosaurus, the rex, azhdarchid, the pebble |
| `world.py` | Looks (colour script), sky, the star, ridge with the Saddle, plants, water, particles, beads, fire, ash |
| `shotkit.py` | Shared set-ups: THE LAKE lock-off, the camp, the shore, the fern forest, POV rings, 2.5D camera |
| `shots_*.py` | The 31 shots, one function each |
| `frame.py` | Float16 canvas, DOF layers, post stack and per-act grades |
| `instruments.py`, `music.py` | Synthesised instruments and the score (leitmotifs, cues M1–M7) |
| `sfx.py`, `mix.py` | Sound design (frame-locked) and the mix/master to −14 LUFS / ≤ −1 dBTP |
| `bakeoff/` | Pipeline bake-off (Blender vs 2.5D) with frames and results |
