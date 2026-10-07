"""Hearth — track 10. A village/pastoral piece in D Mixolydian, 6/8: fingerpicked acoustic guitar, a ten-string
lyre, flute and cello. Original material in the C418 manner (warm, unhurried, a little old).

Dotted quarter ~48 (eighth 144) with rubato. The guitar picks the same p-i-m-a figure throughout over a drone-ish
D / C / G harmony (the flat seventh is the colour); the lyre sings the tune first, the flute takes it an octave
lower and breathier; a B tune moves to E minor; the lyre is left alone for a moment; the cello carries B the second
time; a last full statement, and the guitar and lyre close on an open D.

Form (6/8 bars): intro 4 | A1 8 lyre | A2 8 flute | B1 8 | A3 8 flute+lyre | break 4 lyre alone | B2 8 cello |
A4 8 full | coda 6 + fermata.

Sample mapping notes (measured): the Ovation guitar sounds an octave below the MIDI note (send p+12); the lyre
sounds an octave above (send p to hear p+12; keys E3..C5 -> sounding E4..C6).
"""
from kit import *

H = Human(1066)
OVATION = str(E / "OvationGuitar/Ovation Guitar (mw1 for 12-string).sfz")

# ---------------------------------------------------------------- harmony (sounding pitches): guitar voicing low->high
CH = {
    "D":     ns("D3 A3 D4 F#4"),
    "Dsus4": ns("D3 A3 D4 G4"),
    "C":     ns("C3 G3 C4 E4"),
    "G/B":   ns("B2 G3 B3 D4"),
    "Am7":   ns("A2 E3 G3 C4"),
    "Em7":   ns("E2 B3 D4 G4"),
    "G":     ns("G2 D3 G3 B3"),
    "D/F#":  ns("F#2 D3 A3 D4"),
    "Csus2": ns("C3 G3 D4 G4"),
}
PROG_A = ["D", "C", "G/B", "D", "D", "C", "Am7", "D"]
PROG_B = ["Em7", "G", "D/F#", "C", "Em7", "G", "Am7", "Csus2"]

# (eighth, eighths, note) per bar; written octave
MEL_A = [
    [(0, 3, "A4"), (3, 2, "F#4"), (5, 1, "G4")],
    [(0, 3, "G4"), (3, 2, "E4"), (5, 1, "G4")],
    [(0, 2, "B4"), (2, 1, "A4"), (3, 3, "G4")],
    [(0, 6, "A4")],
    [(0, 2, "A4"), (2, 1, "B4"), (3, 2, "C5"), (5, 1, "B4")],
    [(0, 3, "G4"), (3, 3, "E4")],
    [(0, 2, "E4"), (2, 1, "G4"), (3, 2, "A4"), (5, 1, "G4")],
    [(0, 6, "D4")],
]
MEL_B = [
    [(0, 3, "B4"), (3, 2, "D5"), (5, 1, "E5")],
    [(0, 6, "D5")],
    [(0, 2, "A4"), (2, 1, "D5"), (3, 3, "F#5")],
    [(0, 4, "E5"), (4, 2, "C5")],
    [(0, 3, "G5"), (3, 2, "F#5"), (5, 1, "E5")],
    [(0, 3, "D5"), (3, 3, "B4")],
    [(0, 2, "C5"), (2, 1, "B4"), (3, 2, "A4"), (5, 1, "G4")],
    [(0, 6, "A4")],
]

SEC = {"intro": 0, "A1": 4, "A2": 12, "B1": 20, "A3": 28, "break": 36, "B2": 40, "A4": 48, "coda": 56}
END_BAR = 62
PROG = (["D", "C", "D", "C"] + PROG_A * 2 + PROG_B + PROG_A + ["D", "C", "D", "Dsus4"] + PROG_B + PROG_A
        + ["D", "C", "G/B", "C", "Dsus4", "D"])
assert len(PROG) == END_BAR

T = Tempo(rubato(144, drift=0.02, breath_every=8, breath=0.10, meter=6, rit_from=58, rit_to=62, rit=0.55),
          meter=6, lead_in=0.8)
tb = T.tb
FERMATA = 8.0
LENGTH = tb(END_BAR) + FERMATA + 3

guitar = Sampler(OVATION)
lyre = inst("lyre")
flute = inst("flute", legato=True)
cello = inst("cello_solo", legato=True)
celli = inst("celli")

PICK = [0, 2, 3, 1, 3, 2]                  # p a(top) ... in eighths over the bar


def gnote(p, start, dur, vel):
    s = start + H.t(0.008)
    guitar.note(p + 12, s, s + dur, H.v(vel, 4))


def pick(bar, vel=58, pattern=PICK, strum=False):
    v = CH[PROG[bar]]
    end = tb(bar + 1) + 0.25
    if strum:                              # rolled chord on 1 and 4
        for half in (0, 3):
            for i, p in enumerate(v):
                gnote(p, tb(bar, half) + 0.025 * i, end - tb(bar, half), vel + 2 - (half == 3) * 6)
        return
    for i, k in enumerate(pattern):
        if k is None:
            continue
        st = tb(bar, i)
        gnote(v[k], st, end - st, vel + (6 if i == 0 else 0) - (2 if i % 3 else 0))


def line(target, bar0, mel, vel=64, up=0, lag=0.02, art=1.0):
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + lag + H.t(0.008)
            en = tb(bar0 + i, b + d * art)
            target.note(n(nm) + up, st, en, H.v(vel + (5 if b == 0 else 0)))


def lyre_line(bar0, mel, vel=78):
    """Lyre sounds an octave above the key; plucked so each note just rings."""
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + 0.015 + H.t(0.008)
            lyre.note(n(nm), st, st + 3.0, H.v(vel + (6 if b == 0 else 0)))


def lyre_plucks(bar, eighths=(2, 4), vel=62):
    v = CH[PROG[bar]]
    for e, p in zip(eighths, (v[2], v[3])):
        q = p - 12                         # sounding one octave above the guitar's upper voices
        while q < n("E3"):
            q += 12
        while q > n("C5"):
            q -= 12
        lyre.note(q, tb(bar, e) + H.t(0.008), tb(bar, e) + 2.0, H.v(vel))


def drone(bar0, bars, root="D2", fifth="A2", vel=60):
    for b in range(bar0, bar0 + bars, 2):
        for p in (n(root), n(fifth)):
            celli.note(p, tb(b) - 0.05, tb(min(b + 2, END_BAR)) + 0.1, vel)


# --- intro: guitar alone
for i in range(4):
    pick(SEC["intro"] + i, vel=56)

# --- A1: lyre tune (an octave above written)
for i in range(8):
    pick(SEC["A1"] + i, vel=56)
lyre_line(SEC["A1"], MEL_A)

# --- A2: flute, low and breathy; lyre plucks off-beats; cello drone enters
for i in range(8):
    pick(SEC["A2"] + i, vel=58)
    lyre_plucks(SEC["A2"] + i)
line(flute, SEC["A2"], MEL_A, vel=66)
drone(SEC["A2"], 8, vel=52)

# --- B1: to E minor; flute B tune, lyre answers, guitar rolls the chords
for i in range(8):
    pick(SEC["B1"] + i, vel=60, strum=(i % 2 == 1))
line(flute, SEC["B1"], MEL_B, vel=72)
for i in range(8):
    if i % 2 == 1:
        lyre_plucks(SEC["B1"] + i, eighths=(3, 5), vel=66)
for i, rt in enumerate(["E2", "G2", "F#2", "C2", "E2", "G2", "A2", "C2"]):
    celli.note(n(rt), tb(SEC["B1"] + i) - 0.05, tb(SEC["B1"] + i + 1) + 0.1, 56)

# --- A3: flute and lyre together (lyre an octave up)
for i in range(8):
    pick(SEC["A3"] + i, vel=62)
line(flute, SEC["A3"], MEL_A, vel=76, up=12)
lyre_line(SEC["A3"], MEL_A, vel=82)
drone(SEC["A3"], 8, vel=60)

# --- break: the lyre alone, rising arpeggios
ARP = {"D": ns("D4 F#4 A4 C5 A4 F#4"), "C": ns("C4 E4 G4 C5 G4 E4"), "Dsus4": ns("D4 G4 A4 C5 A4 G4")}
for i in range(4):
    bar = SEC["break"] + i
    for k, p in enumerate(ARP[PROG[bar]]):
        lyre.note(p, tb(bar, k) + H.t(0.006), tb(bar, k) + 2.5, H.v(70 - 2 * k + (8 if k == 0 else 0)))

# --- B2: the cello carries B; flute counter-line of long notes
for i in range(8):
    pick(SEC["B2"] + i, vel=58)
line(cello, SEC["B2"], MEL_B, vel=74, up=-12)
COUNTER_B = [[(0, 6, "G5")], [(0, 6, "F#5")], [(0, 6, "F#5")], [(0, 6, "G5")],
             [(0, 6, "B5")], [(0, 6, "B5")], [(0, 3, "A5"), (3, 3, "G5")], [(0, 6, "E5")]]
line(flute, SEC["B2"], COUNTER_B, vel=56, art=0.95)

# --- A4: full — flute up, lyre, cello on the bass line, guitar rolling
for i in range(8):
    pick(SEC["A4"] + i, vel=64, strum=(i in (3, 7)))
    if i not in (3, 7):
        lyre_plucks(SEC["A4"] + i, vel=58)
line(flute, SEC["A4"], MEL_A, vel=80, up=12)
for i, rt in enumerate(["D3", "C3", "B2", "A2", "D3", "C3", "A2", "D3"]):
    cello.note(n(rt), tb(SEC["A4"] + i) + 0.02, tb(SEC["A4"] + i + 1) - 0.02, 64)
drone(SEC["A4"], 8, vel=58)

# --- coda: guitar thins out, flute remembers the first two bars, lyre closes on an open D
for i in range(6):
    pick(SEC["coda"] + i, vel=54 - 2 * i, pattern=PICK if i < 4 else [0, None, 2, None, 3, None])
line(flute, SEC["coda"], MEL_A[:2], vel=60, up=12)
drone(SEC["coda"], 6, vel=48)
fs = tb(END_BAR)
for i, p in enumerate(ns("D2 A2 D3 F#3 A3 D4")):
    gnote(p, fs + 0.05 * i, FERMATA, 60 - 2 * i)
for k, p in enumerate(ns("A3 D4 F#4 A4")):
    lyre.note(p, fs + 0.9 + 0.18 * k, fs + FERMATA, 70 - 4 * k)
celli.note(n("D2"), fs - 0.1, fs + FERMATA - 2, 46)

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in SEC.items()) + f"  end {fs:.1f}")
gt = guitar.render(LENGTH)
ly = lyre.render(LENGTH)
fl = flute.render(LENGTH)
vc = cello.render(LENGTH)
cl = celli.render(LENGTH)

gt = rig.fx2(Pedalboard([HighpassFilter(70), PeakFilter(200, 1.5, 0.9), PeakFilter(2500, -1.5, 1.0),
                         HighShelfFilter(8000, -2), Compressor(-24, 2.0, 15, 200)]), gt)
ly = rig.fx2(Pedalboard([HighpassFilter(180), PeakFilter(3500, 1.5, 0.8), LowpassFilter(10000)]), ly)
fl = rig.fx2(Pedalboard([HighpassFilter(220), PeakFilter(3000, -1.5, 0.8), LowpassFilter(9000)]), fl)
vc = rig.fx2(Pedalboard([HighpassFilter(60), PeakFilter(2500, -2, 0.8), LowpassFilter(6000)]), vc)
cl = rig.fx2(Pedalboard([HighpassFilter(45), LowpassFilter(1800)]), cl)

gt = rig.pan(rig.at_level(gt.mean(0), -22.5), -0.25) + rig.at_level(gt, -30)
ly = rig.at_level(ly, -22)
fl = rig.at_level(fl, -21)
vc = rig.at_level(vc, -23)
cl = rig.at_level(cl, -31)
ly = rig.pan(ly.mean(0), 0.3) * 0.7 + ly * 0.3
fl = rig.pan(fl.mean(0), 0.1) * 0.8 + fl * 0.2

dry = gt + ly + fl + vc + cl
room = (rig.hall(gt + ly, decay=2.0, size=20, predelay=14, high_cut=7000, early=20, late=60)
        + rig.hall(fl + vc + cl, decay=2.8, size=28, predelay=22, high_cut=6000, early=12, late=80))
mix = dry + room

sections = [(k, tb(v), tb(list(SEC.values())[i + 1]) if i + 1 < len(SEC) else LENGTH) for i, (k, v) in
            enumerate(SEC.items())]
master(mix, "10_hearth", sections=sections,
       stems={"guitar": gt, "lyre": ly, "flute": fl, "cello": vc, "celli": cl}, fade_s=3.0,
       tape_kw={"wow_cents": 3.0, "flutter_cents": 1.0})
