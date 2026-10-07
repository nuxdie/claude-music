"""'The Paradise Picture House' — a Dire Straits-style story song in E minor, 140 BPM, light swing.

Eddie, the projectionist at a dying small-town cinema, runs the last reels for nobody.
The vocal line is played by a soft tenor sax (lyrics in out_paradise/lyrics.lrc);
a clean fingerpicked lead guitar answers each line, and the song ends on a long, building outro solo.

Form: Intro hook(4) V1(8) C(8) Hook(4) V2(8) C(8) Solo(8) V3(8) C(8) Outro solo(24) End(2)
"""
import math
import random
import subprocess
from pathlib import Path

import numpy as np
import pretty_midi as pm
import soundfile as sf
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter,
                        LowShelfFilter, Reverb, Delay, Distortion, Limiter, Gain, Chorus)

BPM = 140
SPB = 60.0 / BPM
SWING = 0.035            # offbeat 8ths land slightly late: laid-back feel
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
OUT = Path(__file__).parent / "out_paradise"
OUT.mkdir(exist_ok=True)
rng = random.Random(1978)


def t(beat):
    b = math.floor(beat)
    f = beat - b
    f = f * (0.5 + SWING) / 0.5 if f < 0.5 else 0.5 + SWING + (f - 0.5) * (0.5 - SWING) / 0.5
    return (b + f) * SPB


# ---------------------------------------------------------------- instruments
rhythm = pm.Instrument(27, name="rhythm gtr")    # clean electric
rhythm_up = pm.Instrument(27, name="rhythm gtr upstrokes")
lead = pm.Instrument(27, name="lead gtr")
voice = pm.Instrument(66, name="voice (tenor sax)")
bass = pm.Instrument(33, name="bass")            # fingered bass
drums = pm.Instrument(0, is_drum=True, name="drums")
organ = pm.Instrument(16, name="organ")          # drawbar organ


def note(inst, pitch, beat, dur, vel, jitter=0.008, offset=0.0):
    s = max(0.0, t(beat) + offset + rng.gauss(0, jitter))
    e = max(s + 0.03, t(beat + dur) + offset)
    v = max(1, min(127, int(vel + rng.gauss(0, 4))))
    inst.notes.append(pm.Note(v, pitch, s, e))
    return s, e


# ---------------------------------------------------------------- expressive mono lines (bends / vibrato / hammer-ons)
def expressive(inst, pitch, beat, dur, vel, flags="", jitter=0.007):
    """pitch may be a list (double-stop: no bends). flags: b1/b2 bend up into note, v vibrato, h hammer-on grace."""
    pb = inst.pitch_bends
    if isinstance(pitch, (list, tuple)):
        s = max(0.0, t(beat) + rng.gauss(0, jitter))
        pb.append(pm.PitchBend(0, s))
        for i, p in enumerate(pitch):
            inst.notes.append(pm.Note(max(1, vel - 6 * i), p, s + i * 0.006, t(beat + dur) - 0.012))
        return
    if "h" in flags:  # quick grace note a whole step below
        gs = t(beat) - 0.055
        pb.append(pm.PitchBend(0, gs))
        inst.notes.append(pm.Note(max(1, vel - 20), pitch - 2, gs, gs + 0.05))
    s = max(0.0, t(beat) + rng.gauss(0, jitter))
    e = t(beat + dur) - 0.012
    v = max(1, min(127, int(vel + rng.gauss(0, 5))))
    bf = 2 if "b2" in flags else (1 if "b1" in flags else 0)
    inst.notes.append(pm.Note(v, pitch - bf, s, e))
    pb.append(pm.PitchBend(0, s))
    base = 0
    if bf:
        target = int(8191 * bf / 2)
        bt = min(0.13, (e - s) * 0.5)
        for k in range(1, 9):
            fr = k / 8
            pb.append(pm.PitchBend(int(target * (1 - (1 - fr) ** 2)), s + bt * fr))
        base = target
    if "v" in flags and e - s > 0.3:
        st, tt = s + 0.15, s + 0.15
        while tt < e:
            depth = min(1.0, (tt - st) / 0.35) * 700
            pb.append(pm.PitchBend(int(max(-8192, min(8191, base + depth * math.sin(2 * math.pi * 5.2 * (tt - st))))), tt))
            tt += 0.02


def play(inst, b0, phrase, vel=96):
    for n in phrase:
        beat, dur, p = n[:3]
        flags = n[3] if len(n) > 3 else ""
        # Knopfler-ish touch: downbeats a bit stronger, offbeats lighter, longer notes sing out
        accent = 6 if abs(beat - round(beat)) < 1e-6 else -4
        accent += 6 if dur >= 1 else 0
        expressive(inst, p, b0 + beat, dur, vel + accent, flags)


# ---------------------------------------------------------------- harmony
VOICING = {   # open-position-ish guitar voicings
    "Em": [40, 47, 52, 55, 59, 64], "C": [48, 52, 55, 60, 64], "D": [50, 57, 62, 66],
    "Am": [45, 52, 57, 60, 64], "B7": [47, 51, 57, 59, 66], "G": [43, 47, 50, 55, 59, 67],
}
ROOT = {"Em": 40, "C": 36, "D": 38, "Am": 33, "B7": 35, "G": 31}
FIFTH = {"Em": 47, "C": 43, "D": 45, "Am": 40, "B7": 42, "G": 38}
ORGAN = {"Em": [59, 64, 67], "C": [60, 64, 67], "D": [57, 62, 66], "Am": [57, 60, 64], "B7": [57, 63, 66], "G": [59, 62, 67]}


def strum(ch, beat, dur, vel, down=True):
    v = VOICING[ch] if down else VOICING[ch][::-1][:4]   # upstrokes catch only the top strings
    for i, p in enumerate(v):
        note(rhythm if down else rhythm_up, p, beat, dur, vel - (i * 2 if down else 0), jitter=0.004, offset=i * 0.009)


RHYTHM_PAT = {
    "verse":  [(0, .35, 1, 70), (1, .12, 1, 46), (1.5, .3, 0, 58), (2.5, .3, 0, 60), (3, .12, 1, 46), (3.5, .35, 0, 62)],
    "chorus": [(0, 1.4, 1, 82), (1.5, .45, 0, 66), (2, 1.4, 1, 78), (3.5, .45, 0, 68)],
    "solo":   [(0, .4, 1, 76), (1, .12, 1, 50), (1.5, .3, 0, 64), (2.5, .3, 0, 66), (3, .12, 1, 50), (3.5, .4, 0, 68)],
}


def comp(b0, ch, style):
    for beat, dur, down, vel in RHYTHM_PAT[style]:
        strum(ch, b0 + beat, dur, vel, bool(down))


def bassline(b0, ch, nxt, vel=96):
    r, f = ROOT[ch], FIFTH[ch]
    approach = ROOT[nxt] - 1 if nxt != ch else r + 10
    for beat, dur, p, v in [(0, .9, r, vel), (1.5, .4, r, vel - 14), (2, .9, f, vel - 6),
                            (3, .4, r + 12, vel - 10), (3.5, .45, approach, vel - 8)]:
        note(bass, p, b0 + beat, dur, v, jitter=0.006)


KICK, SNARE, STICK, HHC, HHO, PEDAL, CRASH, RIDE = 36, 38, 37, 42, 46, 44, 49, 51
TOM_H, TOM_M, TOM_L = 48, 45, 43


def dr(p, beat, vel, dur=0.2):
    note(drums, p, beat, dur, vel, jitter=0.005)


def groove(b0, style, crash=False):
    if crash:
        dr(CRASH, b0, 105, 2)
    if style == "verse":
        for i in range(8):
            dr(HHC, b0 + i * .5, 80 if i % 2 == 0 else 55)
        for s in (1, 3):
            dr(STICK, b0 + s, 95)
        for k in (0, 2.5):
            dr(KICK, b0 + k, 100)
    elif style == "chorus":
        for i in range(8):
            dr(HHO if i == 7 else HHC, b0 + i * .5, 88 if i % 2 == 0 else 62)
        for s in (1, 3):
            dr(SNARE, b0 + s, 108)
        for g in (1.75, 3.75):
            dr(SNARE, b0 + g, 32)       # ghost notes
        for k in (0, 1.5, 2, 2.5):
            dr(KICK, b0 + k, 102)
    elif style == "ride":
        for i in range(8):
            dr(RIDE, b0 + i * .5, 92 if i % 2 == 0 else 66)
        for i in range(4):
            dr(PEDAL, b0 + i + .5, 50)
        for s in (1, 3):
            dr(SNARE, b0 + s, 110)
        dr(SNARE, b0 + 2.75, 34)
        for k in (0, 1.5, 2, 3.5):
            dr(KICK, b0 + k, 104)


def fill(b0, size=1):
    for i in range(4):
        dr(HHC, b0 + i * .5, 78)
    dr(KICK, b0, 100); dr(SNARE, b0 + 1, 105)
    if size == 1:
        seq = [(2.5, SNARE), (2.75, SNARE), (3, TOM_H), (3.25, TOM_H), (3.5, TOM_M), (3.75, TOM_L)]
    else:
        seq = [(2 + i * .25, p) for i, p in enumerate([SNARE, SNARE, TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_L])]
    for i, (b, p) in enumerate(seq):
        dr(p, b0 + b, 88 + i * 3)
    dr(KICK, b0 + 2, 96); dr(KICK, b0 + 3, 96)


# ---------------------------------------------------------------- the song's material
HOOK = [  # the signature guitar motif (Em C D B7)
    [(0, .5, 79), (.5, .25, 78), (.75, .25, 76), (1, .5, 71), (1.5, .5, 74), (2, 1.5, 76, "v"), (3.5, .5, 79)],
    [(0, .5, 79), (.5, .5, 76), (1, .5, 72), (1.5, .5, 76), (2, 2, 76, "b2v")],
    [(0, .5, 78), (.5, .25, 76), (.75, .25, 74), (1, .5, 69), (1.5, .5, 74), (2, 1.5, 78, "v"), (3.5, .5, 81)],
    [(0, 1, 83, "b2v"), (1, .5, 81), (1.5, .5, 78), (2, .5, 75), (2.5, .5, 78), (3, 1, 71, "v")],
]

VERSE_CHORDS = ["Em", "C", "D", "Em", "Em", "C", "Am", "B7"]
CHORUS_CHORDS = ["G", "D", "C", "G", "Am", "C", "D", "D"]

# vocal melody, one 2-bar line at a time: (beat, dur, pitch[, flags])
VERSE_MEL = [
    [(0, .5, 71), (.5, .5, 71), (1, .5, 71), (1.5, .5, 69), (2, .5, 67), (2.5, .5, 67),
     (3, .5, 69), (3.5, .5, 67), (4, .5, 64), (4.5, 1.5, 67, "v")],
    [(0, .5, 69), (.5, .5, 69), (1, .5, 71), (1.5, .5, 69), (2, .5, 71), (2.5, .5, 69),
     (3, .5, 66), (3.5, .5, 66), (4, .5, 67), (4.5, .5, 66), (5, 1, 64, "v")],
    [(0, .5, 71), (.5, .5, 71), (1, .5, 74), (1.5, .5, 71), (2, 1, 76, "b2"), (3, .5, 74),
     (3.5, .5, 71), (4, .5, 72), (4.5, .5, 71), (5, .5, 67), (5.5, .5, 64), (6, 1, 67, "v")],
    [(0, .5, 72), (.5, .5, 72), (1, .5, 72), (1.5, .5, 71), (2, .5, 69), (2.5, .5, 69), (3, 1, 64),
     (4, .5, 66), (4.5, .5, 66), (5, .5, 69), (5.5, .5, 69), (6, .5, 71), (6.5, .5, 69), (7, 1, 63, "v")],
]
CHORUS_MEL = [
    [(0, .5, 71), (.5, .5, 72), (1, 1.5, 74, "v"), (2.5, .5, 71), (3, .5, 74), (3.5, 2.5, 69, "v")],
    [(0, .5, 67), (.5, .5, 69), (1, 1, 72), (2, .5, 71), (2.5, .5, 69), (3, 3, 67, "v")],
    [(0, .5, 69), (.5, .5, 69), (1, .5, 72), (1.5, .5, 72), (2, .5, 72), (2.5, .5, 76), (3, .5, 74), (3.5, 2.5, 72, "v")],
    [(0, .5, 69), (.5, .5, 71), (1, 1, 74, "b2"), (2, .5, 72), (2.5, .5, 71), (3, 3, 69, "v")],
]
# guitar answers after each sung line
VERSE_FILLS = [
    [(6, .25, 72), (6.25, .25, 76), (6.5, .5, 79), (7, 1, 76, "b2v")],
    [(6, 1 / 3, 83), (6 + 1 / 3, 1 / 3, 79), (6 + 2 / 3, 1 / 3, 76), (7, .5, 78, "b1"), (7.5, .5, 76)],
    [(7, .5, [76, 79]), (7.5, .5, [74, 77])],
    [],
]
CHORUS_FILLS = [
    [(6, .5, 81, "h"), (6.5, .5, 78), (7, 1, [74, 78])],
    [(6, 1 / 3, 83), (6 + 1 / 3, 1 / 3, 79), (6 + 2 / 3, 1 / 3, 74), (7, .5, 76, "b2"), (7.5, .5, 74)],
    [(6, .5, [76, 79]), (6.5, .5, [77, 81]), (7, 1, [76, 79])],
    [(6, .25, 74), (6.25, .25, 76), (6.5, .25, 78), (6.75, .25, 81), (7, 1, 83, "b2v")],
]

LYRICS = {
    "v1": ["Ne-on's buz-zing on the Pa-ra-dise sign",
           "On-ly half the let-ters still de-cide to shine",
           "Ed-die threads the reel like it's nine-teen fif-ty nine",
           "For a cou-ple in the back and a kid who snuck in-side"],
    "v2": ["Kap-lan tells him the bank has made the call",
           "Gon-na be a car park by the end of fall",
           "Ed-die nods his head, does-n't say a word at all",
           "He just sweeps the pop-corn off the floor and then locks the hall"],
    "v3": ["Sat-ur-day's last show, and no-bo-dy came",
           "Just the rain and the pro-jec-tor's flick-'ring flame",
           "So Ed-die sits down in the front row all the same",
           "He stays to watch the cred-its roll, he reads out ev-'ry name"],
    "ch": ["And the light keeps rol-lin'",
           "through the dust and the haze",
           "at the Pa-ra-dise Pic-ture House",
           "on the last of the days"],
}


def syllables(line):
    return [s for w in line.split() for s in w.split("-")]


for key, lines in LYRICS.items():   # every syllable gets exactly one note
    mel = CHORUS_MEL if key == "ch" else VERSE_MEL
    for line, m in zip(lines, mel):
        assert len(syllables(line)) == len(m), (key, line, len(syllables(line)), len(m))

SOLO = [  # mid-song solo over the verse changes
    [(0, .5, 71), (.5, .5, 74), (1, .5, 76), (1.5, 1.5, 79, "b1v"), (3, .5, 76), (3.5, .5, 74)],
    [(0, 2, 76, "v"), (2, 1 / 3, 79), (2 + 1 / 3, 1 / 3, 76), (2 + 2 / 3, 1 / 3, 72), (3, 1, 71, "v")],
    [(0, .5, 74), (.5, .5, 78), (1, .5, 81), (1.5, .5, 78), (2, 1.5, 86, "b2v"), (3.5, .5, 83)],
    [(0, .25, 81), (.25, .25, 79), (.5, .25, 76), (.75, .25, 74), (1, 1, 76, "v"), (2, .5, [71, 76]),
     (2.5, .5, [71, 76]), (3, 1, [74, 79])],
    [(i / 3, 1 / 3, p) for i, p in enumerate([64, 67, 71, 67, 71, 76, 71, 76, 79, 76, 79, 83])],
    [(0, 1.5, 84, "b1v"), (1.5, .5, 83), (2, .5, 79), (2.5, .5, 76), (3, 1, 79, "v")],
    [(0, .5, 81), (.5, .5, 84), (1, .5, 81), (1.5, .5, 76), (2, .5, 72), (2.5, .5, 76), (3, 1, 81, "v")],
    [(0, .25, 83), (.25, .25, 81), (.5, .25, 78), (.75, .25, 75), (1, .25, 78), (1.25, .25, 81),
     (1.5, .5, 83), (2, 2, 87, "b1v")],
]

OUTRO_CHORDS = ["Em", "D", "C", "D"] * 6
OUTRO_1 = [  # phase 1: melodic, patient
    [(0, 1, 79, "v"), (1, .5, 76), (1.5, .5, 74), (2, 2, 76, "v")],
    [(0, .5, 74), (.5, .5, 76), (1, .5, 78), (1.5, .5, 81), (2, 2, 78, "v")],
    [(0, 1, 79, "b2v"), (1, .5, 76), (1.5, .5, 72), (2, 1, 76), (3, 1, 74)],
    [(0, 3, 78, "b1v"), (3, .5, 81), (3.5, .5, 83)],
    [(0, 1.5, 88, "b2v"), (1.5, .5, 86), (2, .5, 83), (2.5, .5, 79), (3, 1, 83, "v")],
    [(0, .5, 86), (.5, .5, 81), (1, .5, 78), (1.5, .5, 74), (2, 2, 81, "b2v")],
    [(0, .5, [76, 79]), (.5, .5, [76, 79]), (1, 1, [77, 81]), (2, .5, [76, 79]), (2.5, .5, [72, 76]), (3, 1, [74, 78])],
    [(i * .25, .25, p) for i, p in enumerate([74, 76, 78, 79, 81, 83, 84, 86])] + [(2, 2, 88, "b2v")],
]
PENTA = [64, 67, 69, 71, 74, 76, 79, 81, 83, 86, 88, 91]
TOP = {"Em": 83, "D": 81, "C": 79}


def outro_2(i, ch):
    """phase 2: 16th-note sequences, then a sung-out bend."""
    if i % 2 == 0:
        s = 9 - (i // 2) % 3
        seq = []
        for g in range(2):
            seq += [PENTA[s - g - k] for k in range(4)]
        ph = [(k * .25, .25, p) for k, p in enumerate(seq)]
        return ph + [(2, 2, TOP[ch] + 3 if ch == "Em" else TOP[ch], "b2v")]
    s = 1 + (i // 2) % 2
    return [(k * .25, .25, PENTA[s + k // 2 + (k % 2) * 2]) for k in range(16)]


def outro_3(i, ch):
    """phase 3: descending triplet arpeggio cascades across the chord, climbing higher each pair of bars."""
    tones = sorted({p + 12 * o for p in ORGAN[ch] for o in range(0, 3) if 64 <= p + 12 * o <= 93}, reverse=True)
    start = max(0, min(len(tones) - 6, 2 - i // 2))
    seq = [tones[start + j // 3 + j % 3] for j in range(12)]
    ph = [(j / 3, 1 / 3, p) for j, p in enumerate(seq)]
    if i == 7:
        ph = ph[:6] + [(2, 2, 88, "b2v")]
    return ph


# ---------------------------------------------------------------- arrangement
bar = 0
lrc = []


def B():
    return bar * 4


def section(chords, style, drum_style, lead_bars=None, crash_first=True, fill_last=1, organ_on=False, lead_vel=96):
    global bar
    for i, ch in enumerate(chords):
        nxt = chords[i + 1] if i + 1 < len(chords) else chords[0]
        comp(B(), ch, style)
        bassline(B(), ch, nxt, 100 if style == "chorus" else 94)
        if fill_last and i == len(chords) - 1:
            fill(B(), fill_last)
        else:
            groove(B(), drum_style, crash=crash_first and i == 0)
        if organ_on:
            for p in ORGAN[ch]:
                note(organ, p, B(), 3.95, 62, jitter=0.002)
        if lead_bars:
            ph = lead_bars(i, ch) if callable(lead_bars) else lead_bars[i]
            play(lead, B(), ph, lead_vel)
        bar += 1


def sung(chords, mel, fills, lyric_key, style, drum_style, organ_on=False):
    global bar
    b_start = bar
    for li in range(4):
        b0 = (b_start + li * 2) * 4
        play(voice, b0, mel[li], vel=92)
        play(lead, b0, fills[li], vel=88)
        lrc.append((t(b0 + mel[li][0][0]), LYRICS[lyric_key][li].replace("-", "")))
    section(chords, style, drum_style, organ_on=organ_on)


# count-in on the hi-hat pedal, then the hook
section(["Em", "C", "D", "B7"], "verse", "verse", lead_bars=HOOK, crash_first=False, lead_vel=94)
sung(VERSE_CHORDS, VERSE_MEL, VERSE_FILLS, "v1", "verse", "verse")
sung(CHORUS_CHORDS, CHORUS_MEL, CHORUS_FILLS, "ch", "chorus", "chorus", organ_on=True)
section(["Em", "C", "D", "B7"], "verse", "verse", lead_bars=HOOK, lead_vel=96)
sung(VERSE_CHORDS, VERSE_MEL, VERSE_FILLS, "v2", "verse", "verse")
sung(CHORUS_CHORDS, CHORUS_MEL, CHORUS_FILLS, "ch", "chorus", "chorus", organ_on=True)
section(VERSE_CHORDS, "solo", "ride", lead_bars=SOLO, fill_last=2, lead_vel=100)
sung(VERSE_CHORDS, VERSE_MEL, VERSE_FILLS, "v3", "verse", "verse")
sung(CHORUS_CHORDS, CHORUS_MEL, CHORUS_FILLS, "ch", "chorus", "chorus", organ_on=True)
lrc.append((t(B()), "(guitar solo)"))
section(OUTRO_CHORDS[:8], "solo", "chorus", lead_bars=OUTRO_1, lead_vel=98)
section(OUTRO_CHORDS[8:16], "solo", "ride", lead_bars=outro_2, lead_vel=102, organ_on=True)
section(OUTRO_CHORDS[16:], "chorus", "ride", lead_bars=outro_3, fill_last=2, lead_vel=106, organ_on=True)

# ending: one ringing E minor, high bend sings over it
strum("Em", B(), 7.5, 92)
note(bass, 28, B(), 7.5, 105)
for p in ORGAN["Em"]:
    note(organ, p, B(), 7.5, 66)
dr(CRASH, B(), 115, 4); dr(KICK, B(), 110); dr(57, B(), 100, 4)
play(lead, B(), [(0, 7, 88, "b2v")], 104)
END_S = t(B() + 8) + 2.0

# ---------------------------------------------------------------- render + mix (General MIDI version)
def render_gm():
    global stems
    SR = 44100
    rhythm.notes += rhythm_up.notes
    parts = {"rhythm": rhythm, "lead": lead, "voice": voice, "bass": bass, "drums": drums, "organ": organ}
    full = pm.PrettyMIDI(initial_tempo=BPM)
    stems = {}
    for name, inst in parts.items():
        m = pm.PrettyMIDI(initial_tempo=BPM)
        m.instruments.append(inst)
        m.write(str(OUT / f"{name}.mid"))
        full.instruments.append(inst)
        subprocess.run(["fluidsynth", "-ni", "-q", "-R", "0", "-C", "0", "-g", "0.5", "-r", str(SR),
                        "-F", str(OUT / f"{name}.wav"), SF2, str(OUT / f"{name}.mid")], check=True)
        a, _ = sf.read(OUT / f"{name}.wav", dtype="float32")
        stems[name] = a.mean(axis=1)
    full.write(str(OUT / "paradise_picture_house.mid"))

    n = int(END_S * SR)
    stems = {k: np.pad(a, (0, max(0, n - len(a))))[:n] for k, a in stems.items()}


    def fx(board, x):
        return board(x[np.newaxis, :].astype(np.float32), SR)[0]


    def pan(x, p):
        ang = (p + 1) * math.pi / 4
        return np.stack([x * math.cos(ang), x * math.sin(ang)])


    def rms(x):
        return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


    room = Pedalboard([Reverb(room_size=0.45, damping=0.6, wet_level=1.0, dry_level=0.0, width=1.0)])

    # clean Strat-ish tones: low cut, a touch of edge, presence, compression
    rg = fx(Pedalboard([HighpassFilter(110), Distortion(drive_db=2), PeakFilter(3200, 3, 0.8), LowpassFilter(9000),
                        Compressor(-22, 3, 5, 120), Chorus(rate_hz=0.6, depth=0.15, mix=0.25)]), stems["rhythm"])
    lg = fx(Pedalboard([HighpassFilter(140), Distortion(drive_db=5), PeakFilter(2600, 4, 0.7), PeakFilter(400, -3, 1),
                        LowpassFilter(8500), Compressor(-24, 4, 3, 150)]), stems["lead"])
    lg_wet = fx(Pedalboard([Delay(delay_seconds=SPB * 0.75, feedback=0.25, mix=1.0)]), lg)
    vc = fx(Pedalboard([HighpassFilter(160), PeakFilter(250, -3, 1), Compressor(-20, 3, 5, 120)]), stems["voice"])
    bs = fx(Pedalboard([HighpassFilter(35), LowpassFilter(4000), Compressor(-22, 4, 5, 100)]), stems["bass"])
    dm = fx(Pedalboard([HighpassFilter(30), PeakFilter(5000, 2), Compressor(-18, 3, 3, 60)]), stems["drums"])
    og = fx(Pedalboard([HighpassFilter(200), LowpassFilter(5000)]), stems["organ"])

    # balance by loudness targets (dB relative), then pan
    target = {"rg": -21, "lg": -17, "vc": -18, "bs": -18, "dm": -17, "og": -30}
    lv = {"rg": rg, "lg": lg, "vc": vc, "bs": bs, "dm": dm, "og": og}
    g = {k: 10 ** (target[k] / 20) / rms(v[np.abs(v) > 1e-4] if np.any(np.abs(v) > 1e-4) else v) for k, v in lv.items()}

    mix = (pan(rg * g["rg"], -0.55) + pan(lg * g["lg"], 0.35) + pan(lg_wet * g["lg"] * 0.22, -0.35)
           + pan(vc * g["vc"], 0.0) + pan(bs * g["bs"], 0.0) + pan(dm * g["dm"], 0.0) + pan(og * g["og"], -0.2))
    send = rg * g["rg"] * 0.15 + lg * g["lg"] * 0.25 + vc * g["vc"] * 0.3 + dm * g["dm"] * 0.12 + og * g["og"] * 0.4
    mix += np.stack([fx(room, send), fx(room, np.roll(send, 441))]) * 0.6   # slightly decorrelated stereo verb

    master = Pedalboard([LowShelfFilter(90, 1.0), PeakFilter(10000, 1.5, 0.7), Compressor(-16, 2, 15, 200), Limiter(-1.0, 150)])
    mix = master(mix / (np.abs(mix).max() + 1e-9) * 0.8, SR)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.97
    fade = int(2.5 * SR)
    mix[:, -fade:] *= np.linspace(1, 0, fade) ** 2
    sf.write(OUT / "paradise_picture_house.wav", mix.T, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT / "paradise_picture_house.wav"),
                    "-b:a", "256k", str(OUT / "paradise_picture_house.mp3")], check=True)

    with open(OUT / "lyrics.lrc", "w") as fh:
        fh.write("[ti:The Paradise Picture House]\n")
        for s, line in lrc:
            fh.write(f"[{int(s // 60):02d}:{s % 60:05.2f}]{line}\n")
    print(f"bars={bar}  length={END_S:.1f}s")


if __name__ == "__main__":
    render_gm()
