"""'Highway Ninety' — a 4/4 classic rock instrumental in A (mixolydian), 124 BPM.

Structure: Intro(8) Verse(16) Pre(4) Chorus(8) Verse(8) Pre(4) Chorus(8) Solo(8) Chorus(8) Outro(6)
Renders each part through FluidSynth, then mixes with pedalboard.
"""
import math
import random
import subprocess
from pathlib import Path

import numpy as np
import pretty_midi as pm
import soundfile as sf
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter,
                        LowShelfFilter, Reverb, Delay, Distortion, Limiter, Gain)

BPM = 124
SPB = 60.0 / BPM          # seconds per beat
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
rng = random.Random(7)


def t(beat):
    return beat * SPB


# ---------------------------------------------------------------- instruments
def make(program, is_drum=False, name=""):
    return pm.Instrument(program=program, is_drum=is_drum, name=name)


gtrL = make(30, name="rhythm L")       # distortion guitar
gtrR = make(30, name="rhythm R")
bass = make(34, name="bass")           # picked bass
drums = make(0, is_drum=True, name="drums")
lead = make(29, name="lead")           # overdriven guitar
organ = make(18, name="organ")         # rock organ


def note(inst, pitch, beat, dur, vel, jitter=0.010):
    s = t(beat) + rng.gauss(0, jitter)
    e = s + t(dur)
    v = max(1, min(127, int(vel + rng.gauss(0, 5))))
    inst.notes.append(pm.Note(velocity=v, pitch=pitch, start=max(0, s), end=e))


def power(inst, root, beat, dur, vel, jitter=0.010, octave=True):
    # strum: low string first, a few ms apart
    for i, iv in enumerate([0, 7, 12] if octave else [0, 7]):
        note(inst, root + iv, beat + i * 0.012, dur - i * 0.012, vel - i * 4, jitter)


def both_gtrs(root, beat, dur, vel, octave=True):
    power(gtrL, root, beat, dur, vel, 0.008, octave)
    power(gtrR, root, beat, dur, vel - 3, 0.012, octave)


# pitches
A2, B2, C3, D3, E2, F2, G2 = 45, 47, 48, 50, 40, 41, 43
GTR_ROOT = {"A": A2, "D": D3, "E": E2, "G": G2, "F": F2, "C": C3}
BASS_ROOT = {k: v - 12 for k, v in GTR_ROOT.items()}

# ---------------------------------------------------------------- drums
KICK, SNARE, HHC, HHO, CRASH, RIDE = 36, 38, 42, 46, 49, 51
TOM_H, TOM_M, TOM_L, TOM_F = 48, 47, 45, 43


def d(p, beat, vel, dur=0.25):
    note(drums, p, beat, dur, vel, jitter=0.006)


def beat_verse(b0):
    for i in range(8):
        d(HHC, b0 + i * 0.5, 92 if i % 2 == 0 else 68)
    for k in (0, 2, 2.5):
        d(KICK, b0 + k, 110)
    for s in (1, 3):
        d(SNARE, b0 + s, 112)


def beat_chorus(b0, crash=False):
    if crash:
        d(CRASH, b0, 118, 2)
    for i in range(8):
        d(HHO if i % 2 == 0 else HHC, b0 + i * 0.5, 96 if i % 2 == 0 else 72)
    for k in (0, 1.5, 2, 2.5):
        d(KICK, b0 + k, 112)
    for s in (1, 3):
        d(SNARE, b0 + s, 118)


def beat_ride(b0, crash=False):
    if crash:
        d(CRASH, b0, 118, 2)
    for i in range(8):
        d(RIDE, b0 + i * 0.5, 95 if i % 2 == 0 else 75)
    for k in (0, 2, 2.5):
        d(KICK, b0 + k, 110)
    for s in (1, 3):
        d(SNARE, b0 + s, 115)


def fill(b0, big=False):
    # first half: groove, second half: 16th fill around the kit
    for i in range(4):
        d(HHC, b0 + i * 0.5, 85)
    d(KICK, b0, 110); d(SNARE, b0 + 1, 112)
    seq = [SNARE, SNARE, SNARE, SNARE, TOM_H, TOM_H, TOM_M, TOM_M] if not big else \
          [SNARE, SNARE, TOM_H, TOM_H, TOM_M, TOM_M, TOM_F, TOM_F]
    for i, p in enumerate(seq):
        d(p, b0 + 2 + i * 0.25, 92 + i * 3)
    d(KICK, b0 + 2, 105); d(KICK, b0 + 3, 105)


def pre_build(b0, bar):
    # pre-chorus: floor tom + snare quarters, intensifying
    for i in range(8):
        d(HHO if bar >= 2 else HHC, b0 + i * 0.5, 90 if i % 2 == 0 else 70)
    for i in range(4):
        d(KICK, b0 + i, 108)
    if bar < 3:
        d(SNARE, b0 + 1, 112); d(SNARE, b0 + 3, 112)
    else:
        for i in range(8):
            d(SNARE, b0 + i * 0.5, 80 + i * 6)


# ---------------------------------------------------------------- lead guitar w/ bends
BEND_MAX = 8191  # = +2 semitones


def lead_note(pitch, beat, dur, vel=100, bend_from=None, vib=False, jitter=0.008):
    """bend_from: semitones below target to start from (1 or 2); note sounds pitch-bend_from then bends up."""
    s = max(0, t(beat) + rng.gauss(0, jitter))
    e = s + t(dur) * 0.97
    v = max(1, min(127, int(vel + rng.gauss(0, 4))))
    pb = lead.pitch_bends
    if bend_from:
        src = pitch - bend_from
        lead.notes.append(pm.Note(v, src, s, e))
        pb.append(pm.PitchBend(0, s))
        target = int(BEND_MAX * bend_from / 2)
        bend_time = min(0.14, (e - s) * 0.5)
        for k in range(1, 9):
            frac = k / 8
            pb.append(pm.PitchBend(int(target * (1 - (1 - frac) ** 2)), s + bend_time * frac))
        base = target
    else:
        lead.notes.append(pm.Note(v, pitch, s, e))
        pb.append(pm.PitchBend(0, s))
        base = 0
    if vib and (e - s) > 0.35:
        st = s + 0.18
        tt = st
        while tt < e:
            depth = min(1.0, (tt - st) / 0.3) * 900   # ~ a quarter tone wobble
            pb.append(pm.PitchBend(int(max(-8192, min(8191, base + depth * math.sin(2 * math.pi * 5.6 * (tt - st))))), tt))
            tt += 0.02
    # (no reset at note end: the next note resets at its own start, avoiding mid-bend glitches)


def phrase(b0, notes, vel=100):
    for n in notes:
        beat, dur, p = n[:3]
        flags = n[3] if len(n) > 3 else ""
        bf = 2 if "b2" in flags else (1 if "b1" in flags else None)
        lead_note(p, b0 + beat, dur, vel, bend_from=bf, vib="v" in flags)


# melodies (beat-in-bar, dur, pitch, flags)
CHORUS_MEL = [
    [(0, 1, 74, "b2"), (1, .5, 73), (1.5, .5, 71), (2, 2, 69, "v")],
    [(0, .5, 69), (.5, .5, 71), (1, 1.5, 73), (2.5, 1.5, 76, "v")],
    [(0, 1, 78, "b2"), (1, .5, 76), (1.5, .5, 73), (2, 2, 71, "v")],
    [(0, .5, 73), (.5, .5, 71), (1, 3, 69, "v")],
    [(0, 1, 74), (1, .5, 74), (1.5, .5, 76), (2, 2, 78, "vb2")],
    [(0, 1, 76), (1, 1, 73), (2, 2, 69, "v")],
    [(0, .5, 68), (.5, .5, 69), (1, 1, 71), (2, 2, 76, "b2v")],
    [(0, 3.5, 80, "b2v"), (3.5, .5, 76)],
]
VERSE_MEL = [
    [(.5, .5, 64), (1, .5, 67), (1.5, .5, 69), (2, 1, 69), (3, .5, 67), (3.5, .5, 64)],
    [(0, 2.5, 69, "v")],
    [(.5, .5, 66), (1, .5, 69), (1.5, .5, 66), (2, 1, 64), (3, 1, 62)],
    [(0, 3, 64, "b2v")],
    [(.5, .5, 69), (1, .5, 72, "b1"), (1.5, .5, 69), (2, 1.5, 67), (3.5, .5, 64)],
    [(0, 2.5, 69, "v")],
    [(0, .5, 71), (.5, .5, 74), (1, 1, 71), (2, 2, 67, "v")],
    [(0, 1, 66), (1, 1, 69), (2, 2, 64, "b2v")],
]
SOLO = [
    [(0, 1.5, 76, "b2v"), (1.5, .5, 74), (2, .25, 72), (2.25, .25, 69), (2.5, .5, 72, "b1"), (3, 1, 69, "v")],
    [(i * .25, .25, p) for i, p in enumerate([69, 72, 74, 76, 79, 76, 74, 72])] + [(2, 2, 76, "v")],
    [(0, 1, 81, "b2"), (1, .5, 79), (1.5, .5, 76), (2, .5, 74), (2.5, .5, 76), (3, 1, 78, "v")],
    [(0, .5, 76), (.5, .5, 73), (1, .5, 69), (1.5, .5, 72, "b1"), (2, 2, 69, "v")],
    [(0, 1.5, 88, "b2v"), (1.5, .5, 84), (2, .5, 81), (2.5, .5, 84), (3, 1, 81, "v")],
    [(i / 3, 1 / 3, [84, 81, 79][i % 3]) for i in range(12)],
    [(0, 2, 83, "v"), (2, .5, 81), (2.5, .5, 79), (3, 1, 74, "b2")],
    [(0, .5, 76), (.5, .5, 79), (1, .5, 80), (1.5, .5, 81), (2, 2, 88, "b2v")],
]

# ---------------------------------------------------------------- section writers
bar = 0  # running bar counter


def riff_bar(b0, which, full=True, last=False):
    """Main riff: 'A5 . A5 D5 . A5 . .' / 'G5 . G5 D5 . A5 . .' on an 8th grid."""
    hits = ([(0, 1.0, "A"), (1, .4, "A"), (1.5, 1.0, "D"), (2.5, 1.5, "A")] if which == 0 else
            [(0, 1.0, "G"), (1, .4, "G"), (1.5, 1.0, "D"), (2.5, 1.5, "A")])
    if last:  # bass-string walk-up E-G-G# into A
        hits = hits[:-1] + [(2.5, .45, "A")]
    for beat, dur, ch in hits:
        if full:
            both_gtrs(GTR_ROOT[ch], b0 + beat, dur, 108)
        else:
            power(gtrL, GTR_ROOT[ch], b0 + beat, dur, 108)
        if full:
            note(bass, BASS_ROOT[ch], b0 + beat, dur, 105)
    if last:
        for i, p in enumerate([E2, G2, 44]):
            for g in ((gtrL, gtrR) if full else (gtrL,)):
                note(g, p, b0 + 3 + i * 0.33, .3, 110)
            if full:
                note(bass, p - 12, b0 + 3 + i * 0.33, .3, 110)


def chug_bar(b0, ch, accent_end=None):
    r = GTR_ROOT[ch]
    for i in range(8):
        beat = b0 + i * 0.5
        if i == 0:
            both_gtrs(r, beat, .45, 104, octave=False)
        else:
            both_gtrs(r, beat, .18, 78, octave=False)  # palm-mute-ish
        note(bass, BASS_ROOT[ch], beat, .42, 100 if i % 2 == 0 else 88)
    if accent_end:
        both_gtrs(GTR_ROOT[accent_end], b0 + 3.5, .5, 110)


def chorus_bar(b0, ch, drive=False):
    r = GTR_ROOT[ch]
    if drive:
        for i in range(8):
            both_gtrs(r, b0 + i * .5, .45, 110 if i % 2 == 0 else 96)
    else:
        both_gtrs(r, b0, 1.4, 115)
        both_gtrs(r, b0 + 1.5, 2.45, 112)
    for i in range(8):
        note(bass, BASS_ROOT[ch] + (12 if i == 7 else 0), b0 + i * .5, .45, 104 if i % 2 == 0 else 92)
    # organ: triad in mid register
    triads = {"D": [62, 66, 69], "A": [57, 61, 64], "E": [56, 59, 64], "G": [55, 59, 62]}
    for p in triads[ch]:
        note(organ, p, b0, 3.9, 70, 0.003)


# Intro: 4 bars guitar alone, 4 bars full band
for i in range(4):
    riff_bar(bar * 4, i % 2, full=False, last=(i == 3))
    if i == 3:
        fill(bar * 4)
    bar += 1
for i in range(4):
    riff_bar(bar * 4, i % 2, full=True, last=(i == 3))
    (fill if i == 3 else beat_chorus)(bar * 4, *(() if i == 3 else (i == 0,)))
    bar += 1


def verse(n_bars):
    global bar
    prog = ["A", "A", "D", "A", "A", "A", "G", "D"]
    for i in range(n_bars):
        ch = prog[i % 8]
        chug_bar(bar * 4, ch)
        if i == 0:
            d(CRASH, bar * 4, 110, 2)
        (fill if i == n_bars - 1 else beat_verse)(bar * 4)
        phrase(bar * 4, VERSE_MEL[i % 8], vel=92)
        bar += 1


def pre():
    global bar
    for i, ch in enumerate(["F", "G", "F", "G"]):
        r = GTR_ROOT[ch]
        if i < 3:
            both_gtrs(r, bar * 4, 2.4, 112)
            both_gtrs(r, bar * 4 + 2.5, 1.45, 108)
            for k in range(8):
                note(bass, BASS_ROOT[ch], bar * 4 + k * .5, .45, 100)
        else:
            for k in range(8):
                both_gtrs(r, bar * 4 + k * .5, .4, 90 + k * 4)
                note(bass, BASS_ROOT[ch], bar * 4 + k * .5, .4, 92 + k * 4)
        pre_build(bar * 4, i)
        bar += 1


def chorus(final=False):
    global bar
    prog = ["D", "A", "E", "A", "D", "A", "E", "E"]
    for i, ch in enumerate(prog):
        chorus_bar(bar * 4, ch, drive=(i == 7))
        if i == 7:
            fill(bar * 4, big=True)
        else:
            beat_chorus(bar * 4, crash=(i in (0, 4)))
        phrase(bar * 4, CHORUS_MEL[i], vel=110)
        bar += 1


def solo():
    global bar
    prog = ["A", "A", "D", "A", "A", "A", "G", "E"]
    for i, ch in enumerate(prog):
        r = GTR_ROOT[ch]
        both_gtrs(r, bar * 4, 1.4, 108)
        both_gtrs(r, bar * 4 + 1.5, 1.0, 104)
        both_gtrs(r, bar * 4 + 2.5, 1.45, 106)
        for k in range(8):
            note(bass, BASS_ROOT[ch], bar * 4 + k * .5, .45, 100)
        (fill if i == 7 else beat_ride)(bar * 4, *(() if i == 7 else (i == 0,)))
        phrase(bar * 4, SOLO[i], vel=118)
        bar += 1


verse(16)
pre()
chorus()
verse(8)
pre()
chorus()
solo()
chorus(final=True)

# Outro: riff x4 full, then big ending
for i in range(4):
    riff_bar(bar * 4, i % 2, full=True, last=(i == 3))
    (fill if i == 3 else beat_chorus)(bar * 4, *(() if i == 3 else (i == 0,)))
    bar += 1
b0 = bar * 4
both_gtrs(A2, b0, 7.8, 120)
note(bass, A2 - 12, b0, 7.8, 115)
d(CRASH, b0, 125, 4); d(KICK, b0, 120)
for i in range(16):  # tom/snare roll building to the last hit
    d([TOM_F, TOM_L, TOM_M, SNARE][i // 4], b0 + 4 + i * .25, 80 + i * 3)
both_gtrs(A2, b0 + 8, 6, 125)
note(bass, A2 - 12, b0 + 8, 6, 120)
lead_note(81, b0 + 8, 6, 120, bend_from=2, vib=True)
d(CRASH, b0 + 8, 127, 4); d(KICK, b0 + 8, 125); d(57, b0 + 8, 120, 4)
SONG_END = t(b0 + 14) + 1.5

# ---------------------------------------------------------------- render
SR = 44100
parts = {"gtrL": gtrL, "gtrR": gtrR, "bass": bass, "drums": drums, "lead": lead, "organ": organ}
full = pm.PrettyMIDI(initial_tempo=BPM)
stems = {}
for name, inst in parts.items():
    m = pm.PrettyMIDI(initial_tempo=BPM)
    m.instruments.append(inst)
    mid = OUT / f"{name}.mid"
    wav = OUT / f"{name}.wav"
    m.write(str(mid))
    full.instruments.append(inst)
    subprocess.run(["fluidsynth", "-ni", "-q", "-R", "0", "-C", "0", "-g", "0.5", "-r", str(SR),
                    "-F", str(wav), SF2, str(mid)], check=True)
    audio, _ = sf.read(wav, dtype="float32")
    stems[name] = audio.mean(axis=1)  # mono, we pan ourselves
full.write(str(OUT / "highway_ninety.mid"))

n = int(SONG_END * SR) + SR
for k in stems:
    a = stems[k]
    stems[k] = np.pad(a, (0, max(0, n - len(a))))[:n]


def fx(board, x):
    return board(x[np.newaxis, :].astype(np.float32), SR)[0]


def pan(x, p):  # p in [-1, 1], constant power
    ang = (p + 1) * math.pi / 4
    return np.stack([x * math.cos(ang), x * math.sin(ang)])


rhythm_chain = Pedalboard([
    HighpassFilter(90), Distortion(drive_db=8), LowShelfFilter(250, -2),
    PeakFilter(500, -3, 1.0), PeakFilter(2800, 3, 0.8), LowpassFilter(7500),
    Compressor(-18, 3, 5, 80), Gain(2)])
mix = np.zeros((2, n), dtype=np.float32)
mix += pan(fx(rhythm_chain, stems["gtrL"]), -0.85) * 0.9
mix += pan(fx(rhythm_chain, stems["gtrR"]), 0.85) * 0.9
mix += pan(fx(Pedalboard([HighpassFilter(35), Distortion(drive_db=4), LowpassFilter(3500),
                          Compressor(-20, 4, 5, 100), Gain(5)]), stems["bass"]), 0) * 1.0
dr = fx(Pedalboard([HighpassFilter(30), PeakFilter(4000, 2), Compressor(-16, 3, 3, 60), Gain(4)]), stems["drums"])
dr_verb = fx(Pedalboard([Reverb(room_size=0.3, wet_level=1.0, dry_level=0.0)]), dr)
mix += pan(dr + 0.12 * dr_verb, 0) * 1.0
ld = fx(Pedalboard([HighpassFilter(150), Distortion(drive_db=10), PeakFilter(1500, 3, 0.7), LowpassFilter(8000),
                    Compressor(-20, 4, 3, 100), Gain(4)]), stems["lead"])
ld_wet = fx(Pedalboard([Delay(delay_seconds=SPB * 0.75, feedback=0.3, mix=1.0),
                        Reverb(room_size=0.6, wet_level=1.0, dry_level=0.0)]), ld)
mix += pan(ld, 0.1) * 0.85 + pan(ld_wet, -0.3) * 0.25
og = fx(Pedalboard([HighpassFilter(200), Reverb(room_size=0.5, wet_level=0.3, dry_level=0.8)]), stems["organ"])
mix += pan(og, -0.35) * 0.35

master = Pedalboard([Compressor(-14, 2.5, 10, 150), LowShelfFilter(80, 1.5), Limiter(-1.0, 120)])
mix = master(mix / (np.abs(mix).max() + 1e-9) * 0.7, SR)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.97
# fade the tail
fade = int(1.5 * SR)
mix[:, -fade:] *= np.linspace(1, 0, fade)
sf.write(OUT / "highway_ninety.wav", mix.T, SR)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT / "highway_ninety.wav"),
                "-b:a", "256k", str(OUT / "highway_ninety.mp3")], check=True)
print(f"bars={bar}  length={SONG_END:.1f}s  -> {OUT/'highway_ninety.mp3'}")
