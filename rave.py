"""Rave / IDM toolkit: TB-303-style acid synth, hoover, siren, detuned FM music box, and a breakbeat
slicer with Aphex-style ratchets (pitched re-triggers), reverses and drops. Mono float32 at rig.SR unless noted."""
import numpy as np
from numba import njit
from pedalboard import Pedalboard, Distortion, HighpassFilter, LowpassFilter, Chorus, Bitcrush, PeakFilter

from rig import SR, fx

rng = np.random.default_rng(1997)


def hz(p):
    return 440.0 * 2 ** ((np.asarray(p, dtype=np.float64) - 69) / 12)


# ---------------------------------------------------------------- time-varying filter
@njit(cache=True)
def _svf(x, fc, q, mode, sr):
    out = np.zeros_like(x)
    lp = 0.0
    bp = 0.0
    for i in range(len(x)):
        f = 2.0 * np.sin(np.pi * min(fc[i], 0.2 * sr) / sr)
        hp = x[i] - lp - bp / q
        bp += f * hp
        lp += f * bp
        out[i] = lp if mode == 0 else (bp if mode == 1 else hp)
    return out


def svf(x, fc, q=0.707, mode="lp"):
    """Click-free time-varying state-variable filter. fc: per-sample cutoff array (Hz). x mono or (C, N)."""
    m = {"lp": 0, "bp": 1, "hp": 2}[mode]
    fc = np.asarray(fc, dtype=np.float64)
    if x.ndim == 2:
        return np.stack([_svf(c.astype(np.float64), fc, q, m, float(SR)) for c in x]).astype(np.float32)
    return _svf(x.astype(np.float64), fc, q, m, float(SR)).astype(np.float32)


# ---------------------------------------------------------------- acid
@njit(cache=True)
def _acid_core(freq, gate, trig, accent, cutoff, reso, env_mod, decay, sr):
    n = len(freq)
    out = np.zeros(n, dtype=np.float32)
    ph = 0.0
    f = freq[0]
    env = 0.0
    amp = 0.0
    s1 = s2 = s3 = s4 = 0.0
    edec = np.exp(-1.0 / (decay * sr))
    glide = 1.0 - np.exp(-1.0 / (0.045 * sr))
    for i in range(n):
        if trig[i] > 0:
            env = 1.0
            f = freq[i]
        f += (freq[i] - f) * glide            # slide between tied notes
        env *= edec
        ph += f / sr
        ph -= np.floor(ph)
        osc = 2.0 * ph - 1.0
        a_tgt = gate[i] * (1.0 + 0.6 * accent[i])
        amp += (a_tgt - amp) * 0.004
        fc = cutoff[i] * (1.0 + env_mod * env * (1.0 + 1.5 * accent[i]))
        if fc > 0.45 * sr:
            fc = 0.45 * sr
        g = 1.0 - np.exp(-2.0 * np.pi * fc / sr)
        k = reso * 4.0 * (1.0 + 0.5 * accent[i])
        x = osc - k * s4
        s1 += g * (np.tanh(x) - np.tanh(s1))
        s2 += g * (np.tanh(s1) - np.tanh(s2))
        s3 += g * (np.tanh(s2) - np.tanh(s3))
        s4 += g * (np.tanh(s3) - np.tanh(s4))
        out[i] = s4 * amp
    return out


def acid(notes, length, cutoff_curve, reso=0.82, env_mod=4.0, decay=0.18, drive=14):
    """notes: (pitch, start_s, end_s, accent 0/1, slide 0/1). cutoff_curve: function(time_s) -> base cutoff Hz."""
    n = int(length * SR)
    freq = np.full(n, hz(40), dtype=np.float64)
    gate = np.zeros(n, dtype=np.float64)
    trig = np.zeros(n, dtype=np.float64)
    acc = np.zeros(n, dtype=np.float64)
    last_end = -1.0
    for p, s, e, a, slide in sorted(notes, key=lambda x: x[1]):
        i0, i1 = int(s * SR), min(n, int(e * SR))
        freq[i0:] = hz(p)
        gate[i0:i1] = 1.0
        acc[i0:i1] = a
        if not (slide and abs(s - last_end) < 0.01):
            trig[i0] = 1.0
        last_end = e
    tt = np.arange(n) / SR
    cut = np.asarray(cutoff_curve(tt), dtype=np.float64)
    y = _acid_core(freq, gate, trig, acc, cut, reso, env_mod, decay, float(SR))
    return fx(Pedalboard([Distortion(drive_db=drive), HighpassFilter(60), LowpassFilter(9000)]), y * 0.8)


# ---------------------------------------------------------------- hoover / siren / music box
def hoover(notes, length, voices=7):
    """Rave hoover: stacked detuned saws + sub square, each note dives into pitch; chorused and driven."""
    out = np.zeros(int(length * SR) + SR, dtype=np.float32)
    for p, s, e, v in notes:
        n = int((e - s + 0.15) * SR)
        tt = np.arange(n) / SR
        bend = 7 * np.exp(-tt / 0.07)                    # semitones above, diving down
        sig = np.zeros(n)
        for k in range(voices):
            det = (k - (voices - 1) / 2) * 9 / 1200
            f = hz(p) * 2 ** (bend / 12 + det)
            ph = np.cumsum(f) / SR + rng.random()
            sig += (2 * (ph % 1) - 1) / voices
        fsub = hz(p - 12) * 2 ** (bend / 12)
        sig += 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(fsub) / SR))
        env = np.minimum(1, tt / 0.005) * np.clip((e - s + 0.15 - tt) / 0.15, 0, 1)
        i0 = int(s * SR)
        out[i0:i0 + n] += (sig * env * v / 127).astype(np.float32)
    out = out[:int(length * SR)]
    return fx(Pedalboard([Chorus(rate_hz=1.2, depth=0.4, mix=0.5), Distortion(drive_db=10), HighpassFilter(80),
                          LowpassFilter(7000)]), out)


def siren(start, end, length, lo=520, hi=1250, rate=0.9):
    out = np.zeros(int(length * SR) + SR, dtype=np.float32)
    n = int((end - start) * SR)
    tt = np.arange(n) / SR
    tri = 2 * np.abs(2 * ((tt * rate) % 1) - 1) - 1
    f = lo + (hi - lo) * (tri + 1) / 2
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 0.5) * np.minimum(1, (tt[::-1]) / 0.3)
    i0 = int(start * SR)
    out[i0:i0 + n] = sig
    return fx(Pedalboard([Distortion(drive_db=18), HighpassFilter(300), LowpassFilter(6000)]), out[:int(length * SR)])


def music_box(notes, length, wow=0.18):
    """Aphex-style detuned FM music box: 2-op FM bell, each note a little out of tune, tape wow & flutter."""
    out = np.zeros(int(length * SR) + 3 * SR, dtype=np.float32)
    for p, s, e, v in notes:
        n = int(2.5 * SR)
        tt = np.arange(n) / SR
        cents = rng.normal(0, 14) + wow * 100 * (0.6 * np.sin(2 * np.pi * 0.7 * (s + tt)) + 0.4 * np.sin(2 * np.pi * 5.3 * (s + tt)) * 0.15)
        f = hz(p) * 2 ** (cents / 1200)
        ph_c = 2 * np.pi * np.cumsum(f) / SR
        ph_m = 2 * np.pi * np.cumsum(f * 3.5) / SR
        index = 2.2 * np.exp(-tt / 0.15)
        sig = np.sin(ph_c + index * np.sin(ph_m)) * np.exp(-tt / 0.9) * np.minimum(1, tt / 0.002)
        i0 = int(s * SR)
        out[i0:i0 + n] += (sig * v / 127).astype(np.float32)
    out = out[:int(length * SR)]
    return fx(Pedalboard([Bitcrush(bit_depth=10), HighpassFilter(250), PeakFilter(3000, -3, 1), LowpassFilter(8000)]), out)


# ---------------------------------------------------------------- breakbeat slicer
def slice_break(brk, step_s, n_slices):
    """Cut a stereo break (2, N) into n equal slices of step_s seconds."""
    L = int(round(step_s * SR))
    return [brk[:, i * L:(i + 1) * L].copy() for i in range(n_slices)], L


def _fade(x, f=48):
    x = x.copy()
    f = min(f, x.shape[1] // 2)
    if f > 0:
        x[:, :f] *= np.linspace(0, 1, f)
        x[:, -f:] *= np.linspace(1, 0, f)
    return x


def _repitch(x, semis, out_len):
    r = 2 ** (semis / 12)
    idx = np.arange(out_len) * r
    idx = idx[idx < x.shape[1] - 1]
    y = np.zeros((2, out_len), dtype=np.float32)
    for c in range(2):
        y[c, :len(idx)] = np.interp(idx, np.arange(x.shape[1]), x[c])
    return y


def chop(dest, start_s, slices, L, seq):
    """Write a slice sequence into stereo `dest` from start_s, one token per step (step = slice length L).
    Tokens: int (play slice), 'r5' (reversed slice 5), 'x' (silence), '-' (let previous ring),
    'k5/4+12' ratchet: slice 5 re-triggered 4x within the step, pitch climbing to +12 semitones (Aphex roll)."""
    pos = int(start_s * SR)
    i = 0
    while i < len(seq):
        tok = str(seq[i])
        ring = 1
        while i + ring < len(seq) and seq[i + ring] == "-":
            ring += 1
        span = L * ring
        a = pos + i * L
        if tok == "x":
            pass
        elif tok.startswith("k"):
            body, _, pitch = tok[1:].partition("+")
            sl, _, cnt = body.partition("/")
            sl, cnt, top = int(sl), int(cnt or 4), float(pitch or 0)
            sub = span // cnt
            for k in range(cnt):
                piece = _repitch(slices[sl], top * k / max(1, cnt - 1), sub)
                dest[:, a + k * sub:a + (k + 1) * sub] += _fade(piece)
        else:
            rev = tok.startswith("r")
            src = slices[int(tok[1:] if rev else tok)]
            src = src[:, ::-1] if rev else src
            # let a slice ring over held steps by reading further into the break isn't possible from one slice,
            # so held steps simply extend the slice's own tail (it is already a full 16th)
            seg = _fade(src[:, :min(span, src.shape[1])])
            dest[:, a:a + seg.shape[1]] += seg
        i += ring
    return dest
