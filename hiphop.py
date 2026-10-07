"""Hip-hop toolkit: neural TTS MCs placed on the beat grid, a pitch-locked robot voice, turntable scratches,
vinyl crackle / needle drops, crate-digging sample helpers, auto-wah. Mono float32 at rig.SR unless noted."""
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, PeakFilter, Distortion, Compressor, Bitcrush,
                        Delay, time_stretch)

from rig import SR, fx, LIBS

rng = np.random.default_rng(1986)
VOICE_DIR = LIBS / "voices"


# ---------------------------------------------------------------- MCs
@lru_cache(maxsize=None)
def _voice(name):
    from piper import PiperVoice
    return PiperVoice.load(str(VOICE_DIR / f"{name}.onnx"))


def trim(a, thr=0.03, pad=0.004):
    idx = np.where(np.abs(a) > thr * np.abs(a).max())[0]
    if not len(idx):
        return a
    p = int(pad * SR)
    return a[max(0, idx[0] - p):idx[-1] + p]


def say(voice, text, speed=1.15, expressive=0.75):
    """Synthesize `text` with a Piper voice at 48 kHz, trimmed."""
    from piper import SynthesisConfig
    v = _voice(voice)
    cfg = SynthesisConfig(length_scale=1 / speed, noise_scale=expressive, noise_w_scale=0.9)
    a = np.concatenate([c.audio_float_array for c in v.synthesize(text, cfg)]).astype(np.float32)
    sr = v.config.sample_rate
    g = np.gcd(SR, sr)
    a = resample_poly(a, SR // g, sr // g).astype(np.float32)
    return trim(a)


def fit(a, target_s, lo=0.7, hi=1.45):
    """Time-stretch (pitch kept) toward target length; ratios are capped so words stay intelligible."""
    ratio = float(np.clip(len(a) / SR / target_s, lo, hi))
    if abs(ratio - 1) < 0.03:
        return a
    return time_stretch(a[np.newaxis, :], SR, stretch_factor=ratio)[0].astype(np.float32)


MEGAPHONE = Pedalboard([HighpassFilter(320), PeakFilter(1800, 7, 0.9), Distortion(drive_db=16), LowpassFilter(4800),
                        Compressor(-24, 6, 1, 60)])


def robotize(a, f0=82.41):
    """Monotone robot voice: zero-phase STFT resynthesis with the hop set so the buzz sits exactly on f0."""
    hop = int(round(SR / f0))
    n = hop * 4
    win = np.hanning(n).astype(np.float32)
    out = np.zeros(len(a) + n, dtype=np.float32)
    a = np.concatenate([a, np.zeros(n, dtype=np.float32)])
    for i in range(0, len(a) - n, hop):
        mag = np.abs(np.fft.rfft(a[i:i + n] * win))
        frame = np.roll(np.fft.irfft(mag, n), n // 2) * win
        out[i:i + n] += frame
    return out / (np.abs(out).max() + 1e-9) * np.abs(a).max()


# ---------------------------------------------------------------- samples / vinyl
def load(path, mono=True):
    a, sr = sf.read(path, dtype="float32")
    a = a.T if a.ndim == 2 else a[np.newaxis, :]
    if sr != SR:
        g = np.gcd(SR, sr)
        a = resample_poly(a, SR // g, sr // g, axis=1).astype(np.float32)
    return a.mean(0) if mono else a


def excerpt(a, start, dur):
    return a[..., int(start * SR):int((start + dur) * SR)].copy()


def to_tempo(a, from_bpm, to_bpm):
    """Time-stretch a loop (pitch kept) from one tempo to another."""
    x = a if a.ndim == 2 else a[np.newaxis, :]
    y = time_stretch(x, SR, stretch_factor=to_bpm / from_bpm)
    return y if a.ndim == 2 else y[0]


def repitch(a, semis):
    """Vinyl-style: speed and pitch change together."""
    r = 2 ** (semis / 12)
    idx = np.arange(0, a.shape[-1] - 1, r)
    if a.ndim == 1:
        return np.interp(idx, np.arange(len(a)), a).astype(np.float32)
    return np.stack([np.interp(idx, np.arange(a.shape[1]), c) for c in a]).astype(np.float32)


DUSTY = Pedalboard([HighpassFilter(140), LowpassFilter(5500), Bitcrush(bit_depth=12), Distortion(drive_db=4)])


def crackle(length, density=6.0, hiss_db=-52):
    n = int(length * SR)
    out = rng.standard_normal(n).astype(np.float32) * 10 ** (hiss_db / 20)
    clicks = rng.random(n) < density / SR
    out[clicks] += rng.uniform(-0.25, 0.25, clicks.sum()).astype(np.float32)
    return fx(Pedalboard([HighpassFilter(800), LowpassFilter(9000)]), out)


def needle_drop():
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    thump = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt / 0.05)
    return (thump + rng.standard_normal(n) * np.exp(-tt / 0.01) * 0.6).astype(np.float32) * 0.6


# ---------------------------------------------------------------- turntable
def scratch(sample, moves, beat_s, depth=0.22):
    """DJ scratch. `moves` is one token per beat:
    'baby' fwd+back, 'chirp' fwd+back with the fader cutting each stroke's tail, 'trans' baby with a 1/32 fader gate,
    'tear' fwd in two pushes then back, 'drag' slow fwd, '.' rest.
    The record position follows smooth hand-shaped curves, so pitch sweeps come out naturally."""
    n_beat = int(beat_s * SR)
    out = []
    for mv in moves:
        u = np.linspace(0, 1, n_beat, endpoint=False)
        gate = np.ones(n_beat, dtype=np.float32)
        if mv == ".":
            out.append(np.zeros(n_beat, dtype=np.float32))
            continue
        if mv in ("baby", "chirp", "trans"):
            pos = depth * np.sin(np.pi * u) ** 2               # out and back
            if mv == "chirp":
                gate = ((u % 0.5) < 0.32).astype(np.float32)
            if mv == "trans":
                gate = ((u * 16) % 1 < 0.5).astype(np.float32)
        elif mv == "tear":                                   # two pushes forward, one pull back
            pos = np.where(u < .25, depth * .5 * (1 - np.cos(np.pi * u / .25)) / 2,
                           np.where(u < .5, depth * (.5 + .5 * (1 - np.cos(np.pi * (u - .25) / .25)) / 2),
                                    depth * (1 + np.cos(np.pi * (u - .5) / .5)) / 2))
        else:  # drag
            pos = depth * 1.8 * u ** 1.3
        idx = pos * SR
        seg = np.interp(idx, np.arange(len(sample)), sample, right=0).astype(np.float32)
        speed = np.abs(np.gradient(pos)) * SR                 # quiet when the hand is nearly still
        seg *= np.clip(speed / 0.3, 0, 1) * gate
        f = 64
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        out.append(seg)
    y = np.concatenate(out)
    return fx(Pedalboard([HighpassFilter(150), LowpassFilter(7000), Distortion(drive_db=5)]), y)


# ---------------------------------------------------------------- effects
def autowah(x, beat_s, lo=400, hi=2200, per_beat=2, q=4.0):
    """Rhythmic wah: a resonant bandpass that sweeps up on every 1/per_beat note (click-free)."""
    from rave import svf
    period = beat_s / per_beat
    ph = ((np.arange(len(x)) / SR) % period) / period
    fc = lo * (hi / lo) ** np.sin(np.pi * np.minimum(1, ph * 1.6))
    return svf(x, fc, q=q, mode="bp") * 1.5 + x * 0.15
