"""Small numpy synth + sound-design kit for industrial/metal tracks: synth bass, drones, sub kicks,
impacts, risers, metallic hits, and glitch edits (stutter, tape stop). All mono float32 at rig.SR unless noted."""
import numpy as np
from pedalboard import Pedalboard, LadderFilter, Distortion, Bitcrush, HighpassFilter, LowpassFilter, PeakFilter

from rig import SR, fx

rng = np.random.default_rng(666)


def _buf(length):
    return np.zeros(int(length * SR) + SR, dtype=np.float32)


def _saw(freq, n, phase=0.0):
    ph = (phase + np.arange(n) * freq / SR) % 1.0
    return (2 * ph - 1).astype(np.float32)


def hz(p):
    return 440.0 * 2 ** ((p - 69) / 12)


def synth_bass(notes, length, cutoff=900, drive=22):
    """notes: (pitch, start_s, end_s, vel). Detuned saws + octave-up growl, filtered, then driven hard; clean sine sub."""
    grit, sub = _buf(length), _buf(length)
    for p, s, e, v in notes:
        n = int((e - s) * SR) + int(0.03 * SR)
        f = hz(p)
        tt = np.arange(n) / SR
        osc = _saw(f * 2 ** (-8 / 1200), n) + _saw(f * 2 ** (8 / 1200), n, 0.3) + 0.6 * _saw(f * 2, n, 0.6)
        env = np.minimum(1, tt / 0.003) * np.clip((e - s + 0.03 - tt) / 0.03, 0, 1)
        i0 = int(s * SR)
        grit[i0:i0 + n] += osc * env * (v / 127)
        sub[i0:i0 + n] += np.sin(2 * np.pi * f * tt).astype(np.float32) * env * (v / 127)
    length_n = int(length * SR)
    grit = fx(Pedalboard([LadderFilter(LadderFilter.Mode.LPF24, cutoff_hz=cutoff, resonance=0.3),
                          Distortion(drive_db=drive), HighpassFilter(90), LowpassFilter(5000),
                          PeakFilter(1200, 4, 1.0)]), grit)
    sub = fx(Pedalboard([LowpassFilter(120)]), sub)
    return grit[:length_n], sub[:length_n]


def drone(pitches, start, end, length, cutoff=600, voices=5):
    """Dark detuned-saw pad with slow amplitude swell."""
    out = _buf(length)
    n = int((end - start) * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n, dtype=np.float32)
    for p in pitches:
        for k in range(voices):
            det = (k - (voices - 1) / 2) * 7
            sig += _saw(hz(p) * 2 ** (det / 1200), n, rng.random()) / voices
    env = np.minimum(1, tt / 2.0) * np.minimum(1, (tt[::-1]) / 1.0) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * tt))
    sig = fx(Pedalboard([LadderFilter(LadderFilter.Mode.LPF24, cutoff_hz=cutoff, resonance=0.2)]), sig * env)
    i0 = int(start * SR)
    out[i0:i0 + n] += sig
    return out[:int(length * SR)]


def sub_kick(times, length, vel=1.0):
    """808-style sine kick (150 -> 45 Hz) to reinforce the acoustic kick in heavy sections."""
    out = _buf(length)
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    f = 45 + 105 * np.exp(-tt / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    k = (np.sin(ph) * np.exp(-tt / 0.12)).astype(np.float32)
    k = np.tanh(k * 2.5) / np.tanh(2.5)
    for tm in times:
        i0 = int(tm * SR)
        out[i0:i0 + n] += k * vel
    return out[:int(length * SR)]


def impact(times, length):
    """Cinematic boom: sine dive 90 -> 28 Hz with distortion and a noise crack on top."""
    out = _buf(length)
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    f = 28 + 62 * np.exp(-tt / 0.25)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.9)
    crack = rng.standard_normal(n) * np.exp(-tt / 0.05) * 0.5
    sig = np.tanh(2.0 * boom + crack).astype(np.float32)
    for tm in times:
        i0 = int(tm * SR)
        out[i0:i0 + n] += sig
    return out[:int(length * SR)]


def riser(start, end, length):
    """Noise riser: band of noise sweeping up, swelling in, cut dead at `end`."""
    out = _buf(length)
    n = int((end - start) * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    from rave import svf
    sig = svf(noise, 300 * 40 ** (np.arange(n) / n), q=2.0, mode="bp")
    sig *= (np.linspace(0, 1, n) ** 2)
    i0 = int(start * SR)
    out[i0:i0 + n] += sig
    return out[:int(length * SR)]


def metal_hits(times_vels, length):
    """Industrial metallic percussion: inharmonic partials + noise, bit-crushed and driven."""
    out = _buf(length)
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    partials = [233, 547, 911, 1377, 2210, 3170]
    base = sum(np.sin(2 * np.pi * f * tt + rng.random() * 6) * np.exp(-tt / (0.25 / (1 + i * 0.5)))
               for i, f in enumerate(partials))
    base = base + rng.standard_normal(n) * np.exp(-tt / 0.02) * 2
    hit = fx(Pedalboard([Bitcrush(bit_depth=6), Distortion(drive_db=12), HighpassFilter(200)]),
             (base / np.abs(base).max()).astype(np.float32))
    for tm, v in times_vels:
        i0 = int(tm * SR)
        out[i0:i0 + n] += hit * v
    return out[:int(length * SR)]


# ---------------------------------------------------------------- glitch edits on a stereo mix (2, N)
def stutter(mix, start, end, slice_s, fade=0.002):
    """Replace [start, end) by repeating the slice that begins at `start`."""
    a, b, L = int(start * SR), int(end * SR), int(slice_s * SR)
    sl = mix[:, a:a + L].copy()
    f = int(fade * SR)
    ramp = np.ones(L, dtype=np.float32)
    ramp[:f], ramp[-f:] = np.linspace(0, 1, f), np.linspace(1, 0, f)
    sl *= ramp
    for i in range(a, b, L):
        k = min(L, b - i)
        mix[:, i:i + k] = sl[:, :k]
    return mix


def tape_stop(mix, start, dur):
    """Playback slows to a halt over `dur` seconds (pitch and speed fall together); silence afterwards."""
    a, n = int(start * SR), int(dur * SR)
    speed = np.linspace(1, 0, n) ** 1.5
    pos = a + np.cumsum(speed)
    for c in range(mix.shape[0]):
        mix[c, a:a + n] = np.interp(pos, np.arange(mix.shape[1]), mix[c]) * np.linspace(1, 0.3, n)
    return mix


def silence(mix, start, end, fade=0.004):
    a, b, f = int(start * SR), int(end * SR), int(fade * SR)
    mix[:, a:a + f] *= np.linspace(1, 0, f)
    mix[:, a + f:b] = 0
    return mix
