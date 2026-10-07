"""Shared toolkit for the C418-style album ("Volume Gamma"): note names, rubato tempo maps, instrument paths,
Surge XT patch builders, synthesized voices (sine/FM bells/music box), environmental textures (wind, drips,
bubbles), Volume-Alpha tape character and a common master.

Every track script does:   from kit import *   and renders with rig/orch/surge underneath.
"""
import math
import random
import sys
from pathlib import Path

import numpy as np

ALBUM = Path(__file__).resolve().parent
ROOT = ALBUM.parent
for p in (ROOT, ROOT / "ep", ROOT / "c418", ALBUM):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import rig  # noqa: E402
from rig import SR  # noqa: E402
from orch import Sampler, Layer, GRAND, vpo  # noqa: E402
from surge import Surge  # noqa: E402
import rave  # noqa: E402
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowShelfFilter, PeakFilter,  # noqa: E402,F401
                        HighShelfFilter, LowpassFilter, Chorus, Delay, Distortion, Phaser, Gain, Bitcrush)

OUT = ALBUM / "out"
OUT.mkdir(exist_ok=True)
E = rig.LIBS / "extra"

# ---------------------------------------------------------------- instruments (all verified to render with sfizz)
INST = {
    "grand": str(GRAND),                                                     # Salamander grand, CC64
    "upright": str(rig.LIBS / "kw/UprightPianoKW-SFZ+FLAC-20220221/UprightPianoKW-20220221.sfz"),
    "rhodes": str(E / "jlearman.jRhodes3c/jRhodes3c-looped-flac-sfz/_jRhodes-stereo-looped.sfz"),
    "wurli": str(E / "GregSullivan.E-Pianos/Wurlitzer EP200/Wurlitzer EP200.sfz"),
    "cp80": str(E / "GregSullivan.E-Pianos/CP80/CP80.sfz"),
    "pianet": str(E / "GregSullivan.E-Pianos/Pianet T/Pianet T.sfz"),
    "electric_guitar": str(E / "karoryfer.emilyguitar/emily_clean.sfz"),     # Epiphone electric, DI (clean)
    "guitar": str(E / "OvationGuitar/Ovation Guitar (mw1 for 12-string).sfz"),  # acoustic; sounds 8vb: send p+12
    "tenor_sax": str(E / "MTG.SoloSax/MTG Solo Saxophones/MTG Tenor Sax.sfz"),   # top sample E5 (76)
    "alto_sax": str(E / "MTG.SoloSax/MTG Solo Saxophones/MTG Alto Sax.sfz"),
    "lyre": str(E / "cithara-barbarica/Programs/02-cithara_barbarica_finger.sfz"),    # sounds 8va
    "lyre_nail": str(E / "cithara-barbarica/Programs/03-cithara_barbarica_nail.sfz"),
    # VPO / VSCO orchestra (relative names resolve through orch._linux_sfz for VSCO)
    "celesta": vpo("Keys/celesta.sfz"),
    "glock": vpo("Percussion/glockenspiel.sfz"),                             # range ~G5-C8 only
    "vibes": vpo("Percussion/vibraphone-open.sfz"),
    "tubular": vpo("Percussion/tubular-bells.sfz"),
    "timpani": vpo("Percussion/timpani-hit.sfz"),
    "timp_roll": vpo("Percussion/timpani-roll.sfz"),
    "harp": vpo("Strings/harp-sustain.sfz"),
    "strings": vpo("Strings/all-strings-SEC-sustain.sfz"),
    "strings_trem": vpo("Strings/all-strings-SEC-tremolo.sfz"),
    "strings_pizz": vpo("Strings/all-strings-SEC-pizzicato.sfz"),
    "violins": vpo("Strings/1st-violin-SEC-sustain.sfz"),
    "violas": vpo("Strings/viola-SEC-sustain.sfz"),
    "celli": vpo("Strings/cello-SEC-sustain.sfz"),
    "basses": vpo("Strings/bass-SEC-sustain.sfz"),
    "bass_pizz": vpo("Strings/bass-SEC-pizzicato.sfz"),
    "cello_solo": vpo("Strings/cello-SOLO-sustain.sfz"),
    "violin_solo": vpo("Strings/1st-violin-SOLO-sustain.sfz"),
    "horns": vpo("Brass/french-horn-SEC-sustain.sfz"),
    "horn_solo": vpo("Brass/french-horn-SOLO-sustain.sfz"),
    "trombones": vpo("Brass/trombone-SEC-sustain.sfz"),
    "flute": vpo("Woodwinds/flute-SOLO-sustain.sfz"),
    "alto_flute": vpo("Woodwinds/alto-flute-SOLO-sustain.sfz"),
    "clarinet": vpo("Woodwinds/clarinet-SOLO-sustain.sfz"),
    "oboe": vpo("Woodwinds/oboe-SOLO-sustain.sfz"),
    "bassoon": vpo("Woodwinds/bassoon-SOLO-sustain.sfz"),
    "choir_m": vpo("Vocals/choir-MALE-sustain.sfz"),
    "choir_f": vpo("Vocals/choir-FEMALE-sustain.sfz"),
    "choir": vpo("Vocals/choir-MIXED-sustain.sfz"),
    "marimba": "Marimba.sfz",                                                  # VSCO
    "xylo": "Xylophone.sfz",
    "contrabass_jazz": str(rig.LIBS / "vsco_linux/ContrabassPizzJazz.sfz"),    # pizz with short release (jazz/)
}


def inst(name, **kw):
    """Sampler for a named instrument from INST."""
    return Sampler(INST[name], **kw)


# ---------------------------------------------------------------- notes
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def n(name):
    """'C4' -> 60, 'Bb2', 'F#5'."""
    i, pc = 1, PC[name[0]]
    while i < len(name) and name[i] in "b#":
        pc += -1 if name[i] == "b" else 1
        i += 1
    return pc + 12 * (int(name[i:]) + 1)


def ns(s):
    return [n(x) for x in s.split()]


def hz(p):
    return 440.0 * 2 ** ((p - 69) / 12)


# ---------------------------------------------------------------- tempo
class Tempo:
    """Beat -> seconds with a tempo function bpm(beat). Bars have `meter` beats. lead_in seconds before beat 0."""

    def __init__(self, bpm, meter=4, lead_in=1.0, beats=2000):
        f = bpm if callable(bpm) else (lambda b: bpm)
        self.meter = meter
        self.lead_in = lead_in
        self.grid = np.arange(0, beats, 0.01)
        self.tm = np.concatenate([[0], np.cumsum(0.01 * 60 / np.array([f(b) for b in self.grid[:-1]]))])

    def t(self, beat):
        return self.lead_in + float(np.interp(beat, self.grid, self.tm))

    def tb(self, bar, beat=0.0):
        return self.t(bar * self.meter + beat)


def rubato(base, drift=0.025, breath_every=None, breath=0.12, meter=4, rit_from=None, rit_to=None, rit=0.6):
    """Tempo function: slow sinusoidal drift, a breath at the end of every `breath_every` bars, final ritardando."""
    def f(b):
        tp = base * (1 + drift * math.sin(2 * math.pi * b / 27) + drift * 0.5 * math.sin(2 * math.pi * b / 7.7))
        if breath_every:
            ph = (b / meter) % breath_every
            if ph > breath_every - 0.6:
                tp *= 1 - breath * math.sin(math.pi * (ph - (breath_every - 0.6)) / 0.6 / 2)
        if rit_from is not None and b / meter > rit_from:
            span = (rit_to or rit_from + 4) - rit_from
            tp *= max(rit, 1 - (1 - rit) * (b / meter - rit_from) / span)
        return tp
    return f


# ---------------------------------------------------------------- humanising
class Human:
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.np = np.random.default_rng(seed)

    def t(self, sd=0.010):
        return float(self.np.normal(0, sd))

    def v(self, vel, spread=3):
        return int(max(1, min(127, vel + self.r.randint(-spread, spread))))


# ---------------------------------------------------------------- synthesized voices
def voice(notes, length, harm=(1.0,), vib=0.0, vib_rate=4.6, vib_delay=0.45, glide=0.0, att=0.06, rel=0.4,
          seed=0, detune=0.0):
    """Additive voice. notes: (pitch, start, end, amp). harm: amplitudes of harmonics 1..k. Delayed vibrato (cents),
    portamento between connected notes (glide = time constant s), optional detuned second copy (cents)."""
    r = random.Random(seed)
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    notes = sorted(notes, key=lambda x: x[1])
    for j, (p, s, e, a) in enumerate(notes):
        i0, i1 = int(s * SR), min(nn, int((e + rel) * SR))
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        f = hz(p) * np.ones_like(tt)
        if glide and j and s - notes[j - 1][2] < 0.12:
            f0 = hz(notes[j - 1][0])
            f = f * (f0 / f) ** np.exp(-tt / glide)
        if vib:
            depth = vib * np.clip((tt - vib_delay) / 0.8, 0, 1)
            f = f * 2 ** (depth * np.sin(2 * np.pi * vib_rate * tt + r.random() * 6) / 1200)
        w = np.zeros_like(tt)
        for d in ([0.0] if not detune else [-detune / 2, detune / 2]):
            ph = 2 * np.pi * np.cumsum(f * 2 ** (d / 1200)) / SR + r.random() * 6
            for k, h in enumerate(harm, 1):
                w += h * np.sin(k * ph)
        env = np.minimum(1, tt / att) * np.clip((e - s + rel - tt) / rel, 0, 1)
        out[i0:i1] += (a * w * env).astype(np.float32)
    return out


def fm_bell(notes, length, ratio=3.5, index=2.2, decay=2.5, idecay=0.6, seed=0):
    """FM bell / glassy key (DX-style). notes: (pitch, start, dur_hint, amp). Decay in s (scaled down for high notes)."""
    r = random.Random(seed)
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    for p, s, _, a in notes:
        dec = decay * (2 ** (-(p - 72) / 24))
        L = int(min(dec * 5, 14) * SR)
        i0 = int(s * SR)
        i1 = min(nn, i0 + L)
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        f = hz(p)
        mod = index * np.exp(-tt / idecay) * np.sin(2 * np.pi * f * ratio * tt + r.random())
        w = np.sin(2 * np.pi * f * tt + mod) * np.exp(-tt / dec) * np.minimum(1, tt / 0.003)
        out[i0:i1] += (a * w).astype(np.float32)
    return out


def music_box(notes, length, seed=0):
    """Comb-tine music box: bright inharmonic partials, fast decay, slight detune per tine."""
    r = random.Random(seed)
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    parts = [(1.0, 1.0, 1.0), (2.0, 0.35, 0.5), (3.01, 0.12, 0.3), (5.43, 0.10, 0.15), (8.9, 0.05, 0.08)]
    for p, s, _, a in notes:
        f = hz(p) * 2 ** (r.uniform(-4, 4) / 1200)
        i0 = int(s * SR)
        dec = 1.6 * 2 ** (-(p - 72) / 18)
        L = int(dec * 5 * SR)
        i1 = min(nn, i0 + L)
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        w = sum(amp * np.sin(2 * np.pi * f * m * tt + r.random()) * np.exp(-tt / (dec * dm)) for m, amp, dm in parts)
        out[i0:i1] += (a * w * np.minimum(1, tt / 0.002)).astype(np.float32)
    return out


def square_lead(notes, length, duty=0.5, att=0.01, rel=0.08, vib=0.0, seed=0):
    """Band-limited-ish pulse lead (chiptune-ish, for disc tracks): sum of odd/even harmonics up to 8 kHz."""
    r = random.Random(seed)
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    for p, s, e, a in notes:
        i0, i1 = int(s * SR), min(nn, int((e + rel) * SR))
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        f = hz(p)
        if vib:
            fm = f * 2 ** (vib * np.clip((tt - 0.25) / 0.4, 0, 1) * np.sin(2 * np.pi * 5.5 * tt) / 1200)
        else:
            fm = f * np.ones_like(tt)
        ph = 2 * np.pi * np.cumsum(fm) / SR + r.random()
        w = np.zeros_like(tt)
        for k in range(1, int(8000 / f) + 1):
            w += (2 / (k * np.pi)) * np.sin(k * np.pi * duty) * np.cos(k * ph)
        env = np.minimum(1, tt / att) * np.clip((e - s + rel - tt) / rel, 0, 1)
        out[i0:i1] += (a * w * env).astype(np.float32)
    return out


# ---------------------------------------------------------------- Surge XT patch builders
def _surge_base(**kw):
    s = Surge(**kw)
    s.set(a_osc_2_mute=True, a_osc_3_mute=True, a_noise_volume=-float("inf"))
    return s


def surge_pad(cutoff=900.0, attack=2.0, release=4.0, detune=14.0, voices=3, shape=0.0, reso=10.0, drift=45.0,
              osc="Classic", vol=-6.0):
    return _surge_base(a_osc_1_type=osc, a_osc_1_unison_voices=voices, a_osc_1_unison_detune=detune,
                       a_osc_1_shape=shape, a_osc_drift=drift, a_filter_1_type="LP Vintage Ladder",
                       a_filter_1_cutoff=cutoff, a_filter_1_resonance=reso, a_filter_1_keytrack=25.0,
                       a_amp_eg_attack=attack, a_amp_eg_decay=1.0, a_amp_eg_sustain=100.0,
                       a_amp_eg_release=release, a_amp_eg_envelope_mode="Analog", a_volume=vol)


def surge_pluck(cutoff=2500.0, decay=0.6, release=0.5, shape=0.5, detune=8.0, voices=2, sustain=0.0, vol=-6.0):
    """Saw/square pluck: fast attack, filter-envelope-free (cutoff static) but amp decays; good for arps."""
    return _surge_base(a_osc_1_type="Classic", a_osc_1_unison_voices=voices, a_osc_1_unison_detune=detune,
                       a_osc_1_shape=shape, a_osc_drift=20.0, a_filter_1_type="LP Vintage Ladder",
                       a_filter_1_cutoff=cutoff, a_filter_1_resonance=8.0, a_filter_1_keytrack=60.0,
                       a_amp_eg_attack=0.002, a_amp_eg_decay=decay, a_amp_eg_sustain=sustain,
                       a_amp_eg_release=release, a_amp_eg_envelope_mode="Analog", a_volume=vol)


def surge_bass(cutoff=400.0, shape=0.0, attack=0.01, release=0.3, vol=-6.0):
    return _surge_base(a_osc_1_type="Classic", a_osc_1_unison_voices=1, a_osc_1_shape=shape, a_osc_drift=15.0,
                       a_filter_1_type="LP Vintage Ladder", a_filter_1_cutoff=cutoff, a_filter_1_resonance=15.0,
                       a_filter_1_keytrack=30.0, a_amp_eg_attack=attack, a_amp_eg_decay=1.0,
                       a_amp_eg_sustain=100.0, a_amp_eg_release=release, a_amp_eg_envelope_mode="Analog",
                       a_volume=vol)


# ---------------------------------------------------------------- environmental textures
def noise(nsamp, seed=0):
    return np.random.default_rng(seed).normal(0, 1, nsamp).astype(np.float32)


def wind(length, seed=0, lo=250.0, hi=1400.0, rate=0.07, q=2.0):
    """Gusting wind: noise through a slowly wandering resonant bandpass, amplitude-swelling. Mono."""
    nn = int(length * SR)
    r = np.random.default_rng(seed)
    x = noise(nn, seed)
    tt = np.arange(nn) / SR
    ctrl = sum(np.sin(2 * np.pi * rate * k * tt + r.random() * 6) / k for k in (1, 1.7, 2.9))
    ctrl = (ctrl - ctrl.min()) / (np.ptp(ctrl) + 1e-9)
    fc = lo * (hi / lo) ** ctrl
    y = rave.svf(x, fc.astype(np.float32), q, "bp")
    return (y * (0.3 + 0.7 * ctrl ** 1.5)).astype(np.float32)


def drips(length, times, seed=0, lo=1400.0, hi=3600.0, amp=0.3):
    """Water droplets in a cave: short upward-chirping sine 'plinks' at given times. Mono."""
    r = random.Random(seed)
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    for t0 in times:
        f0 = r.uniform(lo, hi)
        L = int(0.09 * SR)
        i0 = int(t0 * SR)
        i1 = min(nn, i0 + L)
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        f = f0 * (1 + 0.9 * (1 - np.exp(-tt / 0.012)))
        ph = 2 * np.pi * np.cumsum(f) / SR
        out[i0:i1] += (amp * r.uniform(0.4, 1.0) * np.sin(ph) * np.exp(-tt / 0.018)).astype(np.float32)
    return out


def bubbles(length, rate=1.2, seed=0, amp=0.15):
    """Underwater bubbles: Poisson trains of tiny upward sine chirps. Mono."""
    r = random.Random(seed)
    t, times = 0.0, []
    while t < length:
        t += r.expovariate(rate)
        k = r.randint(1, 6)
        times += [t + i * r.uniform(0.03, 0.09) for i in range(k)]
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    for t0 in times:
        i0 = int(t0 * SR)
        L = int(0.05 * SR)
        i1 = min(nn, i0 + L)
        if i1 <= i0:
            continue
        tt = np.arange(i1 - i0) / SR
        f0 = r.uniform(500, 1600)
        f = f0 * (1 + 2.5 * tt / 0.05)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out[i0:i1] += (amp * r.uniform(0.3, 1) * np.sin(ph) * np.sin(np.pi * tt / 0.05) ** 2).astype(np.float32)
    return out


def reverse_swell(x, start, dur, length):
    """Take a stereo/mono signal snippet, reverse it, and place it ending at `start + dur` (reverse-cymbal style)."""
    out = np.zeros((2, int(length * SR)), dtype=np.float32)
    x2 = np.stack([x, x]) if x.ndim == 1 else x
    seg = x2[:, :int(dur * SR)][:, ::-1]
    i0 = int(start * SR)
    k = min(seg.shape[1], out.shape[1] - i0)
    out[:, i0:i0 + k] = seg[:, :k]
    return out


# ---------------------------------------------------------------- tape & master
def tape(x, wow_cents=6.0, flutter_cents=1.5, drive=1.6, hiss_db=-66.0, seed=7):
    """Volume-Alpha cassette character: wow & flutter, soft saturation, a little hiss."""
    rng = np.random.default_rng(seed)
    nn = x.shape[1]
    tt = np.arange(nn) / SR
    cents = wow_cents * np.sin(2 * np.pi * 0.42 * tt) + 0.5 * wow_cents * np.sin(2 * np.pi * 0.13 * tt + 1) \
        + flutter_cents * np.sin(2 * np.pi * 6.3 * tt)
    rate = 2 ** (cents / 1200)
    pos = np.clip(np.cumsum(rate) - rate[0], 0, nn - 1)
    y = np.stack([np.interp(pos, np.arange(nn), c) for c in x]).astype(np.float32)
    y = np.tanh(y * drive) / drive
    hiss = rng.normal(0, 1, y.shape).astype(np.float32)
    hiss = rig.fx2(Pedalboard([HighpassFilter(1500), LowpassFilter(9000)]), hiss)
    return y + hiss * 10 ** (hiss_db / 20) * np.abs(y).max()


def master(mix, name, sections=None, stems=None, fade_s=3.0, target_rms_db=-18.0, top_db=-3.0, tape_kw=None):
    """Normalise, tape, gentle master, limiter to target loudness of the loud parts. Writes out/<name>.wav/.mp3."""
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.7
    if tape_kw is not False:
        mix = tape(mix, **(tape_kw or {}))
    if sections and stems is not None:
        rig.section_table({**stems, "mix": mix}, sections)
    board = Pedalboard([HighpassFilter(28), LowShelfFilter(150, 1.0), HighShelfFilter(7000, top_db),
                        Compressor(-20, 1.5, 40, 300)])
    out = rig.finish(mix, OUT / name, board, fade_s=fade_s, target_rms_db=target_rms_db)
    print("written", OUT / f"{name}.mp3", f"{out.shape[1] / SR:.1f}s")
    return out


def place(dst, src, t0):
    """Add src (mono or stereo) into stereo dst at time t0."""
    s2 = np.stack([src, src]) if src.ndim == 1 else src
    i0 = int(t0 * SR)
    k = min(s2.shape[1], dst.shape[1] - i0)
    if k > 0:
        dst[:, i0:i0 + k] += s2[:, :k]
    return dst


# ---------------------------------------------------------------- album motifs (quoted again in the finale, track 12)
# (beat, beats, note). Transpose with shift().
MOTIF_HOME = [(0, 2, "D5"), (2, 1, "A4"), (3, 1, "B4"), (4, 3, "F#4"), (8, 1, "G4"), (9, 1, "A4"), (10, 1, "D5"),
              (11, 1, "C#5"), (12, 4, "A4")]                                      # track 1, D major, 4/4, 4 bars
MOTIF_BIRCH = [(0, 3, "B4"), (3, 1, "E5"), (4, 2, "D5"), (6, 2, "B4"), (8, 3, "A4"), (11, 1, "G4"),
               (12, 4, "E4")]                                                     # track 2, E minor, 4/4, 4 bars
MOTIF_LANTERN = [(0, 1, "Eb5"), (1, 1, "C5"), (2, 1, "Ab4"), (3, 2, "Bb4"), (5, 1, "C5"), (6, 1, "Db5"),
                 (7, 1, "C5"), (8, 1, "Bb4"), (9, 3, "Ab4")]                     # track 4, Ab major, 3/4, 4 bars


def shift(motif, semis):
    """Transpose a motif; returns (beat, beats, midi) tuples."""
    return [(b, d, (n(x) if isinstance(x, str) else x) + semis) for b, d, x in motif]
