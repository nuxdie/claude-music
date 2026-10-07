"""Long Way Home — track 12, the credits piece. Original material in the manner of C418 ("Alpha").

D major, ~76 BPM, rubato. A grand piano alone with the album's first tune (MOTIF_HOME, track 1); an analog pad
and a sine sub join; a Rhodes takes the arpeggio while a sine lead sings a countermelody; the Birch tune (track 2)
comes back on a solo cello in E minor; a 3/4 interlude remembers the Lantern waltz (track 4) on celesta, harp and
music box; then a long build — drums, strings, an opening filter, the home tune stretched out on the lead — to
a climax of distorted saws, strings, choir and drums with the tune in octaves and the Birch tune answering in
B minor. Everything falls away; the piano plays the home tune once more and stops on Gmaj9, unresolved.

Form (bars): solo 12 | pads 12 | rhodes 12 | birch 12 | lantern 12 (3/4) | build 24 | climax 16 | fall 4 | coda 10.
"""
import math

from kit import *  # noqa: F401,F403
from kit import (rig, SR, np, inst, n, ns, Tempo, Human, surge_pad, voice, music_box, master, rave, shift,
                 MOTIF_HOME, MOTIF_BIRCH, MOTIF_LANTERN)
from kit import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Distortion, Chorus,
                 HighShelfFilter, LowShelfFilter)

H = Human(1212)
NAME = "12_long_way_home"

SEC = {"solo": 0, "pads": 12, "rhodes": 24, "birch": 36, "lantern": 48, "build": 60, "climax": 84, "fall": 100,
       "coda": 104, "end": 114}
METER = [3 if SEC["lantern"] <= b < SEC["build"] else 4 for b in range(SEC["end"] + 40)]
BEAT0 = np.concatenate([[0], np.cumsum(METER)])


def bar_of(beat):
    return int(np.searchsorted(BEAT0, beat, side="right") - 1)


def bpm(b):
    bar = bar_of(b)
    base = {"solo": 70, "pads": 75, "rhodes": 77, "birch": 74, "lantern": 86, "build": 79, "climax": 80,
            "fall": 74, "coda": 66}
    sec = [k for k, v in SEC.items() if v <= bar and k != "end"][-1]
    tp = base[sec]
    if sec == "build":
        tp += 2.0 * (bar - SEC["build"]) / 24
    drift = 0.03 if sec in ("solo", "coda", "lantern") else 0.012
    tp *= 1 + drift * math.sin(2 * math.pi * b / 23) + drift * 0.5 * math.sin(2 * math.pi * b / 6.9)
    ph = (b - BEAT0[bar]) / METER[bar]
    if bar % 4 == 3 and ph > 0.6 and sec in ("solo", "pads", "birch", "coda"):     # breathe at phrase ends
        tp *= 1 - 0.12 * math.sin(math.pi * (ph - 0.6) / 0.4 / 2)
    if sec == "coda" and bar >= SEC["coda"] + 6:
        tp *= max(0.6, 1 - 0.4 * (bar - SEC["coda"] - 6 + ph) / 4)
    # smooth joins between section tempi
    return tp


T = Tempo(bpm, meter=4, lead_in=1.2, beats=int(BEAT0[SEC["end"] + 20]))


def tb(bar, beat=0.0):
    return T.t(BEAT0[bar] + beat)


FERMATA = 12.0
LENGTH = tb(SEC["end"]) + FERMATA + 4

# ---------------------------------------------------------------- harmony: arp pool (6, low->high), pad voicing, sub
CH = {
    "D": ("D2 A2 E3 F#3 A3 D4", "F#3 A3 D4 E4", "D2"),
    "Bm7": ("B1 F#2 D3 A3 B3 D4", "F#3 A3 B3 D4", "B1"),
    "Gmaj7": ("G1 D2 B2 F#3 A3 D4", "F#3 G3 B3 D4", "G1"),
    "A": ("A1 E2 C#3 E3 A3 C#4", "E3 A3 C#4 E4", "A1"),
    "Asus": ("A1 E2 B2 D3 E3 A3", "E3 A3 B3 D4", "A1"),
    "Em7": ("E2 B2 D3 G3 B3 D4", "G3 B3 D4 E4", "E2"),
    "Em": ("E2 B2 E3 G3 B3 E4", "G3 B3 E4 F#4", "E2"),
    "C": ("C2 G2 E3 G3 C4 E4", "E3 G3 C4 D4", "C2"),
    "Am7": ("A1 E2 C3 G3 A3 C4", "E3 G3 A3 C4", "A1"),
    "F#m": ("F#1 C#2 A2 E3 F#3 A3", "E3 F#3 A3 C#4", "F#1"),
    "A/C#": ("C#2 A2 E3 A3 C#4 E4", "E3 A3 C#4 E4", "C#2"),
    "G": ("G1 D2 G2 B2 D3 G3", "G3 B3 D4 A4", "G1"),
    "Gmaj9": ("G1 D2 A2 B2 F#3 A3", "F#3 A3 B3 D4", "G1"),
}
CH = {k: (ns(a), ns(p), n(s)) for k, (a, p, s) in CH.items()}

HOME8 = ["D", "Bm7", "Gmaj7", "A", "D", "Bm7", "Em7", "Asus"]
PROG = (HOME8 + ["Gmaj7", "A/C#", "D", "D"]                                         # solo
        + HOME8 + ["Gmaj7", "A", "Bm7", "A"]                                        # pads
        + ["D", "A/C#", "Bm7", "Gmaj7", "Em7", "G", "A", "A", "D", "A/C#", "Bm7", "Gmaj7"]  # rhodes
        + ["Em", "G", "Am7", "Em", "C", "G", "D", "Em", "C", "D", "Em", "Asus"]    # birch
        + ["D", "A", "G", "D", "Bm7", "G", "A", "D", "D", "A", "G", "A"]           # lantern (3/4)
        + ["D", "A/C#", "Bm7", "Gmaj7"] * 2 + ["Em7", "F#m", "G", "A"]             # build
        + ["D", "A/C#", "Bm7", "Gmaj7", "G", "A", "F#m", "Bm7", "Em7", "G", "Asus", "A"]
        + ["D", "Bm7", "Gmaj7", "A", "D", "Bm7", "Em7", "A"]                       # climax
        + ["Bm7", "D", "Em7", "Bm7", "G", "A", "D", "D"]
        + ["Gmaj7", "Gmaj7", "A", "A"]                                              # fall
        + HOME8[:4] + ["D", "Bm7", "Em7", "Asus", "Gmaj9", "Gmaj9"])               # coda
assert len(PROG) == SEC["end"], len(PROG)

# ---------------------------------------------------------------- instruments
piano = inst("grand")
rhodes = inst("rhodes")
strings = inst("strings")
violins = inst("violins")
celli = inst("celli")
cello = inst("cello_solo")
celesta = inst("celesta")
harp = inst("harp")
choir = inst("choir")
horns = inst("horns")
pad = surge_pad(cutoff=900.0, attack=2.2, release=4.0, detune=14.0, voices=3)
saw = surge_pad(cutoff=3000.0, attack=0.25, release=1.2, detune=24.0, voices=5, reso=14.0)
drums = rig.Drums()


def pn(p, s, d, v, inst_=piano):
    s += H.t(0.009)
    inst_.note(p, s, s + d, H.v(v))


def pedal(bar):
    piano.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)


P_FULL = [0, 1, 2, 3, 4, 3, 2, 1]
P_RISE = [0, 1, 2, 3, 5, 4, 3, 2]
P_SPARSE = [0, None, 2, 3, None, 4, None, None]
P_HALF = [0, None, None, None, 2, None, 3, None]
P_WALTZ = [0, None, 2, 3, 4, 3]


def arp(bar, pattern, vel, synth=piano, sub=0.5, up=0):
    pool = CH[PROG[bar]][0]
    for i, k in enumerate(pattern):
        if k is None:
            continue
        st = tb(bar, i * sub)
        acc = 6 if i == 0 else 0
        pn(pool[k] + up, st, tb(bar + 1) - st + 0.3, vel + acc - (i % 2) * 3, synth)
    if synth is piano:
        pedal(bar)


def motif(synth, bar0, mot, vel, semis=0, octave=False, lag=0.015, scale=1.0, sustain=0.25, meter=4):
    for b, d, p in shift(mot, semis):
        b, d = b * scale, d * scale
        bar = bar0 + int(b // meter)
        st = tb(bar, b % meter) + lag
        endb = b + d
        en = tb(bar0 + int(endb // meter), endb % meter)
        v = vel + (5 if b % meter == 0 else 0)
        pn(p, st, en - st + sustain, v, synth)
        if octave:
            pn(p - 12, st + 0.01, en - st + sustain, v - 12, synth)


# ================================================================ 1. solo piano
for i in range(12):
    bar = SEC["solo"] + i
    pool = CH[PROG[bar]][0]
    if i < 8:
        pn(pool[0], tb(bar), 3.0, 40)
        pn(pool[2], tb(bar, 2), 2.0, 32)
        pn(pool[3], tb(bar, 3), 1.6, 30)
        pedal(bar)
    else:
        arp(bar, P_SPARSE, 34)
motif(piano, 0, MOTIF_HOME, 48)
motif(piano, 4, MOTIF_HOME[:4], 46)
for b, d, nm in [(0, 1, "E5"), (1, 1, "F#5"), (2, 2, "A5")]:                     # bar 6-7 answer
    pn(n(nm), tb(6, b) + 0.02, tb(6, b + d) - tb(6, b) + 0.3, 44)
pn(n("G5"), tb(7) + 0.02, 3.0, 40)
pn(n("E5"), tb(7, 2.5) + 0.02, 2.0, 36)
for bar, b, nm, v in [(8, 0, "F#5", 40), (8, 2, "D6", 34), (9, 0, "E5", 38), (9, 2.5, "A5", 32), (10, 0, "A5", 42),
                      (10, 1.5, "F#5", 36), (10, 3, "D5", 34), (11, 1, "E5", 30)]:
    pn(n(nm), tb(bar, b) + 0.02, 2.4, v)

# ================================================================ 2. pads
for i in range(12):
    bar = SEC["pads"] + i
    arp(bar, P_FULL if i % 4 != 3 else P_RISE, 36)
motif(piano, SEC["pads"], MOTIF_HOME, 50)
motif(piano, SEC["pads"] + 4, MOTIF_HOME, 52, octave=True)
for bar, b, nm, v in [(20, 0, "B4", 44), (20, 1, "D5", 42), (20, 2, "G5", 46), (21, 0, "A5", 46), (21, 2, "E5", 40),
                      (22, 0, "F#5", 44), (22, 2, "D5", 40), (23, 0, "E5", 42), (23, 2, "C#5", 38)]:
    pn(n(nm), tb(bar, b) + 0.02, 2.2, v)

# ================================================================ 3. rhodes + sine countermelody
for i in range(12):
    bar = SEC["rhodes"] + i
    arp(bar, P_FULL if i % 2 == 0 else P_RISE, 54, synth=rhodes, up=12)
    pn(CH[PROG[bar]][0][0], tb(bar), 3.0, 38)
    pn(CH[PROG[bar]][0][1], tb(bar, 2), 2.0, 32)
    pedal(bar)
motif(piano, SEC["rhodes"], MOTIF_HOME, 46, semis=12)
LEAD1 = [(28, [(0, 3, "G5"), (3, 1, "F#5")]), (29, [(0, 2, "D5"), (2, 2, "B4")]), (30, [(0, 4, "C#5")]),
         (31, [(0, 2, "E5"), (2, 2, "A5")]), (32, [(0, 4, "F#5")]), (33, [(0, 2, "E5"), (2, 1, "C#5"), (3, 1, "A4")]),
         (34, [(0, 4, "B4")]), (35, [(0, 3, "D5"), (3, 1, "C#5")])]
lead_notes = []
for bar, notes in LEAD1:
    for b, d, nm in notes:
        lead_notes.append((n(nm), tb(bar, b) + 0.02, tb(bar, b + d) - 0.02, 0.5))

# ================================================================ 4. birch memory: E minor, solo cello
for i in range(12):
    bar = SEC["birch"] + i
    arp(bar, P_HALF if i < 4 else P_SPARSE, 32)
motif(cello, SEC["birch"], MOTIF_BIRCH, 72, semis=-12, lag=0.0, sustain=0.1)
motif(cello, SEC["birch"] + 4, MOTIF_BIRCH, 78, semis=-12, lag=0.0, sustain=0.1)
motif(piano, SEC["birch"] + 4, MOTIF_BIRCH, 40, semis=12)
for bar, b, d, nm in [(44, 0, 4, "E4"), (45, 0, 2, "F#4"), (45, 2, 2, "A4"), (46, 0, 3, "G4"), (46, 3, 1, "B4"),
                      (47, 0, 4, "A4")]:
    cello.note(n(nm) - 12, tb(bar, b), tb(bar, b + d) + 0.1, 70)

# ================================================================ 5. lantern interlude (3/4)
mb_notes = []
for i in range(12):
    bar = SEC["lantern"] + i
    pool = CH[PROG[bar]][0]
    for j, k in enumerate([0, 3, 4]):
        harp.note(pool[k] + 12, tb(bar, j) + H.t(0.006), tb(bar, j) + 2.5, 62 if j == 0 else 52)
    pn(pool[0], tb(bar), 2.4, 30)
    pedal(bar)
motif(celesta, SEC["lantern"], MOTIF_LANTERN, 66, semis=6, meter=3)
motif(celesta, SEC["lantern"] + 4, MOTIF_LANTERN, 62, semis=-6, meter=3)
for b, d, p in shift(MOTIF_LANTERN, 6):
    bar = SEC["lantern"] + 8 + int(b // 3)
    mb_notes.append((p + 12, tb(bar, b % 3), 1, 0.35))
for bar, b, nm in [(54, 1, "A5"), (55, 2, "F#5"), (57, 0, "E6"), (58, 1, "D6"), (59, 0, "C#6"), (59, 2, "E6")]:
    mb_notes.append((n(nm), tb(bar, b), 1, 0.25))

# ================================================================ 6. build
for i in range(24):
    bar = SEC["build"] + i
    arp(bar, P_FULL if i % 4 != 3 else P_RISE, 38 + i // 2)
    sixteen = [0, 2, 4, 5, 3, 4, 2, 4, 1, 2, 4, 5, 3, 4, 5, 3]
    if i >= 8:
        arp(bar, sixteen, 46 + i // 2, synth=rhodes, sub=0.25, up=12)
    else:
        arp(bar, P_RISE, 48, synth=rhodes, up=12)
for b, d, p in shift(MOTIF_HOME, 0):                                                  # augmented home tune
    bar = SEC["build"] + 4 + int(2 * b // 4)
    st = tb(bar, (2 * b) % 4)
    eb = 2 * (b + d)
    en = tb(SEC["build"] + 4 + int(eb // 4), eb % 4)
    lead_notes.append((p, st + 0.02, en - 0.03, 0.55))
LEAD2 = [(72, [(0, 4, "F#5")]), (73, [(0, 2, "E5"), (2, 2, "A5")]), (74, [(0, 4, "F#5")]),
         (75, [(0, 2, "D5"), (2, 2, "B4")]), (76, [(0, 3, "B4"), (3, 1, "D5")]), (77, [(0, 4, "C#5")]),
         (78, [(0, 2, "A4"), (2, 2, "C#5")]), (79, [(0, 4, "D5")]), (80, [(0, 2, "E5"), (2, 2, "G5")]),
         (81, [(0, 4, "B5")]), (82, [(0, 4, "A5")]), (83, [(0, 2, "C#6"), (2, 2, "E6")])]
for bar, notes in LEAD2:
    for b, d, nm in notes:
        lead_notes.append((n(nm), tb(bar, b) + 0.02, tb(bar, b + d) - 0.02, 0.55))

# drums: soft and sparse, growing
for i in range(SEC["build"], SEC["fall"]):
    k = i - SEC["build"]
    big = i >= SEC["climax"]
    vk = 70 + min(k, 24) + (16 if big else 0)
    drums.hit("kick", tb(i), vk)
    drums.hit("kick", tb(i, 2.5), vk - 12)
    if big:
        drums.hit("kick", tb(i, 3), vk - 16)
    for e in range(8):
        name = "ride" if big else "hh_closed"
        drums.hit(name, tb(i, e * 0.5) + H.t(0.004), (60 if e % 2 == 0 else 44) + (10 if big else k // 2))
    if k >= 12:
        drums.hit("rim" if i < SEC["build"] + 16 else "snare", tb(i, 1), 50 + k + (20 if big else 0))
        drums.hit("rim" if i < SEC["build"] + 16 else "snare", tb(i, 3), 54 + k + (20 if big else 0))
    if big and (i - SEC["climax"]) % 4 == 0:
        drums.hit("crash_l", tb(i), 110)
for j, (nm, b) in enumerate([("tom1", 0), ("tom1", 0.5), ("tom2", 1), ("tom2", 1.5), ("tom3", 2), ("tom3", 2.5),
                             ("snare", 3), ("snare", 3.25), ("snare", 3.5), ("snare", 3.75)]):
    drums.hit(nm, tb(SEC["climax"] - 1, b), 80 + 4 * j)
drums.hit("crash_r", tb(SEC["fall"]), 112)
drums.hit("kick", tb(SEC["fall"]), 110)

# ================================================================ 7. climax
for i in range(16):
    bar = SEC["climax"] + i
    arp(bar, [0, 2, 4, 5, 3, 4, 2, 4, 1, 2, 4, 5, 3, 4, 5, 3], 64, synth=rhodes, sub=0.25, up=12)
    pool = CH[PROG[bar]][0]
    for p in pool[:2]:
        pn(p, tb(bar), 3.0, 70)
    for p in pool[2:]:
        pn(p + 12, tb(bar, 0), 1.0, 56)
        pn(p + 12, tb(bar, 2), 1.0, 50)
    pedal(bar)
motif(piano, SEC["climax"], MOTIF_HOME, 84, semis=12, octave=True)
motif(piano, SEC["climax"] + 4, MOTIF_HOME, 88, semis=12, octave=True)
for k in (0, 4):
    for b, d, p in shift(MOTIF_HOME, 0):
        bar = SEC["climax"] + k + int(b // 4)
        violins.note(p + 12, tb(bar, b % 4), tb(SEC["climax"] + k + int((b + d) // 4), (b + d) % 4) + 0.08, 108)
        lead_notes.append((p, tb(bar, b % 4) + 0.02, tb(SEC["climax"] + k + int((b + d) // 4), (b + d) % 4) - 0.03,
                           0.6))
for b, d, p in shift(MOTIF_BIRCH, 7):                                                # Birch, in B minor
    bar = SEC["climax"] + 8 + int(b // 4)
    en = tb(SEC["climax"] + 8 + int((b + d) // 4), (b + d) % 4)
    violins.note(p, tb(bar, b % 4), en + 0.08, 110)
    horns.note(p - 12, tb(bar, b % 4), en + 0.08, 104)
    pn(p, tb(bar, b % 4) + 0.02, en - tb(bar, b % 4) + 0.2, 80)
    pn(p - 12, tb(bar, b % 4) + 0.03, en - tb(bar, b % 4) + 0.2, 70)
for b, d, nm in [(0, 2, "G5"), (2, 2, "A5"), (4, 3, "F#5"), (7, 1, "E5"), (8, 4, "D5"), (12, 4, "D5")]:
    bar = SEC["climax"] + 12 + b // 4
    en = tb(SEC["climax"] + 12 + (b + d) // 4, (b + d) % 4)
    violins.note(n(nm), tb(bar, b % 4), en + 0.08, 106)
    horns.note(n(nm) - 12, tb(bar, b % 4), en + 0.08, 98)
    pn(n(nm), tb(bar, b % 4) + 0.02, en - tb(bar, b % 4) + 0.2, 78)
    lead_notes.append((n(nm), tb(bar, b % 4) + 0.02, en - 0.03, 0.6))
for i in range(16):
    bar = SEC["climax"] + i
    for p in CH[PROG[bar]][1]:
        choir.note(p, tb(bar) - 0.06, tb(bar + 1) + 0.08, 96)
        saw.note(p, tb(bar) - 0.02, tb(bar + 1) + 0.02, 100)
    horns.note(CH[PROG[bar]][2] + 24, tb(bar), tb(bar + 1), 90) if i < 8 else None

# ================================================================ strings, pad, sub across the piece
STR_START = SEC["rhodes"] + 4
for bar in range(STR_START, SEC["fall"] + 4):
    if SEC["lantern"] <= bar < SEC["build"]:
        continue
    if bar < SEC["build"]:
        vel = 60
    elif bar < SEC["climax"]:
        vel = 62 + (bar - SEC["build"]) * 2
    elif bar < SEC["fall"]:
        vel = 112
    else:
        vel = 70 - (bar - SEC["fall"]) * 8
    for p in CH[PROG[bar]][1]:
        strings.note(p, tb(bar) - 0.05, tb(bar + 1) + 0.1, vel)
    celli.note(CH[PROG[bar]][2] + 12 if CH[PROG[bar]][2] + 12 >= n("C2") else CH[PROG[bar]][2] + 24,
               tb(bar) - 0.03, tb(bar + 1) + 0.1, vel)
PAD_BARS = [b for b in range(SEC["pads"], SEC["fall"] + 4)]
for bar in PAD_BARS:
    for p in CH[PROG[bar]][1]:
        pad.note(p, tb(bar) - 0.05, tb(bar + 1) + 0.1, 80)
sub_notes = [(CH[PROG[bar]][2] + 12, tb(bar), tb(bar + 1) - 0.05, 0.5)
             for bar in range(SEC["pads"] + 4, SEC["fall"] + 2) if not (SEC["lantern"] <= bar < SEC["build"])]

# ================================================================ 9. coda: piano alone
for i in range(8):
    bar = SEC["coda"] + i
    arp(bar, P_HALF if i < 4 else P_SPARSE, 32 - i)
motif(piano, SEC["coda"], MOTIF_HOME, 46)
motif(piano, SEC["coda"] + 4, MOTIF_HOME[:4], 40)
pn(n("E5"), tb(SEC["coda"] + 6) + 0.05, 2.5, 34)
pn(n("C#5"), tb(SEC["coda"] + 7) + 0.05, 2.5, 32)
fs = tb(SEC["coda"] + 8)
piano.pedal(fs - 0.03, fs + FERMATA + 4)
for i, nm in enumerate(["G1", "D2", "A2", "B2", "F#3", "A3", "D4"]):
    piano.note(n(nm), fs + 0.08 * i, fs + FERMATA + 4, 36 - i)
piano.note(n("A4"), fs + 1.6, fs + FERMATA + 4, 34)                                  # the home tune's last note
piano.note(n("E5"), fs + 5.5, fs + FERMATA + 4, 24)

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in SEC.items()))


def lp_curve(x2, keys, q=0.8):
    tt = np.arange(x2.shape[1]) / SR
    fc = np.exp(np.interp(tt, [tb(b) for b, _ in keys], [math.log(f) for _, f in keys])).astype(np.float32)
    return np.stack([rave.svf(c, fc, q, "lp") for c in x2]).astype(np.float32)


PN = piano.render(LENGTH)
RH = rhodes.render(LENGTH)
STR = strings.render(LENGTH) + celli.render(LENGTH) * 0.7
VN = violins.render(LENGTH)
VC = cello.render(LENGTH)
CE = celesta.render(LENGTH)
HP = harp.render(LENGTH)
CHR = choir.render(LENGTH)
HN = horns.render(LENGTH)
PD = pad.render(LENGTH)
SW = saw.render(LENGTH)
DRC = drums.render(LENGTH)
DR = rig.drum_bus(DRC, close=0.8, room=0.8, kick_db=-3, snare_db=-4, hat_db=-6, tom_db=-2, oh_db=0)
SUB = voice(sub_notes, LENGTH, att=0.4, rel=1.0)
LEAD = voice(lead_notes, LENGTH, harm=(1.0, 0.3, 0.1), vib=14, glide=0.07, att=0.09, rel=0.7, seed=5)
MB = music_box(mb_notes, LENGTH, seed=4)

PN = rig.fx2(Pedalboard([HighpassFilter(35), PeakFilter(220, 1.0, 0.8), PeakFilter(3000, -2, 0.9),
                         LowpassFilter(9000), Compressor(-24, 1.8, 20, 250)]), PN)
RH = rig.fx2(Pedalboard([HighpassFilter(120), Chorus(0.4, 0.3, 7, 0, 0.4)]), RH)
PD = lp_curve(PD, [(0, 600), (SEC["build"], 700), (SEC["climax"], 4200), (SEC["fall"], 4200), (SEC["coda"], 500)])
PD = rig.fx2(Pedalboard([HighpassFilter(110), Chorus(0.3, 0.25, 7, 0, 0.5)]), PD)
SW = rig.fx2(Pedalboard([HighpassFilter(160), Distortion(14), LowpassFilter(4200), Chorus(0.6, 0.3, 8, 0, 0.5)]), SW)
SUB = rig.fx(Pedalboard([LowpassFilter(160)]), SUB)
LEAD = rig.fx(Pedalboard([HighpassFilter(150), LowpassFilter(5000)]), LEAD)
MB = rig.fx(Pedalboard([HighpassFilter(300)]), MB)
DR = rig.fx2(Pedalboard([Compressor(-18, 2.5, 10, 120), HighShelfFilter(8000, -3)]), DR)

PN = rig.at_level(PN, -20)
RH = rig.at_level(RH, -26)
STR = rig.at_level(STR, -24)
VN = rig.at_level(VN, -24)
VC = rig.at_level(VC, -21)
CE = rig.at_level(CE, -23)
HP = rig.at_level(HP, -26)
CHR = rig.at_level(CHR, -24)
HN = rig.at_level(HN, -25)
PD = rig.at_level(PD, -28)
SW = rig.at_level(SW, -22)
DR = rig.at_level(DR, -21)
SUB = rig.pan(rig.at_level(SUB, -27), 0)
LEAD = rig.pan(rig.at_level(LEAD, -23), -0.1)
MB = rig.pan(rig.at_level(MB, -28), 0.25)

# section gain shaping: the piano solo stays intimate, build rises, fall sinks
PN = rig.automate(PN, [(0, tb(SEC["pads"]), 3.0), (tb(SEC["climax"]), tb(SEC["fall"]), -3.0),
                       (tb(SEC["coda"]), LENGTH, 3.0)], ramp=2.0)
PD = rig.automate(PD, [(tb(SEC["pads"]), tb(SEC["rhodes"]), -4.0), (tb(SEC["lantern"]), tb(SEC["build"]), -5.0),
                       (tb(SEC["climax"]), tb(SEC["fall"]), 3.0), (tb(SEC["fall"]), LENGTH, -2.0)], ramp=3.0)
STR = rig.automate(STR, [(tb(SEC["rhodes"]), tb(SEC["birch"]), -5.0), (tb(SEC["birch"]), tb(SEC["lantern"]), -4.0),
                         (tb(SEC["build"]), tb(SEC["build"] + 12), -4.0), (tb(SEC["climax"]), tb(SEC["fall"]), 3.0)],
                   ramp=3.0)
RH = rig.automate(RH, [(tb(SEC["climax"]), tb(SEC["fall"]), 2.0)], ramp=2.0)
DR = rig.automate(DR, [(tb(SEC["build"]), tb(SEC["build"] + 12), -6.0), (tb(SEC["build"] + 12), tb(SEC["climax"]), -3.0)],
                  ramp=3.0)

keys = PN + RH
orch = STR + VN + VC + HN + CHR
bells = CE + HP + MB
synth = PD + SW + SUB + LEAD
dry = keys + orch + bells + synth + DR
wet = (rig.hall(keys + bells, decay=2.8, size=30, predelay=20, high_cut=6500, early=16, late=75)
       + rig.hall(orch, decay=3.4, size=45, predelay=24, high_cut=6500, early=18, late=85)
       + rig.hall(PD + LEAD + SW * 0.5, decay=6.0, size=50, predelay=40, high_cut=5000, early=4, late=95) * 0.9
       + rig.hall(DR, decay=1.6, size=25, predelay=8, high_cut=6000, early=10, late=40) * 0.6)
mix = dry + wet
names = list(SEC)
sections = [(k, tb(SEC[k]), tb(SEC[names[i + 1]]) if i + 1 < len(names) else LENGTH) for i, k in enumerate(names)]
master(mix, NAME, sections=sections,
       stems={"piano": PN, "rhodes": RH, "strings": STR + VN, "cello": VC, "bells": bells, "pad": PD, "saw": SW,
              "lead": LEAD, "drums": DR, "choir": CHR},
       fade_s=4.0, target_rms_db=-17.0)
