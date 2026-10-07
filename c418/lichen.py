"""Lichen — a quiet piano piece in the manner of C418's Minecraft soundtrack (Volume Alpha). Original material.

F major, ~70 BPM with breathing rubato. A close-miked living-room upright (KW, freepats, soft layer) plays
Wet-Hands-style broken chords under a short, plain melody; a slow analog pad (Surge XT) and a sine sub fade in
behind it; an interlude hands the tune to a soft sine lead with delayed vibrato while the piano drops to single
high "droplets"; the piano returns alone and stops on an unresolved add9. Master: tape wow, gentle saturation,
rolled-off top, a little hiss.

Form (bars): intro 4 | A1 8 | A2 8 | B 8 | interlude 8 | A3 8 | ending 2 + fermata.
"""
import math
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "ep"))
sys.path.insert(0, str(HERE))
import rig  # noqa: E402
from rig import SR  # noqa: E402
from orch import Sampler, GRAND  # noqa: E402
from surge import Surge  # noqa: E402
import rave  # noqa: E402

rng = random.Random(2011)
np_rng = np.random.default_rng(2011)
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
KW = rig.LIBS / "kw/UprightPianoKW-SFZ+FLAC-20220221/UprightPianoKW-20220221.sfz"

PC = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def n(name):
    i = 2 if len(name) > 2 and name[1] in "b#" else 1
    return PC[name[:i]] + 12 * (int(name[i:]) + 1)


def ns(s):
    return [n(x) for x in s.split()]


# ---------------------------------------------------------------- harmony: arpeggio pool (low->high), pad voicing, sub
CH = {
    "F":     (ns("F2 C3 G3 A3 C4 E4"), ns("A3 C4 E4 G4"), n("F1")),
    "C/E":   (ns("E2 C3 G3 D4 E4 G4"), ns("E3 G3 C4 D4"), n("E1")),
    "Dm7":   (ns("D2 A2 E3 F3 A3 C4"), ns("F3 A3 C4 E4"), n("D2")),
    "Bbmaj9": (ns("Bb1 F2 D3 A3 C4 D4"), ns("A3 C4 D4 F4"), n("Bb1")),
    "Bb69":  (ns("Bb1 F2 C3 D3 G3 C4"), ns("G3 C4 D4 F4"), n("Bb1")),
    "Csus":  (ns("C2 G2 D3 F3 Bb3 C4"), ns("G3 Bb3 D4 F4"), n("C2")),
    "Am7":   (ns("A1 E2 C3 G3 C4 E4"), ns("E3 G3 C4 E4"), n("A1")),
    "F/A":   (ns("A1 F2 C3 G3 A3 C4"), ns("A3 C4 E4 G4"), n("A1")),
    "Gm7":   (ns("G1 D2 Bb2 F3 A3 D4"), ns("F3 A3 Bb3 D4"), n("G1")),
}
PROG_A = ["F", "C/E", "Dm7", "Bbmaj9", "F", "C/E", "Bb69", "Csus"]
PROG_B = ["Dm7", "Am7", "Bbmaj9", "F/A", "Gm7", "Am7", "Bbmaj9", "Csus"]

# melodies: per bar, (beat, beats, note)
MEL_A = [
    [(0, 2, "C6"), (2, 1, "A5"), (3, 1, "G5")],
    [(0, 3, "E5"), (3, 1, "G5")],
    [(0, 1, "F5"), (1, 1, "E5"), (2, 2, "C5")],
    [(0, 3, "D5")],
    [(0, 2, "C6"), (2, 1, "A5"), (3, 1, "C6")],
    [(0, 2, "D6"), (2, 2, "G5")],
    [(0, 1, "F5"), (1, 1, "G5"), (2, 2, "A5")],
    [(0, 3, "G5")],
]
MEL_B = [
    [(0, 2, "A5"), (2, 1, "F5"), (3, 1, "E5")],
    [(0, 3, "E5"), (3, 1, "C5")],
    [(0, 1, "D5"), (1, 1, "F5"), (2, 2, "A5")],
    [(0, 4, "C6")],
    [(0, 2, "Bb5"), (2, 2, "D5")],
    [(0, 2, "C5"), (2, 1, "E5"), (3, 1, "G5")],
    [(0, 4, "A5")],
    [(0, 2, "G5"), (2.5, 1.5, "F5")],
]
LEAD = [  # interlude: the tune remembered, slower and lower
    [(0, 3, "A4"), (3, 1, "C5")],
    [(0, 4, "G4")],
    [(0, 2, "F4"), (2, 2, "A4")],
    [(0, 4, "D5")],
    [(0, 3, "C5"), (3, 1, "E5")],
    [(0, 4, "D5")],
    [(0, 2, "C5"), (2, 2, "A4")],
    [(0, 4, "G4")],
]

SEC = {"intro": 0, "A1": 4, "A2": 12, "B": 20, "inter": 28, "A3": 36, "end": 44}
END_BAR = 46
PROG = ["F", "Bbmaj9", "F", "Bbmaj9"] + PROG_A * 2 + PROG_B + PROG_A * 2 + ["Bbmaj9", "Bbmaj9"]
assert len(PROG) == END_BAR

# ---------------------------------------------------------------- rubato tempo map
BPM = 70


def tempo(b):
    """Local tempo at beat b: slow drift, a breath at the end of every 8-bar phrase, and a long final ritardando."""
    bar = b / 4
    tp = BPM * (1 + 0.025 * math.sin(2 * math.pi * b / 26) + 0.012 * math.sin(2 * math.pi * b / 7.3))
    ph = (bar - 4) % 8 if bar >= 4 else bar % 4 + 4
    if ph > 7.25:                                   # last three beats of a phrase
        tp *= 1 - 0.14 * math.sin(math.pi * (ph - 7.25) / 0.75 / 2)
    if bar > 42:
        tp *= max(0.62, 1 - 0.38 * (bar - 42) / 4)
    if SEC["inter"] <= bar < SEC["A3"]:             # interlude floats a little slower
        tp *= 0.96
    return tp


_grid = np.arange(0, END_BAR * 4 + 64, 0.01)
_tm = np.concatenate([[0], np.cumsum(0.01 * 60 / np.array([tempo(b) for b in _grid[:-1]]))])
LEAD_IN = 1.2


def t(beat):
    return LEAD_IN + float(np.interp(beat, _grid, _tm))


def tb(bar, beat=0.0):
    return t(bar * 4 + beat)


FERMATA = 11.0
LENGTH = tb(END_BAR) + FERMATA + 4

# ---------------------------------------------------------------- instruments
piano = Sampler(str(KW))
grand = Sampler(str(GRAND))        # soft Salamander underlay for body in the low end
pad = Surge(a_osc_1_type="Classic", a_osc_1_unison_voices=3, a_osc_1_unison_detune=14, a_osc_1_shape=0.0,
            a_osc_drift=45.0, a_filter_1_type="LP Vintage Ladder", a_filter_1_cutoff=780.0,
            a_filter_1_resonance=12.0, a_filter_1_keytrack=25.0,
            a_amp_eg_attack=2.4, a_amp_eg_decay=1.0, a_amp_eg_sustain=100.0, a_amp_eg_release=4.0,
            a_amp_eg_envelope_mode="Analog", a_volume=-6.0)
for k in ("a_osc_2_mute", "a_osc_3_mute"):
    pad.set(**{k: True})
pad.set(a_noise_volume=-float("inf"))


def jit(sd=0.010):
    return np_rng.normal(0, sd)


def pnote(pitch, start, dur, vel, both=False):
    s = start + jit()
    v = vel + rng.randint(-3, 3)
    piano.note(pitch, s, s + dur, v)
    if both:
        grand.note(pitch, s, s + dur, v - 6)


def pedal_bar(bar):
    piano.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)
    grand.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)


P_FULL = [0, 1, 2, 3, 4, 3, 2, 1]
P_RISE = [0, 1, 2, 3, 5, 4, 3, 2]
P_SPARSE = [0, None, 2, 3, None, 4, None, None]
P_HALF = [0, None, None, None, 2, None, 3, None]


def arp(bar, chord, pattern, vel=34):
    pool = CH[chord][0]
    for i, k in enumerate(pattern):
        if k is None:
            continue
        accent = 6 if i == 0 else (2 if i == 4 else 0)
        st = tb(bar, i * 0.5)
        pnote(pool[k], st, tb(bar + 1, 0) - st + 0.3, vel + accent - (i % 2) * 3, both=(k <= 1))
    pedal_bar(bar)


def melody(bar0, mel, vel=46, octave=False, lag=0.018):
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + lag
            en = tb(bar0 + i, b + d)
            v = vel + (4 if b == 0 else 0)
            pnote(n(nm), st, en - st + 0.25, v)
            if octave:
                pnote(n(nm) - 12, st + 0.012, en - st + 0.25, v - 12)


# --- intro: pad alone on F / Bbmaj9, a low bass note per bar, high bell-like notes falling in
for i in range(4):
    bar = SEC["intro"] + i
    ch = PROG[bar]
    pnote(CH[ch][0][0], tb(bar), 3.5, 30, both=True)
    pedal_bar(bar)
for bar, beat, nm, v in [(0, 2.0, "C6", 30), (1, 0.5, "A5", 27), (1, 2.5, "D6", 26), (2, 1.0, "G6", 24),
                         (2, 3.0, "E6", 25), (3, 0.0, "A5", 28), (3, 2.0, "C6", 27)]:
    pnote(n(nm), tb(bar, beat), 2.5, v)

# --- A1: sparse left hand, the tune
for i in range(8):
    bar = SEC["A1"] + i
    arp(bar, PROG[bar], P_SPARSE if i < 7 else P_HALF, vel=32)
melody(SEC["A1"], MEL_A, vel=44)

# --- A2: flowing left hand, tune with octave colour in the second half; a grace echo
for i in range(8):
    bar = SEC["A2"] + i
    arp(bar, PROG[bar], P_FULL if i % 4 != 3 else P_RISE, vel=33)
melody(SEC["A2"], MEL_A[:4], vel=46)
melody(SEC["A2"] + 4, MEL_A[4:], vel=48, octave=True)
pnote(n("D6"), tb(SEC["A2"] + 3, 3.0), 1.2, 30)
pnote(n("C6"), tb(SEC["A2"] + 7, 3.0), 1.2, 28)

# --- B: the lift; left hand fuller, melody in octaves
for i in range(8):
    bar = SEC["B"] + i
    arp(bar, PROG[bar], P_RISE if i % 2 else P_FULL, vel=36)
melody(SEC["B"], MEL_B, vel=50, octave=True)

# --- interlude: pad + sub + sine lead; piano only low roots and high droplets
for i in range(8):
    bar = SEC["inter"] + i
    pool = CH[PROG[bar]][0]
    pnote(pool[0], tb(bar), 3.0, 26, both=True)
    pedal_bar(bar)
    for beat in ([1.5] if i % 2 else [0.5, 2.5]):
        top = [p + 24 for p in pool[3:]]
        pnote(rng.choice(top), tb(bar, beat), 2.0, 22 + rng.randint(0, 4))

# --- A3: piano alone again, softer, half-time left hand
for i in range(8):
    bar = SEC["A3"] + i
    arp(bar, PROG[bar], P_HALF if i < 4 else P_SPARSE, vel=30)
melody(SEC["A3"], MEL_A[:7], vel=40)
pnote(n("G5"), tb(SEC["A3"] + 7, 0) + 0.05, 3.0, 36)

# --- ending: Bbmaj9 twice, slower and slower, then a rolled F add9 left to ring
for i, bar in enumerate((44, 45)):
    arp(bar, "Bbmaj9", P_HALF, vel=30 - 3 * i)
pnote(n("D5"), tb(44, 0) + 0.03, 3.5, 34)
pnote(n("C5"), tb(45, 2) + 0.03, 2.5, 30)
fs = tb(END_BAR)
piano.pedal(fs - 0.03, fs + FERMATA)
grand.pedal(fs - 0.03, fs + FERMATA)
for i, nm in enumerate(["F1", "C2", "G2", "A2", "C3", "G3", "A3", "E4"]):
    piano.note(n(nm), fs + 0.07 * i, fs + FERMATA, 34 - i)
    if i < 3:
        grand.note(n(nm), fs + 0.07 * i, fs + FERMATA, 26)
piano.note(n("G5"), fs + 1.4, fs + FERMATA, 32)
piano.note(n("C6"), fs + 4.2, fs + FERMATA, 26)

# --- pad: enters at A2, full in B and interlude, gone by mid-A3
PAD_BARS = list(range(SEC["intro"], SEC["A1"])) + list(range(SEC["A2"], SEC["A3"] + 3))
for bar in PAD_BARS:
    for p in CH[PROG[bar]][1]:
        pad.note(p, tb(bar) - 0.05, tb(bar + 1) + 0.1, 80)
pad_gain = [(0, tb(4) - 0.5, 0.0), (tb(4) - 0.5, tb(12), -40.0), (tb(12), tb(16), -6.0), (tb(16), tb(20), -2.0),
            (tb(36), tb(40), -5.0), (tb(40), LENGTH, -60.0)]


# --- sub: sine on chord roots, B through interlude
def sine_notes(notes, length, harm=0.0, vib=0.0, glide=0.0, att=0.06, rel=0.4):
    """Sine voice with optional 2nd/3rd harmonic, delayed vibrato and portamento between consecutive notes."""
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    notes = sorted(notes, key=lambda x: x[1])
    for j, (p, s, e, a) in enumerate(notes):
        i0, i1 = int(s * SR), min(nn, int((e + rel) * SR))
        tt = np.arange(i1 - i0) / SR
        f = rave.hz(p) * np.ones_like(tt)
        if glide and j and s - notes[j - 1][2] < 0.12:
            f0 = rave.hz(notes[j - 1][0])
            f = f * (f0 / f) ** np.exp(-tt / glide)
        if vib:
            depth = vib * np.clip((tt - 0.45) / 0.8, 0, 1)
            f = f * 2 ** (depth * np.sin(2 * np.pi * 4.6 * tt + rng.random() * 6) / 1200)
        ph = 2 * np.pi * np.cumsum(f) / SR
        w = np.sin(ph) + harm * 0.35 * np.sin(2 * ph + 0.3) + harm * 0.12 * np.sin(3 * ph)
        env = np.minimum(1, tt / att) * np.clip((e - s + rel - tt) / rel, 0, 1)
        out[i0:i1] += (a * w * env).astype(np.float32)
    return out


sub_notes = [(CH[PROG[bar]][2] + 12, tb(bar), tb(bar + 1) - 0.05, 0.5) for bar in range(SEC["B"], SEC["A3"])]
lead_notes = []
for i, notes in enumerate(LEAD):
    for b, d, nm in notes:
        lead_notes.append((n(nm), tb(SEC["inter"] + i, b) + 0.02, tb(SEC["inter"] + i, b + d) - 0.02, 0.5))

# ================================================================= render & mix
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowShelfFilter, PeakFilter, HighShelfFilter,
                        LowpassFilter, Chorus)  # noqa: E402

print(f"length {LENGTH:.1f}s  A1 {tb(4):.1f}  A2 {tb(12):.1f}  B {tb(20):.1f}  inter {tb(28):.1f}  "
      f"A3 {tb(36):.1f}  end {fs:.1f}")
pno = piano.render(LENGTH)
grd = grand.render(LENGTH)
pd = pad.render(LENGTH)
sub = sine_notes(sub_notes, LENGTH, att=0.4, rel=1.0)
lead = sine_notes(lead_notes, LENGTH, harm=1.0, vib=14, glide=0.07, att=0.09, rel=0.7)

# piano: felt-ish — darker top, warm low-mids, gentle glue
pno = rig.fx2(Pedalboard([HighpassFilter(40), PeakFilter(220, 1.5, 0.8), PeakFilter(2800, -2.5, 0.9),
                          LowpassFilter(6500), Compressor(-26, 1.8, 20, 250)]), pno)
grd = rig.fx2(Pedalboard([HighpassFilter(35), LowpassFilter(2500)]), grd)
pd = rig.fx2(Pedalboard([HighpassFilter(110), PeakFilter(400, -2, 0.8), LowpassFilter(3200), Chorus(0.3, 0.25, 7, 0.0, 0.5)]), pd)
pd = rig.automate(pd, pad_gain, ramp=2.5)
sub = rig.fx(Pedalboard([LowpassFilter(160)]), sub)
lead = rig.fx(Pedalboard([HighpassFilter(150), LowpassFilter(4000)]), lead)

pno = rig.at_level(pno, -20)
grd = rig.at_level(grd, -31)
pd = rig.at_level(pd, -27)
sub = rig.pan(rig.at_level(sub, -26), 0)
lead_st = rig.pan(rig.at_level(lead, -23), -0.1)

piano_bus = pno + grd
dry = piano_bus + pd + sub + lead_st
room = (rig.hall(piano_bus, decay=2.6, size=28, predelay=22, high_cut=6000, early=18, late=72)
        + rig.hall(pd + 0.8 * lead_st, decay=6.0, size=50, predelay=40, high_cut=5000, early=4, late=95) * 0.9)
mix = dry + room


# ---------------------------------------------------------------- tape: wow & flutter, saturation, hiss
def tape(x, wow_cents=6.0, flutter_cents=1.5):
    nn = x.shape[1]
    tt = np.arange(nn) / SR
    cents = wow_cents * np.sin(2 * np.pi * 0.42 * tt) + 0.5 * wow_cents * np.sin(2 * np.pi * 0.13 * tt + 1) \
        + flutter_cents * np.sin(2 * np.pi * 6.3 * tt)
    rate = 2 ** (cents / 1200)
    pos = np.cumsum(rate) - rate[0]
    pos = np.clip(pos, 0, nn - 1)
    y = np.stack([np.interp(pos, np.arange(nn), c) for c in x]).astype(np.float32)
    y = np.tanh(y * 1.6) / 1.6
    hiss = np_rng.normal(0, 1, y.shape).astype(np.float32)
    hiss = rig.fx2(Pedalboard([HighpassFilter(1500), LowpassFilter(9000)]), hiss)
    return y + hiss * 10 ** (-66 / 20) * np.abs(y).max()


mix = mix / np.abs(mix).max() * 0.7
mix = tape(mix)

sections = [("intro", 0, tb(4)), ("A1", tb(4), tb(12)), ("A2", tb(12), tb(20)), ("B", tb(20), tb(28)),
            ("interlude", tb(28), tb(36)), ("A3", tb(36), tb(44)), ("end", tb(44), LENGTH)]
rig.section_table({"piano": piano_bus, "pad": pd, "sub": sub, "lead": lead_st, "mix": mix}, sections)
master = Pedalboard([HighpassFilter(28), LowShelfFilter(150, 1.0), HighShelfFilter(7000, -3.0),
                     Compressor(-20, 1.5, 40, 300)])
rig.finish(mix, OUT / "lichen", master, fade_s=3.5, target_rms_db=-18.0)
print("written", OUT / "lichen.mp3")
