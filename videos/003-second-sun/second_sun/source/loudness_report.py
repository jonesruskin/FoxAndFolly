"""Per-shot loudness of the film mix (used by the review loop)."""
import subprocess, sys, os
import numpy as np, pyloudnorm as pyln
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import timeline as TL
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "build", "mix.wav")
x = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "2", "-"], capture_output=True).stdout
x = np.frombuffer(x, np.float32).reshape(-1, 2); sr = 48000
m = pyln.Meter(sr, block_size=0.4)
for sid, a, b, n in TL.SHOTS:
    seg = x[int(a * sr):int(b * sr)]
    try:
        l = m.integrated_loudness(seg)
    except Exception:
        l = -99
    pk = 20 * np.log10(np.abs(seg).max() + 1e-9)
    print(f"{sid} {a:6.1f} {l:6.1f} LUFS  pk {pk:6.1f}  {'#' * max(0, int(l + 40)) if np.isfinite(l) else ''}  {n}")
print("digital silence 225.0-230.0 max sample:", float(np.abs(x[int(225 * sr):int(230 * sr)]).max()))
