"""'Infernal Engine (Mutation)' — the Mick Gordon track pushed through Prodigy and Aphex Twin. E Phrygian, 136 BPM.

Prodigy: chopped funk breakbeat under the metal riffs, a TB-303 acid line, hoover stabs, a siren.
Aphex Twin: a detuned FM music box, drill'n'bass edits (pitched ratchets, reversed slices) in the 7/8 section
and a drum-edit solo in the break, plus a wonky music-box coda after the final tape stop.

Form: Intro box(8) | Break+acid build(4) | Riff A+breaks(8) | Riff B 7/8 drill(8) | Break: box/acid/drill solo(8)
      | Riff A+lead(8) | Breakdown+hoover(8) | Final(8) | End + coda
"""
import random
from pathlib import Path

import numpy as np
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter,
                        HighShelfFilter, NoiseGate, Delay, Distortion, Bitcrush, Gain)

import rig
import synth
import rave
from rig import SR, Track, Drums, amp, fx, fx2, pan, at_level, stereo_reverb, drum_bus, finish

BPM = 136
SPB = 60 / BPM
DOWN = 7
OUT = Path(__file__).parent / "out_mutation"
OUT.mkdir(exist_ok=True)
rng = random.Random(1997)


def t(beat):
    return beat * SPB


def jit(sd=0.004):
    return rng.gauss(0, sd)


def vh(v, sd=4):
    return v + rng.gauss(0, sd)


gL, gR, lead = Track("guitar"), Track("guitar"), Track("guitar")
kit = Drums()                    # live kit: kick unison, crashes, blasts
bass_notes, kicks_sub, metal, impacts, risers, drones = [], [], [], [], [], []
acid_notes, hoover_notes, box_notes, sirens = [], [], [], []
chops = []                       # (start_s, sequence)
break_filter = []                # (start_s, end_s, from_hz, to_hz) lowpass sweeps on the break bus
glitches = []

CH = {"X": [28, 35, 40], "x": [28, 35], "O": [40, 47, 52], "F": [29, 36, 41], "B": [34, 41, 46], "G": [31, 38, 43]}
ROOT = {"X": 28, "x": 28, "O": 40, "F": 29, "B": 34, "G": 31}


def hit(name, beat, vel, sd=0.003):
    kit.hit(name, t(beat) + jit(sd), vh(vel, 3))


def riff(b0, pattern, vel=118, kick=True, hoov=False):
    steps, i = len(pattern), 0
    while i < steps:
        c = pattern[i]
        if c in CH:
            hold = 1
            while i + hold < steps and pattern[i + hold] == "-":
                hold += 1
            beat = b0 + i * 0.25
            muted = c == "x"
            dur = 0.2 if muted else hold * 0.25 - 0.03
            for tr, sd in ((gL, 0.003), (gR, 0.005)):
                s0 = t(beat) + jit(sd)
                for k, p in enumerate(CH[c]):
                    tr.note(p, s0 + k * 0.004, s0 + t(dur), vh(vel - (8 if muted else 0)), "mute_down" if muted else "down")
            bass_notes.append((ROOT[c], t(beat), t(beat + dur), vel))
            if kick:
                hit("kick", beat, 118)
                kicks_sub.append(t(beat))
            if hoov and not muted and hold >= 2:
                hoover_notes.append((ROOT[c] + 24, t(beat), t(beat + dur), 110))
            i += hold
        else:
            i += 1


A = ["X-.xx.xO.xx.F-.x", "X-.xx.xO.xx.B-G-"]
B = ["X-.x.xX-.x.xF-", "X-.x.xX-.x.xB."]
BD = ["X--.....X--.x.xx", "B-----..F-----.x"]

# breakbeat chop sequences (slice indices into a 2-bar, 32-slice funk break)
NORM = [list(range(16)), list(range(16, 32))]
CHOP = [[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 10, 11, 12, 13, "k12/2", 15],
        [16, 17, 18, 19, 20, 21, "r4", 23, 24, 25, 26, 27, "k28/4+5", "k28/4+7", "k12/8+12", "k12/8+19"]]
DRILL = [[0, "k7/3", 2, "k9/6+7", 4, "x", 6, 0, "k12/4", 10, 11, "k12/8+12", "r4", 15],
         [16, "k17/3", 18, 19, "k20/8+12", 21, "r22", 24, "k25/6+3", 26, "k27/2", 28, "k12/12+24", "x"]]
DSOLO = [["k4/16+12", "x", "k0/3", 2, "k12/6+5", 13, "r14", "x", "k7/12+19", "k9/5", 10, "r11", "k12/24+24", "-", "x", "k4/3"],
         ["k0/8", 1, "k4/32+36", "-", "-", "-", "x", "r12", 8, "k9/6+7", "k12/4+12", "k12/6+17", "k12/8+24", "k12/12+31",
          "k12/16+38", "x"]]
HALF = [[0, "-", "x", "x", 4, "-", "x", "x", "x", "x", 2, "x", 12, "-", "x", "r12"],
        [16, "-", "x", "x", 20, "-", "x", 7, "x", "x", 26, "x", 28, "-", "k12/4+7", "k12/6+12"]]

# acid line: (step, semitone above E2, accent, slide)
ACID = [(0, 0, 1, 0), (1, 0, 0, 0), (2, 12, 0, 1), (3, 0, 0, 0), (4, 1, 1, 0), (5, 0, 0, 0), (6, 12, 0, 0), (7, 15, 1, 1),
        (8, 0, 0, 0), (9, 6, 0, 0), (10, 0, 1, 0), (11, 12, 0, 1), (12, 13, 0, 0), (13, 0, 0, 0), (14, 18, 1, 1), (15, 0, 0, 0)]


def acid_bar(b0, transpose=0, density=1.0):
    for st, semi, acc, slide in ACID:
        if density < 1 and rng.random() > density and st % 4:
            continue
        s = t(b0 + st * .25)
        e = s + t(.25) * (1.02 if slide else 0.55)
        acid_notes.append((40 + semi + transpose, s, e, acc, slide))


BOX = [[(0, 1, 76), (1, .5, 79), (1.5, .5, 77), (2, 2, 76)], [(0, 1, 72), (1, 1, 71), (2, 2, 76)],
       [(0, 1, 77), (1, .5, 79), (1.5, .5, 80), (2, 2, 79)], [(0, 1, 77), (1, 1, 76), (2, 2, 71)],
       [(0, .5, 88), (.5, .5, 84), (1, .5, 83), (1.5, .5, 79), (2, 2, 76)], [(0, 1, 77), (1, 1, 72), (2, 2, 71)],
       [(0, .5, 76), (.5, .5, 77), (1, .5, 79), (1.5, .5, 82), (2, 2, 83)], [(0, 4, 76)]]


def box_bar(b0, phrase, vel=90, drift=0.02):
    for beat, dur, p in phrase:
        box_notes.append((p, t(b0 + beat) + rng.gauss(0, drift), t(b0 + beat + dur), vel))


def groove_A(b0, i, double_kick=False):
    if i % 2 == 0:
        hit("crash_l" if i % 4 == 0 else "crash_r", b0, 122)
    if double_kick:
        for s in range(16):
            hit("kick", b0 + s * .25, 104)
            kicks_sub.append(t(b0 + s * .25))


LEAD = [[(0, 1.5, 76, "b2v"), (1.5, .5, 77), (2, 2, 76, "v")], [(0, 1, 79), (1, 1, 77), (2, 1, 76), (3, 1, 74)],
        [(0, 3, 77, "b1v"), (3, 1, 80)], [(0, 4, 76, "v")], [(0, 1.5, 83, "b2v"), (1.5, .5, 82), (2, 2, 80, "v")],
        [(0, 1, 79), (1, 1, 77), (2, 2, 76, "v")], [(0, .5, 76), (.5, .5, 77), (1, .5, 80), (1.5, .5, 82), (2, 2, 83, "b1v")],
        [(0, 4, 88, "b2v")]]


def lead_line(b0, phrase, vel=115):
    for n in phrase:
        beat, dur, p = n[:3]
        flags = n[3] if len(n) > 3 else ""
        s, e = t(b0 + beat) + jit(), t(b0 + beat + dur) - 0.015
        bf = 2 if "b2" in flags else (1 if "b1" in flags else 0)
        lead.note(p - bf, s, e, vh(vel), "long")
        lead.bend(s - 0.002, 0)
        base = 0
        if bf:
            for k in range(1, 9):
                lead.bend(s + 0.12 * k / 8, bf * (1 - (1 - k / 8) ** 2))
            base = bf
        if "v" in flags:
            tt = s + 0.2
            while tt < e:
                lead.bend(tt, base + min(1, (tt - s - 0.2) / 0.3) * 0.3 * np.sin(2 * np.pi * 6 * (tt - s - 0.2)))
                tt += 0.015


# ---------------------------------------------------------------- arrangement
pos = 0.0
SECTIONS = []


def mark(name, beats):
    SECTIONS.append((name, t(pos), t(pos + beats)))


# 1. Intro: the music box, alone with a tritone hum; the break creeps in through a closed filter
mark("intro", 32)
drones.append(([28, 34], t(0), t(48) + 0.3, 450))
for bar in range(8):
    box_bar(pos + bar * 4, BOX[bar])
    if bar >= 4:
        chops.append((t(pos + bar * 4), NORM[bar % 2]))
    if bar >= 6:
        acid_bar(pos + bar * 4, density=0.6)
break_filter.append((t(pos + 16), t(pos + 32), 300, 1800))
pos += 32

# 2. Build: full break + acid opening up + siren, drill fill, stutter
mark("build", 16)
for bar in range(4):
    chops.append((t(pos + bar * 4), DSOLO[0] if bar == 3 else NORM[bar % 2]))
    acid_bar(pos + bar * 4)
sirens.append((t(pos), t(pos + 16)))
risers.append((t(pos + 4), t(pos + 15)))
glitches.append(("stutter", t(pos + 15), t(pos + 15.5), t(0.125)))
glitches.append(("stutter", t(pos + 15.5), t(pos + 16), t(0.0625)))
pos += 16

# 3. DROP: Riff A over chopped breaks, hoover stabs
mark("riffA", 32)
impacts.append(t(pos))
for i in range(8):
    riff(pos, A[i % 2], hoov=(i % 4 == 0))
    groove_A(pos, i)
    chops.append((t(pos), CHOP[i % 2] if i % 4 == 3 else NORM[i % 2]))
    pos += 4

# 4. Riff B in 7/8, drill'n'bass
mark("riffB", 28)
for i in range(8):
    riff(pos, B[i % 2])
    if i % 2 == 0:
        hit("crash_l", pos, 120)
    chops.append((t(pos), DRILL[i % 2]))
    pos += 3.5

# 5. Break: tape stop; detuned music box over acid; drill'n'bass drum solo; siren; riser
mark("break", 32)
riff(pos, A[0])
chops.append((t(pos), NORM[0]))
glitches.append(("tapestop", t(pos + 2), t(2), None))
pos += 4
drones.append(([28, 34], t(pos), t(pos + 20), 500))
for bar in range(4):
    box_bar(pos + bar * 4, BOX[bar], vel=80, drift=0.035)
    acid_bar(pos + bar * 4, transpose=0 if bar < 2 else 5)
    if bar >= 2:
        chops.append((t(pos + bar * 4), NORM[bar % 2]))
break_filter.append((t(pos + 8), t(pos + 16), 500, 6000))
pos += 16
for bar in range(2):
    chops.append((t(pos + bar * 4), DSOLO[bar]))
    acid_bar(pos + bar * 4, transpose=7 * bar)
sirens.append((t(pos), t(pos + 8)))
risers.append((t(pos), t(pos + 8)))
glitches.append(("stutter", t(pos + 7.5), t(pos + 8), t(0.0625)))
pos += 8
pos += 4   # (bar 8 of the break: the drill solo's tail rings into silence -- dramatic gap)
glitches.append(("silence", t(pos - 4), t(pos - 0.02), None))

# 6. Riff A + lead + double kick + breaks + acid underneath
mark("A+lead", 32)
impacts.append(t(pos))
for i in range(8):
    riff(pos, A[i % 2], kick=False)
    groove_A(pos, i, double_kick=True)
    lead_line(pos, LEAD[i])
    chops.append((t(pos), CHOP[i % 2]))
    acid_bar(pos, density=0.8)
    pos += 4

# 7. Breakdown: half-time, hoover stabs, impacts, half-time break chops
mark("breakdown", 32)
drones.append(([40, 47, 55, 59], t(pos), t(pos + 32) + 0.3, 1400))
for i in range(8):
    riff(pos, BD[i % 2], vel=124, hoov=True)
    if i % 4 == 0:
        impacts.append(t(pos))
    hit("crash_l" if i % 2 == 0 else "crash_r", pos, 125)
    hit("snare", pos + 2, 127)
    chops.append((t(pos), HALF[i % 2]))
    pos += 4

# 8. Final: blast beat + breaks + acid, drill stutters, out
mark("final", 32)
impacts.append(t(pos))
for i in range(8):
    riff(pos, A[i % 2], kick=(i >= 4))
    if i < 4:
        for s in range(16):
            hit("kick" if s % 2 == 0 else "snare", pos + s * .25, 115 if s % 2 == 0 else 105)
            if s % 2 == 0:
                kicks_sub.append(t(pos + s * .25))
        for q in range(4):
            hit("crash_l" if q % 2 == 0 else "crash_r", pos + q, 110)
    else:
        groove_A(pos, i)
    chops.append((t(pos), DRILL[0] + ["k12/4+12", "k12/8+24"] if i == 7 else CHOP[i % 2]))
    acid_bar(pos, transpose=12 if i >= 4 else 0)
    pos += 4
glitches.append(("stutter", t(pos - 2), t(pos - 1), t(0.125)))
glitches.append(("stutter", t(pos - 1), t(pos), t(0.03125)))

# 9. End: last hit, tape stop, then the music box comes back alone, wrong
riff(pos, "X---------------")
impacts.append(t(pos))
hit("crash_l", pos, 127); hit("crash_r", pos, 125)
glitches.append(("tapestop", t(pos + 3), 1.6, None))
coda = t(pos + 3) + 2.2
for k, p in enumerate([76, 77, 76, 71]):
    box_notes.append((p, coda + k * 0.42 + rng.gauss(0, 0.03), coda + k * 0.42 + 0.4, 70))
END = coda + 3.5

# ---------------------------------------------------------------- render
print(f"{END:.1f}s. rendering...")
di_L, di_R = gL.render(END, down=DOWN), gR.render(END, down=DOWN)
di_lead = lead.render(END)
kitmics = kit.render(END)

# the break: a 2-bar funk break played on the kit, then crushed like an old sampler
bk = Drums()
for bar in range(2):
    b0 = bar * 4
    kicks = [0, 2, 10, 11] if bar == 0 else [0, 2, 10]
    for st in kicks:
        bk.hit("kick", t(b0 + st * .25), 112)
    for st in (4, 12):
        bk.hit("snare", t(b0 + st * .25), 122)
    for st in ([7, 9, 15] if bar == 0 else [7, 9, 14]):
        bk.hit("snare", t(b0 + st * .25), 62)
    for st in range(0, 16, 2):
        bk.hit("hh_open" if st == 14 and bar == 1 else "hh_closed", t(b0 + st * .25), 92 if st % 4 == 0 else 72)
brk = drum_bus(bk.render(t(8) + 1), room=0.7, close=1.0)
brk = fx2(Pedalboard([Compressor(-24, 6, 2, 80), Distortion(drive_db=7), Bitcrush(bit_depth=12),
                      HighpassFilter(45), LowpassFilter(11000), Gain(-6)]), brk)
slices, L = rave.slice_break(brk, t(0.25), 32)
brk_bus = np.zeros((2, int(END * SR) + SR), dtype=np.float32)
for start, seq in chops:
    rave.chop(brk_bus, start, slices, L, seq)
brk_bus = brk_bus[:, :int(END * SR)]
for s, e, f0, f1 in break_filter:   # smooth exponential lowpass sweeps
    a, b = int(s * SR), int(e * SR)
    fc = f0 * (f1 / f0) ** (np.arange(b - a) / (b - a))
    brk_bus[:, a:b] = rave.svf(brk_bus[:, a:b], fc)

grit, sub = synth.synth_bass(bass_notes, END)
subk = synth.sub_kick(kicks_sub, END)
imp = synth.impact(impacts, END)
rs = sum(synth.riser(a, b, END) for a, b in risers)
dn = sum(synth.drone(p, a, b, END, cutoff=c) for p, a, b, c in drones)


def acid_cut(tt):  # the knob-twiddling: slow sweeps across the song
    return 350 + 900 * (0.5 + 0.5 * np.sin(2 * np.pi * tt / (t(32)))) ** 2


ac = rave.acid(acid_notes, END, acid_cut)
hv = rave.hoover(hoover_notes, END)
sr_ = sum(rave.siren(a, b, END) for a, b in sirens)
mb = rave.music_box(box_notes, END)

print("amps...")
pre = Pedalboard([NoiseGate(threshold_db=-48, ratio=10, attack_ms=0.5, release_ms=40), HighpassFilter(110),
                  PeakFilter(900, 6, 0.8)])
aL = amp(fx(pre, di_L), "JVM-OD2-RD-Cab", peak_in=0.7)
aR = amp(fx(pre, di_R), "Bug333-Lead-Cab", peak_in=0.7)
ld = amp(fx(Pedalboard([HighpassFilter(150), PeakFilter(900, 4, 0.8)]), di_lead), "JVM-OD2-RD-Cab", peak_in=0.6)
post = Pedalboard([NoiseGate(threshold_db=-40, ratio=8, attack_ms=0.3, release_ms=30), HighpassFilter(45),
                   LowShelfFilter(110, 2), PeakFilter(450, -4, 1.0), PeakFilter(2800, 2, 1.0), LowpassFilter(10500),
                   Compressor(-18, 3, 3, 80)])
aL, aR = fx(post, aL), fx(post, aR)
ld = fx(Pedalboard([HighpassFilter(200), PeakFilter(1500, 3, 0.8), LowpassFilter(9000), Compressor(-22, 4, 3, 150)]), ld)

drm = drum_bus(kitmics, room=0.45, kick_db=3, snare_db=2, hat_db=-4, oh_db=-2)
drm = drm * (10 ** (-15 / 20) / rig.active_rms(drm.mean(0)))
brk_bus = brk_bus * (10 ** (-15 / 20) / rig.active_rms(brk_bus.mean(0)))
for name in ("drm", "brk_bus"):
    v = globals()[name]
    c = 10 ** ((-15 + 7) / 20)
    globals()[name] = c * np.tanh(v / c)

aL, aR, ld = at_level(aL, -18), at_level(aR, -18), at_level(ld, -17)
grit, sub, subk = at_level(grit, -22), at_level(sub, -20), at_level(subk, -21)
ac, hv, mb = at_level(ac, -21), at_level(hv, -21), at_level(mb, -20)
imp, rs, dn, sr_ = at_level(imp, -15), at_level(rs, -26), at_level(dn, -25), at_level(sr_, -28)
ld_echo = fx(Pedalboard([Delay(delay_seconds=SPB * 0.75, feedback=0.35, mix=1.0), LowpassFilter(4500)]), ld)
ac_echo = fx(Pedalboard([Delay(delay_seconds=SPB * 0.75, feedback=0.4, mix=1.0), HighpassFilter(300)]), ac)

mix = (pan(aL, -1.0) + pan(aR, 1.0) + pan(ld, 0.0) + pan(ld_echo * 0.3, 0.0) + pan(grit, 0) + pan(sub, 0)
       + pan(subk, 0) + drm + brk_bus + pan(imp, 0) + pan(dn, 0) + pan(ac, 0.15) + pan(ac_echo * 0.3, -0.5)
       + pan(hv, 0) + pan(sr_, -0.3) + pan(mb, 0.2) + pan(rs, 0))
mix += stereo_reverb(ld * 0.3 + dn * 0.3 + imp * 0.2 + mb * 0.6 + hv * 0.2 + sr_ * 0.3, room=0.8, damping=0.3) * 0.5
mix = rig.automate(mix, [(0, SECTIONS[0][2] - 0.2, -3)], ramp=0.5)

if __import__("os").environ.get("DEBUG"):
    rig.section_table({"gtrL": aL, "drums": drm, "break": brk_bus, "acid": ac, "hoover": hv, "box": mb, "grit": grit,
                       "impact": imp, "MIX": mix}, SECTIONS)

for kind, a, b, arg in glitches:
    if kind == "stutter":
        synth.stutter(mix, a, b, arg)
    elif kind == "silence":
        synth.silence(mix, a, b)
    else:
        synth.tape_stop(mix, a, b)
        synth.silence(mix, a + b, a + b + 0.05)

master = Pedalboard([HighpassFilter(22), LowShelfFilter(70, 1.0), PeakFilter(300, -1.5, 0.8), HighShelfFilter(9000, 1.0),
                     Compressor(-10, 2.0, 15, 150)])
finish(mix, OUT / "infernal_mutation", master, fade_s=1.0, target_rms_db=-11)
print("done ->", OUT / "infernal_mutation.mp3")
