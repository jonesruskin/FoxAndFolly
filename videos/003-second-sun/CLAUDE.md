# Video 003 — SECOND SUN

**Status:** delivered (5:09, 1080p24). Deliverables in `second_sun/` (media in Git LFS).
**Brief:** the user-supplied production brief (wordless, 31 shots, leitmotifs, review loop).

## Key facts for future sessions
- Everything is in `second_sun/`: deliverables at the top level, code in `second_sun/source/`, intermediates in `second_sun/build/` (git-ignored).
- Rebuild with `cd second_sun/source && make film`. Re-render one shot with `python build.py --shots S19`.
- Timing source of truth: `source/timeline.py` (shots, cards, star keys, duet tempo map, sync events).
- THE LAKE lock-off lives in `shotkit.lake()`. Never give it per-shot camera parameters.
- Remaining limitations: see `second_sun/REVIEW_LOG.md` §Final.
