# Video NNN — TITLE

**Status:** brainstorm
**Branch:** video/NNN-slug

## Decisions so far
- (record every judgment call here and in production_notes.md)

## Next steps
1. Brainstorm ≥5 concepts in production_notes.md, score them, pick one (check bible/episode-log.md).
2. Write src/story.py (lines + scenes), then script.md from it.
3. Build src/render.py (reuse shared/foxfolly), render one style frame per scene, inspect.
4. Compose src/music.py following the script's music cues.
5. `python build.py --qa`, review build/qa/, fix, and repeat until every checklist item passes.
6. Fill output/youtube_upload.md, add a row to bible/episode-log.md.
