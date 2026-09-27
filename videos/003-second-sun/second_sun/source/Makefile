# SECOND SUN — `make film` rebuilds every deliverable from source.
PY ?= python3
film:
	$(PY) build.py
audio:
	$(PY) build.py --audio-only
qc:
	$(PY) build.py --qc
animatic:
	$(PY) render.py animatic --scale 0.25
.PHONY: film audio qc animatic
