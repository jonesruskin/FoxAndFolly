"""Code-only music toolkit: additive instruments, reverb, loudness mastering.

Everything is synthesised from sine waves and noise, so the result is
100% original audio (no samples, nothing for Content ID to match).
"""
import numpy as np
from scipy import signal

SR = 48000


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def db(x):
    return 10 ** (x / 20.0)


class Buffer:
    def __init__(self, seconds, sr=SR):
        self.sr = sr
        self.n = int(seconds * sr)
        self.L = np.zeros(self.n, np.float32)
        self.R = np.zeros(self.n, np.float32)

    def add(self, start, mono, gain=1.0, pan=0.0):
        """Equal-power pan in [-1, 1]."""
        i0 = int(round(start * self.sr))
        if i0 < 0:
            mono, i0 = mono[-i0:], 0
        if i0 >= self.n:
            return
        seg = mono[: self.n - i0] * gain
        a = (pan + 1) * np.pi / 4
        self.L[i0:i0 + len(seg)] += seg * np.cos(a)
        self.R[i0:i0 + len(seg)] += seg * np.sin(a)

    def add_stereo(self, start, l, r, gain=1.0):
        i0 = int(start * self.sr)
        m = min(len(l), self.n - i0)
        self.L[i0:i0 + m] += l[:m] * gain
        self.R[i0:i0 + m] += r[:m] * gain

    def stereo(self):
        return np.stack([self.L, self.R], axis=1)


def _t(dur, sr=SR):
    return np.arange(int(dur * sr), dtype=np.float64) / sr


def env_asr(n, attack, release, sr=SR, curve=2.0):
    """Smooth attack/sustain/release envelope (raised-cosine edges)."""
    e = np.ones(n, np.float32)
    a = min(n // 2, int(attack * sr))
    r = min(n - a, int(release * sr))
    if a > 0:
        e[:a] = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))) ** (curve / 2)
    if r > 0:
        e[n - r:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))) ** (curve / 2)
    return e


def bell(freq, dur=4.0, vel=0.5, bright=1.0, sr=SR):
    """Celesta / soft-piano-like struck tone (inharmonic-ish partials)."""
    t = _t(dur, sr)
    partials = ((1.0, 1.0, 1.0), (2.0, 0.28 * bright, 1.8), (3.01, 0.12 * bright, 2.6),
                (4.07, 0.07 * bright, 3.5), (5.98, 0.03 * bright, 5.0))
    out = np.zeros_like(t)
    tau = 1.4 * (440.0 / freq) ** 0.35
    for ratio, amp, dk in partials:
        f = freq * ratio
        if f > sr * 0.45:
            continue
        out += amp * np.sin(2 * np.pi * f * t + ratio) * np.exp(-t * dk / tau)
    # slow chorus-like shimmer
    out *= 1 + 0.03 * np.sin(2 * np.pi * 4.2 * t)
    atk = np.clip(t / 0.004, 0, 1)
    tail = env_asr(len(t), 0.0, min(0.6, dur * 0.3), sr)
    return (out * atk * tail * vel).astype(np.float32)


def additive_tone(freq, dur, harmonics=10, tilt=1.4, detune_cents=(0.0,), vib=0.0,
                  vib_rate=5.0, attack=1.0, release=2.0, sr=SR, seed=0):
    """Warm sustained tone: sum of detuned band-limited harmonic stacks."""
    rng = np.random.default_rng(seed)
    t = _t(dur, sr)
    out = np.zeros_like(t)
    vibr = vib * np.sin(2 * np.pi * vib_rate * t + rng.random() * 6.28)
    for dc in detune_cents:
        f0 = freq * 2 ** (dc / 1200.0)
        phase_base = 2 * np.pi * f0 * (t + np.cumsum(vibr) / sr)
        for k in range(1, harmonics + 1):
            if f0 * k > sr * 0.45:
                break
            out += np.sin(k * phase_base + rng.random() * 6.28) / k ** tilt
    out /= max(1, len(detune_cents))
    return (out * env_asr(len(t), attack, release, sr)).astype(np.float32)


def noise_band(dur, lo, hi, seed=0, sr=SR):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(int(dur * sr))
    sos = signal.butter(2, [lo, hi], btype="band", fs=sr, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def reverb_ir(seconds=4.0, decay=1.3, seed=1, sr=SR, predelay=0.02):
    """Synthetic stereo hall impulse response: decorrelated noise tails that
    darken over time (high frequencies die faster)."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    out = []
    for ch in range(2):
        rng = np.random.default_rng(seed + ch)
        x = rng.standard_normal(n)
        bright = signal.sosfilt(signal.butter(2, 6000, "low", fs=sr, output="sos"), x)
        dark = signal.sosfilt(signal.butter(2, 1200, "low", fs=sr, output="sos"), x)
        mixk = np.exp(-t / 0.5)
        tail = (bright * mixk + dark * (1 - mixk) * 1.6) * np.exp(-t * 6.9 / (decay * 3))
        pd = int(predelay * sr)
        tail = np.concatenate([np.zeros(pd), tail[: n - pd]])
        out.append(tail / np.sqrt(np.sum(tail ** 2)))
    return np.stack(out, 1).astype(np.float32)


def convolve_reverb(stereo, ir):
    wet = np.zeros_like(stereo)
    for ch in range(2):
        wet[:, ch] = signal.oaconvolve(stereo[:, ch], ir[:, ch], mode="full")[: len(stereo)]
    return wet


def automation(points, n, sr=SR):
    """Piecewise-smooth gain curve from (time, dB) points."""
    ts = np.array([p[0] for p in points]) * sr
    vs = np.array([p[1] for p in points])
    x = np.arange(n)
    from scipy.interpolate import PchipInterpolator
    f = PchipInterpolator(ts, vs, extrapolate=False)
    y = f(np.clip(x, ts[0], ts[-1]))
    return db(y).astype(np.float32)


def true_peak(stereo, sr=SR):
    up = signal.resample_poly(stereo, 4, 1, axis=0)
    return 20 * np.log10(np.max(np.abs(up)) + 1e-12)


def limiter(stereo, ceiling_db=-1.5, lookahead=0.008, release=0.25, sr=SR):
    """Transparent look-ahead peak limiter.

    Gain reduction is computed ahead of each peak and smoothed on both the
    attack (moving average inside the look-ahead window) and the release
    (exponential), so it never switches abruptly and cannot click.
    """
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    ceiling = db(ceiling_db)
    peak = np.max(np.abs(stereo), axis=1)
    la = int(lookahead * sr)
    g_req = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    g_min = minimum_filter1d(g_req, size=2 * la + 1)
    g = uniform_filter1d(g_min, size=la)
    a = np.exp(-1.0 / (release * sr))
    red = signal.lfilter([1 - a], [1, -a], 1 - g)
    g = 1 - np.maximum(red, 1 - g)
    g = uniform_filter1d(g, size=max(3, la // 4))
    return (stereo * g[:, None]).astype(np.float32)
