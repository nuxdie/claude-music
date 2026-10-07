"""Pebble Song — track 3 of Volume Gamma. Creative-mode mood (bright, curious, a little dreamy). Original material.

G Lydian / G major, 96 BPM. Rhodes broken chords in 8ths, a Surge saw-pluck 16th arpeggio sparkling an octave above,
a soft triangle-ish lead with delayed vibrato, sine sub bass, and tiny synthesized percussion (shaker, tick, felt kick).
The middle section drops the pulse, slows a touch and turns reflective (borrowed Eb / Ab major-7 chords under a high
Rhodes line and a slow pad) before the bright theme returns with the lead doubled in octaves.

Form (bars): intro 8 | A 16 | B 16 | middle 16 | A' 16 | outro 8.
"""
import math

from kit import *

h = Human(303)
NAME = "03_pebble_song"

# ---------------------------------------------------------------- harmony: (arp pool low->high, bass root, pad)
CH = {
    "Gmaj9":   (ns("G2 D3 F#3 A3 B3 D4"), n("G1"), ns("B3 D4 F#4 A4")),
    "A/G":     (ns("G2 E3 A3 C#4 E4 A4"), n("G1"), ns("A3 C#4 E4 G4")),
    "Em9":     (ns("E2 B2 G3 B3 D4 F#4"), n("E1"), ns("G3 B3 D4 F#4")),
    "Cmaj7#11": (ns("C3 G3 B3 E4 F#4 G4"), n("C2"), ns("B3 E4 F#4 G4")),
    "Cmaj7":   (ns("C3 G3 B3 C4 E4 G4"), n("C2"), ns("G3 B3 C4 E4")),
    "D":       (ns("D3 A3 D4 F#4 A4 D5"), n("D2"), ns("A3 D4 F#4 A4")),
    "Bm7":     (ns("B2 F#3 A3 B3 D4 F#4"), n("B1"), ns("F#3 A3 B3 D4")),
    "Em7":     (ns("E2 B2 G3 B3 D4 E4"), n("E1"), ns("G3 B3 D4 E4")),
    "Am7":     (ns("A2 E3 G3 A3 C4 E4"), n("A1"), ns("G3 A3 C4 E4")),
    "D/F#":    (ns("F#2 D3 A3 D4 E4 F#4"), n("F#1"), ns("F#3 A3 D4 E4")),
    "Gmaj7":   (ns("G2 D3 F#3 G3 B3 D4"), n("G1"), ns("F#3 G3 B3 D4")),
    "Ebmaj7":  (ns("Eb2 Bb2 G3 Bb3 D4 G4"), n("Eb1"), ns("G3 Bb3 D4 F4")),
    "Dsus":    (ns("D3 A3 D4 E4 G4 A4"), n("D2"), ns("G3 A3 D4 E4")),
    "Abmaj7#11": (ns("Ab2 Eb3 G3 C4 D4 Eb4"), n("Ab1"), ns("G3 C4 D4 Eb4")),
}
PA = ["Gmaj9", "A/G", "Em9", "Cmaj7#11"] * 2
PB = ["Cmaj7", "D", "Bm7", "Em7", "Am7", "D/F#", "Gmaj7", "A/G"]
PM = ["Em9", "Cmaj7", "Ebmaj7", "Dsus", "Em9", "Cmaj7", "Abmaj7#11", "A/G"]

SEC = {"intro": 0, "A": 8, "B": 24, "mid": 40, "A2": 56, "out": 72}
END = 80
PROG = PA + PA * 2 + PB * 2 + PM * 2 + PA * 2 + PA[:4] + ["Gmaj9", "A/G", "Gmaj9", "A/G"]
assert len(PROG) == END

MEL_A = [
    [(0, 1.5, "D5"), (1.5, 0.5, "B4"), (2, 2, "F#5")],
    [(0, 1, "E5"), (1, 1, "C#5"), (2, 2, "A4")],
    [(0, 1.5, "B4"), (1.5, 0.5, "G4"), (2, 1, "D5"), (3, 1, "F#5")],
    [(0, 3, "E5"), (3, 1, "F#5")],
    [(0, 1.5, "G5"), (1.5, 0.5, "F#5"), (2, 2, "D5")],
    [(0, 1, "C#5"), (1, 1, "E5"), (2, 2, "A5")],
    [(0, 1, "G5"), (1, 1, "F#5"), (2, 1, "E5"), (3, 1, "B4")],
    [(0, 4, "E5")],
]
MEL_B = [
    [(0, 2, "E5"), (2, 1, "G5"), (3, 1, "B5")],
    [(0, 2, "A5"), (2, 2, "F#5")],
    [(0, 1, "D5"), (1, 1, "F#5"), (2, 2, "B5")],
    [(0, 3, "G5"), (3, 1, "E5")],
    [(0, 2, "C5"), (2, 1, "E5"), (3, 1, "A5")],
    [(0, 2, "F#5"), (2, 1.5, "A5"), (3.5, 0.5, "G5")],
    [(0, 4, "F#5")],
    [(0, 2, "E5"), (2, 2, "C#5")],
]
MEL_MID = [
    [(0, 4, "B5")], [(0, 2, "G5"), (2, 2, "E5")], [(0, 3, "G5"), (3, 1, "Bb5")], [(0, 2, "A5"), (2, 2, "E5")],
    [(0, 3, "B5"), (3, 1, "D6")], [(0, 4, "E6")], [(0, 2, "Eb6"), (2, 2, "C6")], [(0, 4, "C#6")],
]


# ---------------------------------------------------------------- tempo: steady, middle relaxes, outro slows
def bpm(b):
    bar = b / 4
    tp = 96 * (1 + 0.006 * math.sin(2 * math.pi * b / 31))
    if SEC["mid"] - 1 <= bar < SEC["A2"]:
        w = min(1, (bar - SEC["mid"] + 1)) if bar < SEC["A2"] - 1 else (SEC["A2"] - bar)
        tp *= 1 - 0.07 * max(0, w)
    if bar > END - 3:
        tp *= max(0.6, 1 - 0.4 * (bar - END + 3) / 3)
    return tp


T = Tempo(bpm, lead_in=0.8)
tb = T.tb
LENGTH = tb(END) + 9

rhodes = inst("rhodes")
pluck = surge_pluck(cutoff=3200.0, decay=0.35, release=0.25, shape=0.0, detune=10.0, voices=2, vol=-8.0)
pad = surge_pad(cutoff=1100.0, attack=2.5, release=4.0, detune=12.0, voices=3)

# ---------------------------------------------------------------- Rhodes
R_PATS = {
    "flow": [0, 2, 3, 4, 5, 4, 3, 2],
    "rise": [0, 3, 1, 4, 2, 5, 3, 4],
    "sparse": [0, None, 3, None, 4, None, 5, None],
    "half": [0, None, None, None, 3, None, 4, None],
}


def rh_bar(bar, pat, vel=56):
    pool = CH[PROG[bar]][0]
    for i, k in enumerate(R_PATS[pat]):
        if k is None:
            continue
        st = tb(bar, i * 0.5) + h.t(0.007)
        acc = 8 if i == 0 else (3 if i == 4 else 0)
        rhodes.note(pool[k], st, tb(bar + 1) + 0.15 if k == 0 else st + 0.9, h.v(vel + acc - 4 * (i % 2)))
    rhodes.pedal(tb(bar) + 0.02, tb(bar + 1) - 0.01)


for bar in range(END):
    if bar < SEC["A"]:
        rh_bar(bar, "sparse" if bar < 4 else "flow", 50 + bar)
    elif bar < SEC["B"]:
        rh_bar(bar, "flow", 56)
    elif bar < SEC["mid"]:
        rh_bar(bar, "rise" if bar % 2 else "flow", 60)
    elif bar < SEC["A2"]:
        rh_bar(bar, "half", 48)
    elif bar < SEC["out"]:
        rh_bar(bar, "rise" if bar % 4 == 3 else "flow", 60)
    else:
        rh_bar(bar, "flow" if bar < END - 4 else ("sparse" if bar < END - 2 else "half"), 54 - (bar - SEC["out"]))

# middle: high Rhodes melody (bell register)
for i, notes in enumerate(MEL_MID * 2):
    bar = SEC["mid"] + i
    for b, d, nm in notes:
        st = tb(bar, b) + 0.02 + h.t(0.006)
        en = tb(bar, b + d)
        v = 58 if i < 8 else 62
        rhodes.note(n(nm), st, en + 0.3, h.v(v + (4 if b == 0 else 0)))
        if i >= 8:
            rhodes.note(n(nm) - 12, st + 0.015, en + 0.3, h.v(v - 12))

# final chord: G with A/G colour — G2 D3 A3 C#4 F#4 B4, let ring
fs = tb(END)
for i, nm in enumerate(["G1", "G2", "D3", "A3", "C#4", "F#4", "B4", "E5"]):
    rhodes.note(n(nm), fs + 0.06 * i, fs + 8, 56 - 2 * i)
rhodes.pedal(fs - 0.02, fs + 8)

# ---------------------------------------------------------------- pluck arp (16ths, above the Rhodes)
ARP16 = [0, 2, 4, 5, 3, 5, 4, 2, 1, 3, 5, 4, 2, 4, 3, 5]


def arp_bar(bar, vel=88, density=1.0):
    pool = [p + 12 for p in CH[PROG[bar]][0][1:]]
    for i, k in enumerate(ARP16):
        if density < 1 and i % 2 and h.r.random() > density:
            continue
        st = tb(bar, i * 0.25) + h.t(0.003)
        pluck.note(pool[k % len(pool)], st, st + 0.12, h.v(vel - (0 if i % 4 == 0 else 14), 5))


for bar in range(SEC["A"] + 4, SEC["mid"]):
    arp_bar(bar, density=0.5 if bar < SEC["A"] + 8 else 1.0)
for bar in range(SEC["A2"], SEC["out"] + 4):
    arp_bar(bar, density=1.0 if bar < SEC["out"] else 0.4)


# ---------------------------------------------------------------- lead
def mel(bar0, m, amp=0.5, octave=0):
    out = []
    for i, notes in enumerate(m):
        for b, d, nm in notes:
            out.append((n(nm) + octave, tb(bar0 + i, b) + 0.01, tb(bar0 + i, b + d) - 0.03, amp))
    return out


lead_n = (mel(SEC["A"], MEL_A) + mel(SEC["A"] + 8, MEL_A)
          + mel(SEC["B"], MEL_B) + mel(SEC["B"] + 8, MEL_B, 0.55)
          + mel(SEC["A2"], MEL_A, 0.5) + mel(SEC["A2"] + 8, MEL_A, 0.55))
lead_hi = mel(SEC["B"] + 8, MEL_B, 0.22, 12) + mel(SEC["A2"] + 8, MEL_A, 0.25, 12)
# outro: the first phrase once more, fragile
lead_n += mel(SEC["out"], MEL_A[:3], 0.38)

# ---------------------------------------------------------------- sub bass: dotted-quarter pulse on the root
sub_n = []
for bar in range(SEC["A"], SEC["out"] + 6):
    if SEC["mid"] <= bar < SEC["A2"]:
        sub_n.append((CH[PROG[bar]][1] + 12, tb(bar), tb(bar + 1) - 0.05, 0.42))
        continue
    r = CH[PROG[bar]][1] + 12
    for b, d in ((0, 1.4), (1.5, 0.9), (2.5, 1.4)):
        sub_n.append((r, tb(bar, b), tb(bar, b + d), 0.5 if b == 0 else 0.4))

# ---------------------------------------------------------------- pad (B half, middle, A2 swell)
for bar in list(range(SEC["B"] + 8, SEC["A2"] + 8)):
    for p in CH[PROG[bar]][2]:
        pad.note(p, tb(bar) - 0.05, tb(bar + 1) + 0.1, 85)


# ---------------------------------------------------------------- tiny percussion (synthesized)
def perc_render(length):
    nn = int(length * SR)
    shaker = np.zeros(nn, np.float32)
    tick = np.zeros(nn, np.float32)
    kick = np.zeros(nn, np.float32)
    nz = noise(int(0.08 * SR), 5)
    sh_src = rave.svf(nz, np.full(len(nz), 7500.0, np.float32), 1.2, "bp")
    for bar in range(SEC["A"] + 8, SEC["out"] + 4):
        if SEC["mid"] <= bar < SEC["A2"]:
            continue
        full = bar >= SEC["B"]
        for i in range(16):
            if not full and i % 2:
                continue
            st = tb(bar, i * 0.25) + h.t(0.004)
            a = (0.55 if i % 4 == 2 else 0.3 if i % 2 == 0 else 0.18) * h.r.uniform(0.8, 1.1)
            L = int((0.05 if i % 4 == 2 else 0.03) * SR)
            env = np.exp(-np.arange(L) / (L / 4)) * np.minimum(1, np.arange(L) / (0.004 * SR))
            i0 = int(st * SR)
            shaker[i0:i0 + L] += a * sh_src[:L] * env
        for b in (1, 3):                                   # wooden tick on 2 & 4
            i0 = int((tb(bar, b) + h.t(0.003)) * SR)
            L = int(0.03 * SR)
            tt = np.arange(L) / SR
            f = 1900 if b == 1 else 1750
            tick[i0:i0 + L] += 0.5 * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.006)
        if full or bar >= SEC["A2"]:                       # felt kick: 1, and the "and" of 2
            for b in ((0, 2.5) if bar % 2 == 0 else (0, 1.75, 2.5)):
                i0 = int(tb(bar, b) * SR)
                L = int(0.25 * SR)
                tt = np.arange(L) / SR
                f = 52 + 60 * np.exp(-tt / 0.03)
                kick[i0:i0 + L] += 0.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.09)
    return shaker, tick, kick


# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  A {tb(8):.1f}  B {tb(24):.1f}  mid {tb(40):.1f}  A2 {tb(56):.1f}  out {tb(72):.1f}")
rh = rhodes.render(LENGTH)
pl = pluck.render(LENGTH)
pd = pad.render(LENGTH)
lead = voice(lead_n, LENGTH, harm=(1, 0, 0.11, 0, 0.04), vib=13, glide=0.05, att=0.04, rel=0.35, seed=3)
lead_o = voice(lead_hi, LENGTH, harm=(1, 0.2), vib=10, att=0.05, rel=0.4, seed=4)
sub = voice(sub_n, LENGTH, harm=(1, 0.12), att=0.02, rel=0.15, seed=5)
shaker, tick, kick = perc_render(LENGTH)

rh = rig.fx2(Pedalboard([HighpassFilter(60), PeakFilter(300, -2, 0.9), HighShelfFilter(6000, -2),
                         Compressor(-24, 2, 15, 200)]), rh)
pl = rig.fx2(Pedalboard([HighpassFilter(400), LowpassFilter(6500), Delay(0.4688, 0.3, 0.25)]), pl)
pd = rig.fx2(Pedalboard([HighpassFilter(150), LowpassFilter(3500), Chorus(0.25, 0.3, 7, 0, 0.5)]), pd)
pd = rig.automate(pd, [(0, tb(SEC["B"] + 8), -60), (tb(SEC["B"] + 8), tb(SEC["mid"]), -8),
                       (tb(SEC["A2"]), LENGTH, -3)], ramp=3.0)
lead = rig.fx(Pedalboard([HighpassFilter(180), LowpassFilter(5000)]), lead)
sub = rig.fx(Pedalboard([LowpassFilter(180)]), sub)
shaker = rig.fx(Pedalboard([HighpassFilter(3000)]), shaker)

rh = rig.at_level(rh, -19)
pl = rig.at_level(pl, -28)
pd = rig.at_level(pd, -28)
lead_st = rig.pan(rig.at_level(lead, -20.5), 0.05) + rig.pan(rig.at_level(lead_o, -31), -0.3)
sub_st = rig.pan(rig.at_level(sub, -23), 0)
perc = (rig.pan(rig.at_level(shaker, -36), 0.35) + rig.pan(rig.at_level(tick, -37), -0.25)
        + rig.pan(rig.at_level(kick, -27), 0))
# pluck: auto-pan wobble
tt = np.arange(pl.shape[1]) / SR
w = 0.5 + 0.35 * np.sin(2 * np.pi * 0.11 * tt)
pl = np.stack([pl[0] * (1.4 - w), pl[1] * (0.6 + w)])

dry = rh + pl + pd + lead_st + sub_st + perc
wet = (rig.hall(rh + 0.5 * pl + 0.2 * perc, decay=2.2, size=26, predelay=18, high_cut=7000, early=15, late=70)
       + rig.hall(pd + lead_st, decay=4.5, size=40, predelay=35, high_cut=6000, early=5, late=90) * 0.8)
mix = dry + wet

sections = [("intro", 0, tb(8)), ("A", tb(8), tb(24)), ("B", tb(24), tb(40)), ("middle", tb(40), tb(56)),
            ("A2", tb(56), tb(72)), ("outro", tb(72), LENGTH)]
master(mix, NAME, sections, {"rhodes": rh, "pluck": pl, "pad": pd, "lead": lead_st, "sub": sub_st, "perc": perc},
       fade_s=4.0, target_rms_db=-18.0, tape_kw={"wow_cents": 4.0, "flutter_cents": 1.0, "hiss_db": -70})
