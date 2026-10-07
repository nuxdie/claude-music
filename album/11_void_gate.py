"""Void Gate — track 11. The End / the boss. Original material in the manner of C418.

E minor, 110 BPM, 4/4. A relentless Surge saw arpeggio carries the whole fight; around it an orchestra of
tremolo strings, horns, trombones, timpani and a low male choir builds in waves. A Phrygian bridge (Em <-> F)
winds the tension up to a climax with the tune in octaves over a distorted saw layer and full choir. One last
hit, then the void: a celesta and a lone sine remember the tune, a step lower each time, and fall away.

Form (bars): intro 8 | A 16 | break 8 | B 16 | bridge 8 | climax 16 | hit 2 | void 18 (~66 BPM).
"""
import math

from kit import *  # noqa: F401,F403
from kit import rig, SR, np, inst, n, ns, Tempo, Human, surge_pluck, surge_pad, surge_bass, voice, master, rave
from kit import Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Delay, Distortion, Chorus

H = Human(1111)
NAME = "11_void_gate"

SEC = {"intro": 0, "A": 8, "break": 24, "B": 32, "bridge": 48, "climax": 56, "hit": 72, "void": 74, "end": 92}


def bpm(b):
    bar = b / 4
    tp = 110 * (1 + 0.004 * math.sin(2 * math.pi * b / 31))
    if bar >= SEC["hit"]:
        tp *= max(0.6, 1 - 0.4 * (bar - SEC["hit"]) / 2)
    if bar >= SEC["void"] + 12:
        tp *= max(0.75, 1 - 0.25 * (bar - SEC["void"] - 12) / 6)
    return tp


T = Tempo(bpm, meter=4, lead_in=0.6)
tb = T.tb
LENGTH = tb(SEC["end"]) + 9.0

# ---------------------------------------------------------------- harmony
CHORD = {"Em": (4, [0, 3, 7]), "C": (0, [0, 4, 7]), "Am": (9, [0, 3, 7]), "B": (11, [0, 4, 7]),
         "D": (2, [0, 4, 7]), "F": (5, [0, 4, 7]), "G": (7, [0, 4, 7]), "Bsus": (11, [0, 5, 7])}
PROG_A = ["Em", "Em", "C", "C", "Am", "Am", "B", "B"]
PROG_A2 = ["Em", "C", "Am", "B", "Em", "C", "D", "B"]
PROG_BR = ["Em", "F", "Em", "F", "Am", "F", "Bsus", "B"]
PROG_CL = ["Em", "C", "G", "D", "Am", "C", "B", "B"]
PROG = (["Em", "Em", "C", "C", "Em", "Em", "Bsus", "B"] + PROG_A + PROG_A2 + PROG_A + PROG_A + PROG_A2 + PROG_BR
        + PROG_CL + PROG_CL[:7] + ["Em"] + ["Em", "Em"] + ["Em", "C", "Am", "B"] * 4 + ["Em", "Em"])
assert len(PROG) == SEC["end"], len(PROG)


def tones(ch, lo):
    """Chord tones from MIDI `lo` upward (lo = lowest allowed root region)."""
    r, iv = CHORD[ch]
    root = lo + ((r - lo) % 12)
    return [root + i for i in iv]


def arp_pool(ch):
    r, i3, i5 = tones(ch, n("E3") - 2)
    return [r - 12, r, i5, r + 12, i3 + 12, i5 + 12, r + 24]


ARP_FULL = [1, 3, 4, 5, 3, 4, 2, 4, 1, 3, 4, 6, 5, 4, 3, 2]
ARP_LOW = [0, 2, 1, 2, 3, 2, 1, 2, 0, 2, 1, 2, 4, 3, 2, 1]
ARP_8 = [1, None, 3, None, 4, None, 3, None, 1, None, 3, None, 5, None, 4, None]

# ---------------------------------------------------------------- instruments
arp = surge_pluck(cutoff=9000.0, decay=0.32, release=0.18, shape=0.0, detune=9.0, voices=2, vol=-4.0)
arp2 = surge_pluck(cutoff=9000.0, decay=0.22, release=0.12, shape=0.35, detune=4.0, voices=1, vol=-6.0)
bass = surge_bass(cutoff=520.0, shape=0.0, attack=0.005, release=0.12)
dist = surge_pad(cutoff=2600.0, attack=0.4, release=1.5, detune=22.0, voices=5, reso=18.0)
drone = surge_pad(cutoff=420.0, attack=4.0, release=6.0, detune=10.0, voices=3)
trem = inst("strings_trem")
strs = inst("strings")
horns = inst("horns")
bones = inst("trombones")
choir_m = inst("choir_m")
choir = inst("choir")
timp = inst("timpani")
roll = inst("timp_roll")
celesta = inst("celesta")
low_str = inst("basses")


def bar_t(bar):
    return tb(bar), tb(bar + 1)


# ---- arpeggio
def arp_bar(bar, pattern, vel, synth=arp, octave=0):
    pool = arp_pool(PROG[bar])
    for i, k in enumerate(pattern):
        if k is None:
            continue
        st = tb(bar, i * 0.25) + H.t(0.002)
        acc = 14 if i % 4 == 0 else 0
        synth.note(pool[k] + octave, st, st + T.t(bar * 4 + i * 0.25 + 0.22) - T.t(bar * 4 + i * 0.25), vel + acc)


for bar in range(SEC["intro"], SEC["hit"]):
    if bar < SEC["intro"] + 4:
        arp_bar(bar, ARP_LOW, 70)
    elif bar < SEC["A"]:
        arp_bar(bar, ARP_LOW if bar % 2 else ARP_FULL, 80)
    elif SEC["break"] <= bar < SEC["B"]:
        arp_bar(bar, ARP_8, 72)
    else:
        arp_bar(bar, ARP_FULL, 92)
        if bar >= SEC["climax"] or (SEC["B"] + 8 <= bar < SEC["bridge"]):
            arp_bar(bar, ARP_FULL[8:] + ARP_FULL[:8], 84, synth=arp2, octave=12)
# void: the arpeggio's ghost, eighths, thinning out
for i, bar in enumerate(range(SEC["void"] + 2, SEC["void"] + 10)):
    pat = ARP_8 if i < 4 else [1, None, None, None, 4, None, None, None, None, None, 3, None, None, None, None, None]
    arp_bar(bar, pat, 54 - 3 * i)

# ---- bass: driving eighths on the root
for bar in range(SEC["A"], SEC["hit"]):
    if SEC["break"] <= bar < SEC["B"]:
        continue
    r = tones(PROG[bar], n("E1"))[0]
    for e in range(8):
        st = tb(bar, e * 0.5)
        oc = 12 if (e % 4 == 3 and bar >= SEC["B"]) else 0
        bass.note(r + oc, st, st + 0.18, 100 if e % 2 == 0 else 84)

# ---- drone (intro + break + void)
for bar in list(range(0, SEC["A"])) + list(range(SEC["break"], SEC["B"])) + list(range(SEC["void"], SEC["end"])):
    r = tones(PROG[bar], n("E2"))[0]
    drone.note(r - 12, tb(bar) - 0.02, tb(bar + 1) + 0.05, 90)
    drone.note(r - 5, tb(bar) - 0.02, tb(bar + 1) + 0.05, 70)


# ---- strings: tremolo chords; sustained high line in climax
def voicing(ch, lo=n("E3")):
    t = tones(ch, lo - 2)
    return [t[0], t[1], t[2], t[0] + 12, t[1] + 12]


for bar in range(SEC["A"], SEC["hit"]):
    if SEC["break"] <= bar < SEC["B"]:
        continue
    s, e = bar_t(bar)
    v = {SEC["A"]: 62, SEC["B"]: 78, SEC["bridge"]: 84, SEC["climax"]: 104}
    vel = [v[k] for k in sorted(v) if k <= bar][-1]
    if SEC["bridge"] <= bar < SEC["climax"]:
        vel += (bar - SEC["bridge"]) * 3
    for p in voicing(PROG[bar]):
        trem.note(p, s + H.t(0.006), e + 0.05, H.v(vel))
    if bar >= SEC["climax"]:
        for p in tones(PROG[bar], n("E5") - 3)[:2]:
            strs.note(p + 12, s, e + 0.05, 96)
for bar in range(SEC["B"], SEC["hit"]):
    r = tones(PROG[bar], n("E1") + 4)[0]
    low_str.note(r, tb(bar) + 0.01, tb(bar + 1) + 0.05, 90 if bar < SEC["climax"] else 110)

# ---- the tune (horns); octaves with strings and trombones at the climax
MEL1 = [[(0, 2, "E4"), (2, 1, "G4"), (3, 1, "B4")], [(0, 3, "A4"), (3, 1, "G4")],
        [(0, 2, "G4"), (2, 1, "E4"), (3, 1, "C5")], [(0, 4, "B4")],
        [(0, 2, "A4"), (2, 1, "C5"), (3, 1, "E5")], [(0, 3, "D5"), (3, 1, "C5")],
        [(0, 2, "B4"), (2, 1, "A4"), (3, 1, "F#4")], [(0, 2, "F#4"), (2, 2, "D#4")]]
MEL2 = [[(0, 3, "E5"), (3, 1, "D5")], [(0, 2, "C5"), (2, 1, "B4"), (3, 1, "G4")],
        [(0, 2, "A4"), (2, 2, "C5")], [(0, 4, "B4")],
        [(0, 1, "G4"), (1, 1, "B4"), (2, 2, "E5")], [(0, 2, "E5"), (2, 2, "C5")],
        [(0, 2, "D5"), (2, 1, "F#4"), (3, 1, "A4")], [(0, 4, "B4")]]
MEL_CL = [[(0, 2, "E5"), (2, 1, "D5"), (3, 1, "B4")], [(0, 3, "C5"), (3, 1, "E5")],
          [(0, 2, "D5"), (2, 1, "B4"), (3, 1, "G4")], [(0, 4, "A4")],
          [(0, 2, "C5"), (2, 1, "E5"), (3, 1, "A5")], [(0, 3, "G5"), (3, 1, "E5")],
          [(0, 2, "F#5"), (2, 1, "D#5"), (3, 1, "B4")], [(0, 4, "B4")]]
MEL_CL2 = MEL_CL[:7] + [[(0, 4, "E5")]]


def play(synth, bar0, mel, vel, shift=0, legato=0.08, lag=0.0):
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + lag + H.t(0.008)
            en = tb(bar0 + i, b + d) + legato
            synth.note(n(nm) + shift, st, en, H.v(vel + (6 if b == 0 else 0)))


play(horns, SEC["A"], MEL1, 74)
play(horns, SEC["A"] + 8, MEL2, 78)
play(horns, SEC["B"], MEL1, 88)
play(horns, SEC["B"] + 8, MEL2, 94)
play(strs, SEC["B"] + 8, MEL2, 70, shift=12)
for k, mel in ((0, MEL_CL), (8, MEL_CL2)):
    b0 = SEC["climax"] + k
    play(horns, b0, mel, 112, shift=-12 if k == 0 else 0)
    play(horns, b0, mel, 104, shift=0 if k == 0 else -12)
    play(bones, b0, mel, 104, shift=-12)
    play(strs, b0, mel, 104, shift=12)

# bridge: low brass stabs on the Phrygian move, horns call
for bar in range(SEC["bridge"], SEC["climax"]):
    ch = PROG[bar]
    for p in tones(ch, n("E2")):
        bones.note(p, tb(bar), tb(bar, 1.5), 80 + (bar - SEC["bridge"]) * 4)
        bones.note(p, tb(bar, 2.5), tb(bar, 4) - 0.05, 72 + (bar - SEC["bridge"]) * 4)
for i in range(0, 8, 2):
    bar = SEC["bridge"] + i
    horns.note(n("E4"), tb(bar, 1), tb(bar, 3), 90 + i * 3)
    horns.note(n("F4"), tb(bar + 1, 1), tb(bar + 1, 3.5), 94 + i * 3)

# ---- choirs
CHOIR_BARS = list(range(4, SEC["A"])) + list(range(SEC["break"], SEC["hit"]))
for bar in CHOIR_BARS:
    t = tones(PROG[bar], n("G2") + 2)
    vel = 70 if bar < SEC["bridge"] else 96
    for p in (t[0], t[2], t[0] + 12):
        if p < n("G2"):
            p += 12
        choir_m.note(p, tb(bar) - 0.08, tb(bar + 1) + 0.1, vel)
    if bar >= SEC["climax"]:
        for p in tones(PROG[bar], n("G4") - 2):
            choir.note(p, tb(bar) - 0.08, tb(bar + 1) + 0.1, 104)

# ---- timpani
for bar in range(SEC["A"], SEC["hit"]):
    if SEC["break"] <= bar < SEC["B"]:
        continue
    r = tones(PROG[bar], n("C2"))[0]
    if r > n("G2"):
        r -= 12
    if r < n("C2"):
        r += 12
    big = bar >= SEC["climax"]
    timp.note(r, tb(bar), tb(bar, 1), 96 if big else 82)
    if bar >= SEC["B"]:
        timp.note(r, tb(bar, 2.5), tb(bar, 3), 76 if big else 64)
        timp.note(r, tb(bar, 3), tb(bar, 4), 88 if big else 72)
    if big and bar % 2:
        for s in (3.25, 3.5, 3.75):
            timp.note(r + 7 if r + 7 <= n("C4") else r, tb(bar, s), tb(bar, s + 0.25), 90)
# rolls into the A, B, bridge, climax
for bar0, nb, v in ((SEC["A"] - 2, 2, 70), (SEC["B"] - 2, 2, 80), (SEC["bridge"] + 4, 4, 92), (SEC["climax"] - 1, 1, 110)):
    roll.note(n("E2"), tb(bar0), tb(bar0 + nb) - 0.03, v)
# ---- the final hit
hit = tb(SEC["hit"])
for p in (n("E2"), n("B2")):
    timp.note(p, hit, hit + 2, 120)
for p in ns("E2 B2 E3 G3"):
    bones.note(p, hit, hit + 1.6, 120)
for p in ns("E3 B3 E4 G4 B4 E5"):
    trem.note(p, hit, hit + 1.4, 120)
    horns.note(p, hit, hit + 1.5, 116) if p <= n("E5") else None
for p in ns("E3 B3 E4"):
    choir.note(p, hit, hit + 2.0, 110)
bass.note(n("E1"), hit, hit + 1.5, 120)

# ---- the void: celesta + lone sine remember the tune, a step lower each time
v0 = SEC["void"] + 2
celesta_mel = []
sine_mel = []
for k, (mel, sh) in enumerate(((MEL1[:4], 12), (MEL1[4:], 10), (MEL1[:3], 7))):
    b0 = v0 + 4 * k
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(b0 + i, b) + H.t(0.015)
            celesta.note(n(nm) + sh, st, st + 2.5, H.v(60 - 6 * k))
            sine_mel.append((n(nm) + sh - 12, st + 0.03, tb(b0 + i, b + d) - 0.03, 0.5 * (1 - 0.15 * k)))
# last: a single E falling to D#, then nothing
lt = tb(v0 + 14)
celesta.note(n("E5"), lt, lt + 4, 46)
sine_mel.append((n("E4"), lt + 0.05, lt + 3.0, 0.4))
sine_mel.append((n("D#4"), lt + 3.0, tb(SEC["end"]) + 3, 0.32))
drone.note(n("E1"), tb(SEC["end"] - 2), tb(SEC["end"]) + 3, 70)

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in SEC.items()))


def svf_curve(x2, keys, q=0.9):
    """Time-varying lowpass on a stereo signal; keys = [(bar, Hz)] interpolated exponentially in time."""
    tt = np.arange(x2.shape[1]) / SR
    ts = [tb(b) for b, _ in keys]
    fc = np.exp(np.interp(tt, ts, [math.log(f) for _, f in keys])).astype(np.float32)
    return np.stack([rave.svf(c, fc, q, "lp") for c in x2]).astype(np.float32)


A = arp.render(LENGTH)
A2 = arp2.render(LENGTH)
A = svf_curve(A, [(0, 260), (4, 900), (8, 2600), (24, 3200), (24.5, 900), (31, 1400), (32, 2800), (48, 3600),
                  (55.5, 7500), (72, 8000), (72.2, 1200), (SEC["void"] + 2, 1600), (SEC["end"], 900)], q=1.1)
A2 = svf_curve(A2, [(0, 3000), (56, 3000), (64, 7000), (72, 7000)])
B = bass.render(LENGTH)
DR = drone.render(LENGTH)
TR, ST, HN, BN = trem.render(LENGTH), strs.render(LENGTH), horns.render(LENGTH), bones.render(LENGTH)
CM, CH = choir_m.render(LENGTH), choir.render(LENGTH)
TP = timp.render(LENGTH) + roll.render(LENGTH)
CE = celesta.render(LENGTH)
LS = low_str.render(LENGTH)
SN = voice(sine_mel, LENGTH, harm=(1.0, 0.12), vib=10, glide=0.06, att=0.12, rel=1.2, seed=3)

for bar in range(SEC["climax"], SEC["hit"]):
    for p in tones(PROG[bar], n("E3") - 2):
        dist.note(p, tb(bar) - 0.02, tb(bar + 1) + 0.02, 100)
D = dist.render(LENGTH)
D = rig.fx2(Pedalboard([HighpassFilter(150), Distortion(16), LowpassFilter(3800), Chorus(0.5, 0.3, 8, 0, 0.5)]), D)

A = rig.fx2(Pedalboard([HighpassFilter(90), Delay(T.t(0.75) - T.t(0), 0.28, 0.22)]), A)
A2 = rig.fx2(Pedalboard([HighpassFilter(300), Delay(T.t(0.5) - T.t(0), 0.25, 0.25)]), A2)
B = rig.fx2(Pedalboard([LowpassFilter(900), Compressor(-20, 3, 5, 80)]), B)
B = np.stack([B.mean(0)] * 2)
TP = rig.fx2(Pedalboard([HighpassFilter(30), PeakFilter(90, 3, 1.0)]), TP)
CE = rig.fx2(Pedalboard([HighpassFilter(200)]), CE)
SN = rig.pan(rig.fx(Pedalboard([LowpassFilter(3000)]), SN), 0.0)
DR = rig.fx2(Pedalboard([HighpassFilter(30), LowpassFilter(1200)]), DR)

A = rig.at_level(A, -21)
A2 = rig.at_level(A2, -29)
B = rig.at_level(B, -23)
D = rig.at_level(D, -27)
DR = rig.at_level(DR, -30)
TR = rig.at_level(TR, -22)
ST = rig.at_level(ST, -24)
HN = rig.at_level(HN, -19)
BN = rig.at_level(BN, -23)
CM = rig.at_level(CM, -26)
CH = rig.at_level(CH, -26)
TP = rig.at_level(TP, -19)
CE = rig.at_level(CE, -29)
LS = rig.at_level(LS, -25)
SN = rig.at_level(SN, -31)

# waves: the arpeggio and synths swell section by section
WAVE = [(tb(0), tb(SEC["A"]), -4.0), (tb(SEC["A"]), tb(SEC["break"]), -2.0), (tb(SEC["break"]), tb(SEC["B"]), -4.0),
        (tb(SEC["bridge"]), tb(SEC["climax"]), 1.0), (tb(SEC["climax"]), tb(SEC["hit"]), 2.0)]
A = rig.automate(A, WAVE, ramp=1.5)
B = rig.automate(B, WAVE, ramp=1.5)
orch_wave = [(tb(SEC["A"]), tb(SEC["break"]), -1.5), (tb(SEC["climax"]), tb(SEC["hit"]), 1.0)]

# pan the orchestra a little
HN = HN * np.array([[0.85], [1.0]], dtype=np.float32)
BN = BN * np.array([[1.0], [0.8]], dtype=np.float32)

orch = rig.automate(TR + ST + HN + BN + CM + CH + TP + LS, orch_wave, ramp=1.5)
synth = A + A2 + B + D + DR
void = CE + SN
dry = orch + synth + void
wet = (rig.hall(orch, decay=3.4, size=45, predelay=24, high_cut=6500, early=20, late=80)
       + rig.hall(A + A2 + D, decay=2.4, size=30, predelay=12, high_cut=7000, early=8, late=60) * 0.7
       + rig.hall(void + DR, decay=7.5, size=60, predelay=60, high_cut=5000, early=4, late=100) * 1.2)
mix = dry + wet

sections = [(k, tb(v), tb(list(SEC.values())[i + 1]) if i + 1 < len(SEC) else LENGTH)
            for i, (k, v) in enumerate(SEC.items())]
master(mix, NAME, sections=sections,
       stems={"arp": A, "orch": orch, "horns": HN, "choir": CM + CH, "timp": TP, "void": void, "drone": DR},
       fade_s=5.0, target_rms_db=-16.0, tape_kw={"wow_cents": 3.0, "hiss_db": -68.0})
