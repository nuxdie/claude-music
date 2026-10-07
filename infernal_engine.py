"""'Infernal Engine' — an industrial-metal instrumental in the spirit of Mick Gordon's DOOM scores. E Phrygian, 132 BPM.

Low-E 8-string guitars (tape-varispeed below the sampled range), kick locked to every guitar hit,
a distorted synth bass doubling the riffs, metallic industrial percussion, sub impacts, risers,
a 7/8 section, glitch stutters and tape stops.

Form: Intro(8) | Riff A(8) | Riff B 7/8(8) | Break(4) | Riff A + lead(8) | Breakdown(8) | Final(8) | End
"""
import random
from pathlib import Path

import numpy as np
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter,
                        HighShelfFilter, NoiseGate, Delay, Distortion, Gain)

import rig
import synth
from rig import SR, Track, Drums, amp, fx, fx2, pan, at_level, stereo_reverb, drum_bus, finish

BPM = 132
SPB = 60 / BPM
DOWN = 7                     # varispeed: 8-string low E (E1) from a 6-string library
OUT = Path(__file__).parent / "out_infernal"
OUT.mkdir(exist_ok=True)
rng = random.Random(2016)


def t(beat):
    return beat * SPB


def jit(sd=0.004):
    return rng.gauss(0, sd)


def vh(v, sd=4):
    return v + rng.gauss(0, sd)


gL, gR = Track("guitar"), Track("guitar")
lead = Track("guitar")
dr = Drums()
bass_notes, kicks_sub, metal, impacts, risers, drones = [], [], [], [], [], []
glitches = []                # (kind, start_s, end_or_dur_s, arg)

CH = {  # sounding pitches (8-string, low E1 = 28)
    "X": [28, 35, 40], "x": [28, 35], "O": [40, 47, 52], "F": [29, 36, 41], "B": [34, 41, 46], "G": [31, 38, 43],
}
ROOT = {"X": 28, "x": 28, "O": 40, "F": 29, "B": 34, "G": 31}


def hit(name, beat, vel, sd=0.003):
    dr.hit(name, t(beat) + jit(sd), vh(vel, 3))


def riff(b0, pattern, vel=118, kick=True, bass=True):
    """16th-note riff language: X E5, x palm-muted chug, O octave E5, F/B/G power chords, '-' hold, '.' choke."""
    steps = len(pattern)
    i = 0
    while i < steps:
        c = pattern[i]
        if c in CH:
            hold = 1
            while i + hold < steps and pattern[i + hold] == "-":
                hold += 1
            beat = b0 + i * 0.25
            muted = c == "x"
            dur = 0.2 if muted else hold * 0.25 - 0.03
            for tr, sd in ((gL, 0.003), (gR, 0.005)):   # tight double-tracking
                s0 = t(beat) + jit(sd)
                for k, p in enumerate(CH[c]):
                    tr.note(p, s0 + k * 0.004, s0 + t(dur), vh(vel - (8 if muted else 0)),
                            "mute_down" if muted else "down")
            if bass:
                bass_notes.append((ROOT[c], t(beat), t(beat + dur), vel))
            if kick:
                hit("kick", beat, 118)
                kicks_sub.append(t(beat))
            i += hold
        else:
            i += 1


A = ["X-.xx.xO.xx.F-.x", "X-.xx.xO.xx.B-G-"]
B = ["X-.x.xX-.x.xF-", "X-.x.xX-.x.xB."]            # 7/8: 14 sixteenths
BD = ["X--.....X--.x.xx", "B-----..F-----.x"]       # breakdown, half-time


def groove_A(b0, i, double_kick=False):
    if i % 2 == 0:
        hit("crash_l" if i % 4 == 0 else "crash_r", b0, 122)
    for q in range(4):
        hit("ride_bell", b0 + q, 100)
    hit("snare", b0 + 1, 125); hit("snare", b0 + 3, 125)
    if double_kick:
        for s in range(16):
            hit("kick", b0 + s * .25, 108)
            kicks_sub.append(t(b0 + s * .25))


def groove_B(b0, i):
    if i % 2 == 0:
        hit("crash_l", b0, 122)
    hit("snare", b0 + 1.5, 125); hit("snare", b0 + 3, 118)
    for q in range(7):
        hit("hh_closed", b0 + q * .5, 95 if q % 2 == 0 else 75)


def fill16(b0, beats=4, start=0):
    seq = ["snare"] * 4 + ["tom1"] * 4 + ["tom2"] * 4 + ["tom3"] * 4
    n = int(beats * 4)
    for k in range(n):
        hit(seq[int(k * len(seq) / n)], b0 + start + k * .25, 95 + k * 2)


# ---------------------------------------------------------------- arrangement
pos = 0.0

# 1. Intro: drone, industrial percussion, pulsing synth bass, riser, glitch, DROP
drones.append(([28, 40, 47], t(0), t(32) + 0.3, 900))
impacts.append(t(0))
for bar in range(8):
    b0 = pos + bar * 4
    if bar >= 2:
        for st, v in ((0, 1.0), (3, .6), (6, .8), (10, .7), (12, .9), (14, .5)):
            metal.append((t(b0 + st * .25) + jit(), v))
    if bar >= 4:
        for e in range(8):
            bass_notes.append((28, t(b0 + e * .5), t(b0 + e * .5 + .4), 50 + (bar - 4) * 18 + e * 2))
    if bar == 4:
        impacts.append(t(b0))
    if bar == 7:
        for k in range(8):
            hit("snare", b0 + k * .25, 70 + k * 6)
risers.append((t(pos + 20), t(pos + 30)))
glitches.append(("stutter", t(pos + 30), t(pos + 31), t(0.25)))
glitches.append(("stutter", t(pos + 31), t(pos + 32), t(0.125)))
pos += 32

# 2. Riff A
impacts.append(t(pos))
for i in range(8):
    riff(pos, A[i % 2])
    groove_A(pos, i)
    pos += 4

# 3. Riff B in 7/8
for i in range(8):
    riff(pos, B[i % 2])
    groove_B(pos, i)
    if i == 7:
        fill16(pos, beats=1.5, start=2)
    pos += 3.5

# 4. Break: one bar of riff, tape-stop, near-silence, then the build
riff(pos, A[0])
groove_A(pos, 0)
glitches.append(("tapestop", t(pos + 2), t(2), None))
pos += 4
drones.append(([28, 34], t(pos), t(pos + 12), 500))           # E + Bb: the tritone hum
for st in (0, 6, 10, 15):
    metal.append((t(pos + st * .25), 0.8))
pos += 4
risers.append((t(pos), t(pos + 8)))
for bar in range(2):
    b0 = pos + bar * 4
    for k in range(16):
        hit("snare", b0 + k * .25, 60 + bar * 30 + k * 2)
        bass_notes.append((28, t(b0 + k * .25), t(b0 + k * .25 + .2), 60 + bar * 30 + k * 2))
    hit("kick", b0, 110); hit("kick", b0 + 2, 110)
glitches.append(("stutter", t(pos + 7), t(pos + 7.5), t(0.125)))
glitches.append(("stutter", t(pos + 7.5), t(pos + 8), t(0.0625)))
pos += 8

# 5. Riff A with double kick and a lead on top
impacts.append(t(pos))
LEAD = [
    [(0, 1.5, 76, "b2v"), (1.5, .5, 77), (2, 2, 76, "v")],
    [(0, 1, 79), (1, 1, 77), (2, 1, 76), (3, 1, 74)],
    [(0, 3, 77, "b1v"), (3, 1, 80)],
    [(0, 4, 76, "v")],
    [(0, 1.5, 83, "b2v"), (1.5, .5, 82), (2, 2, 80, "v")],
    [(0, 1, 79), (1, 1, 77), (2, 2, 76, "v")],
    [(0, .5, 76), (.5, .5, 77), (1, .5, 80), (1.5, .5, 82), (2, 2, 83, "b1v")],
    [(0, 4, 88, "b2v")],
]


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


for i in range(8):
    riff(pos, A[i % 2], kick=False)
    groove_A(pos, i, double_kick=True)
    lead_line(pos, LEAD[i])
    pos += 4

# 6. Breakdown: half-time, huge stabs, impacts, dark pad
drones.append(([40, 47, 55, 59], t(pos), t(pos + 32) + 0.3, 1400))
for i in range(8):
    riff(pos, BD[i % 2], vel=124)
    if i % 4 == 0:
        impacts.append(t(pos))
    hit("crash_l" if i % 2 == 0 else "crash_r", pos, 125)
    hit("snare", pos + 2, 127)
    for q in range(4):
        hit("hh_open" if q % 2 else "ride_bell", pos + q, 90)
    if i == 7:
        fill16(pos, beats=2, start=2)
    pos += 4

# 7. Final: blast beat under riff A, then unison, glitch out
impacts.append(t(pos))
for i in range(8):
    riff(pos, A[i % 2], kick=(i >= 4))
    if i < 4:   # blast beat: kick and snare alternating 16ths, crash on quarters
        for s in range(16):
            hit("kick" if s % 2 == 0 else "snare", pos + s * .25, 115 if s % 2 == 0 else 105)
            if s % 2 == 0:
                kicks_sub.append(t(pos + s * .25))
        for q in range(4):
            hit("crash_l" if q % 2 == 0 else "crash_r", pos + q, 110)
    else:
        groove_A(pos, i)
    pos += 4
glitches.append(("stutter", t(pos - 2), t(pos - 1), t(0.125)))
glitches.append(("stutter", t(pos - 1), t(pos), t(0.03125)))

# 8. End: one last hit, let it ring, tape-stop into silence
riff(pos, "X---------------")
impacts.append(t(pos))
hit("crash_l", pos, 127); hit("crash_r", pos, 125)
glitches.append(("tapestop", t(pos + 3), 1.6, None))
END = t(pos + 3) + 1.6 + 0.5

# ---------------------------------------------------------------- render
print(f"{END:.1f}s. rendering guitars (varispeed -{DOWN}) / drums / synths...")
di_L, di_R = gL.render(END, down=DOWN), gR.render(END, down=DOWN)
di_lead = lead.render(END)
kit = dr.render(END)
grit, sub = synth.synth_bass([(p, s, e, v) for p, s, e, v in bass_notes], END)
subk = synth.sub_kick(kicks_sub, END)
mt = synth.metal_hits(metal, END)
imp = synth.impact(impacts, END)
rs = sum(synth.riser(a, b, END) for a, b in risers)
dn = sum(synth.drone(p, a, b, END, cutoff=c) for p, a, b, c in drones)

print("amps...")
# tight metal front end: gate the DI, trim lows and push mids into the amp (Tube Screamer trick)
pre = Pedalboard([NoiseGate(threshold_db=-48, ratio=10, attack_ms=0.5, release_ms=40), HighpassFilter(110),
                  PeakFilter(900, 6, 0.8)])
aL = amp(fx(pre, di_L), "JVM-OD2-RD-Cab", peak_in=0.7)
aR = amp(fx(pre, di_R), "Bug333-Lead-Cab", peak_in=0.7)
ld = amp(fx(Pedalboard([HighpassFilter(150), PeakFilter(900, 4, 0.8)]), di_lead), "JVM-OD2-RD-Cab", peak_in=0.6)
post = Pedalboard([NoiseGate(threshold_db=-40, ratio=8, attack_ms=0.3, release_ms=30), HighpassFilter(45),
                   LowShelfFilter(110, 3), PeakFilter(450, -4, 1.0), PeakFilter(2800, 2, 1.0), LowpassFilter(10500),
                   Compressor(-18, 3, 3, 80)])
aL, aR = fx(post, aL), fx(post, aR)
ld = fx(Pedalboard([HighpassFilter(200), PeakFilter(1500, 3, 0.8), LowpassFilter(9000), Compressor(-22, 4, 3, 150)]), ld)

drm = drum_bus(kit, room=0.45, kick_db=3, snare_db=2, hat_db=-4, oh_db=-2)
drm = drm * (10 ** (-14 / 20) / rig.active_rms(drm.mean(0)))
clip = 10 ** ((-14 + 7) / 20)
drm = clip * np.tanh(drm / clip)

aL, aR = at_level(aL, -17), at_level(aR, -17)
ld = at_level(ld, -17)
grit, sub, subk = at_level(grit, -21), at_level(sub, -19), at_level(subk, -20)
mt, imp, rs, dn = at_level(mt, -22), at_level(imp, -15), at_level(rs, -26), at_level(dn, -24)
ld_echo = fx(Pedalboard([Delay(delay_seconds=SPB * 0.75, feedback=0.35, mix=1.0), LowpassFilter(4500)]), ld)

mix = (pan(aL, -1.0) + pan(aR, 1.0) + pan(ld, 0.0) + pan(ld_echo * 0.3, 0.0) + pan(grit, 0) + pan(sub, 0)
       + pan(subk, 0) + drm + pan(imp, 0) + pan(dn, 0))
mix += np.stack([pan(mt, -0.4)[0] + pan(mt, 0.4)[0] * 0.3, pan(mt, 0.4)[1] + pan(mt, -0.4)[1] * 0.3])
mix += pan(rs, 0)
mix += stereo_reverb(ld * 0.3 + mt * 0.4 + dn * 0.3 + imp * 0.2, room=0.8, damping=0.3) * 0.5

SECTIONS = [("intro", 0, 32), ("riffA", 32, 64), ("riffB", 64, 92), ("break", 92, 108), ("A+lead", 108, 140),
            ("breakdown", 140, 172), ("final", 172, 204)]
if __import__("os").environ.get("DEBUG"):
    rig.section_table({"gtrL": aL, "lead": ld, "grit": grit, "sub": sub, "subkick": subk, "drums": drm, "metal": mt,
                       "impact": imp, "riser": rs, "drone": dn, "MIX": mix},
                      [(n, t(a), t(b)) for n, a, b in SECTIONS])

mix = rig.automate(mix, [(0, t(30), -3.5)], ramp=0.3)    # keep the intro back so the drop lands

for kind, a, b, arg in glitches:
    if kind == "stutter":
        synth.stutter(mix, a, b, arg)
    else:
        synth.tape_stop(mix, a, b)
        synth.silence(mix, a + b, a + b + 0.05)

master = Pedalboard([HighpassFilter(22), LowShelfFilter(70, 1.0), PeakFilter(300, -1.5, 0.8), HighShelfFilter(9000, 1.0),
                     Compressor(-10, 2.0, 15, 150)])
finish(mix, OUT / "infernal_engine", master, fade_s=0.5, target_rms_db=-11)
print("done ->", OUT / "infernal_engine.mp3")
