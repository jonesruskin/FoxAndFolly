# Fox & Folly — working notes for Claude

YouTube channel of short animated fables for teens and adults.
Tagline: **"Old wisdom. Sharp twists."** Everything (story, animation, music) is made in code by Claude, and the channel owns 100% of it.

## Read first, every session
1. `bible/channel.md`: audience, format, narrative voice, what makes an episode ours.
2. `bible/style-guide.md`: the visual, typographic and musical identity (non-negotiable look).
3. `bible/episode-log.md`: every published or in-progress video. Don't repeat a story, creature, fact or twist shape.
4. If working on a specific video, that video's `videos/NNN-slug/CLAUDE.md`.

## Repo layout
```
bible/          channel identity (read-only unless the owner changes direction)
shared/fonts/   OFL-licensed fonts (Cormorant Garamond) + license
shared/foxfolly/ reusable Python library: anim (easing/keyframes), post (bloom, god rays,
                grade, grain), text (narration typography), audio (synths, reverb, limiter,
                mastering), noise
templates/video/ skeleton copied by tools/new_video.sh
tools/          new_video.sh, contact_sheet.py
videos/NNN-slug/ one folder per episode:
    CLAUDE.md          status + decisions for this video
    script.md          story, scene table, palette
    production_notes.md brainstorm, tool choices, fact sources, QA checklist
    build.py           ONE command rebuilds every deliverable
    src/story.py       single source of truth for timing (lines, scenes, card)
    src/render.py      frames -> build/video.mp4
    src/music.py       score -> build/music.wav
    src/qa.py          automated QA -> build/qa/
    build/             intermediates (git-ignored, re-creatable)
    output/            deliverables (media tracked by Git LFS)
```

## Rules
- One branch per video; keep channel-wide changes (bible, shared lib) in their own commits.
- Media (`*.mp4 *.wav *.mov`, `videos/*/output/*.png`) goes through **Git LFS** (see `.gitattributes`). Never commit `build/`.
- No external images, footage, audio or non-OFL fonts. Everything visible/audible is generated.
- Timing lives in `src/story.py` only; the script table, subtitles, renderer and QA read from it.
- Every narration line: hold ≥ max(2.5 s, chars/12 s), 0.7 s fades, bottom-centre, title-safe.
- Audio master: 48 kHz stereo, −14 LUFS integrated, true peak ≤ −1 dBTP, AAC 320 kbps in the MP4.
- Video: 1920×1080, 30 fps, H.264 High, yuv420p, ≥ 12 Mbps.
- Before a full render: render one style frame per scene and inspect it. After: run `build.py --qa`
  and review the contact sheets frame by frame.
- Record every judgment call in the video's `production_notes.md`.

## Environment setup (fresh container)
```
apt-get install -y ffmpeg git-lfs libegl1 libgl1
pip install numpy scipy pillow skia-python opencv-python-headless pyloudnorm fonttools
git lfs install
```
