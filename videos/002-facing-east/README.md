# 002 — Facing East

*The sunflower who stopped chasing the sun.* · 4:37 · 1920×1080 · 30 fps

## Rebuild everything with one command

```bash
cd videos/002-facing-east
python build.py          # music → frames → mux → subtitles → thumbnail → output/
python build.py --qa     # the same, plus automated QA (frames every 2 s, loudness, black/freeze scan)
```

A full render takes about 60 minutes on 4 CPU cores. Useful partial commands:

```bash
python src/render.py stills 27 118 190     # style frames at given seconds → build/stills/
python src/render.py video --start 180 --end 200 --out build/preview.mp4
python src/music.py                        # score only → build/music.wav
python src/story.py                        # print and validate the narration timeline
```

## Source map

| File | Role |
|---|---|
| `src/story.py` | **Single source of truth**: narration lines, timings, scenes, title card. Everything else reads it. |
| `src/flora.py` | Procedural sunflowers (3D-projected heads, golden-angle florets, petals, stems, leaves). |
| `src/render.py` | The world: time-of-day sky model, stars, moon, hills, pre-rendered field, mist, the old ones, Hesper, particles (fireflies, pollen, bees), camera, macro shot, title card, post. |
| `src/music.py` | The score (leitmotifs, chord plan, automation, mastering to −14 LUFS). |
| `src/qa.py` | Automated technical QA → `build/qa/`. |
| `build.py` | Orchestrates everything and fills `output/`. |
| `../../shared/foxfolly/` | Reusable channel toolkit (easing and keyframes, bloom and god rays and grain, typography, synths and reverb and limiter). |

## Deliverables (`output/`, media in Git LFS)

`final_video.mp4` · `subtitles.en.srt` · `script.md` · `music.wav` · `thumbnail_frame.png` ·
`youtube_upload.md` · `production_notes.md`
