"""Deterministic procedural textures (tileable fractal noise via FFT)."""
import numpy as np


def fractal_noise(h, w, beta=2.0, seed=0, lo_cut=1.0):
    """Tileable 1/f^beta noise normalised to [0, 1]. Larger beta = smoother."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    amp = 1.0 / np.maximum(f, lo_cut) ** (beta / 2.0)
    amp[0, 0] = 0.0
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * amp))
    n -= n.min()
    n /= max(n.max(), 1e-9)
    return n.astype(np.float32)


def sample_wrap(tex, x, y):
    """Bilinear sample of a tileable texture at float coords (arrays ok)."""
    h, w = tex.shape[:2]
    x = np.asarray(x) % w
    y = np.asarray(y) % h
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx = x - x0
    fy = y - y0
    x1 = (x0 + 1) % w
    y1 = (y0 + 1) % h
    a = tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx
    b = tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx
    return a * (1 - fy) + b * fy
