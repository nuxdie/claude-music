"""01 Spawn Point — title-screen theme. D major, 64 BPM, analog synth + piano.

A warm detuned pad fades in on Dadd9 with sine bells falling around it; the grand piano states MOTIF_HOME (the
album's home tune, which returns in the finale); a slow Surge pluck arpeggio with dotted-eighth echoes enters; the
B section hands a counter-melody to a soft analog lead with glide and delayed vibrato while the pad's filter opens;
an arpeggio-only interlude; the home tune again, doubled by FM bells, at the brightest point; then the filter
closes and the piano leaves the tune on an unresolved Gmaj7#11 -> Dadd9.

Form (bars): intro 4 | A 8 | B 8 | interlude 4 | A' 8 | B' 4 | outro 5 + fermata.
"""
from kit import *

H = Human(1009)

CH = {  # arp pool low->high, pad voicing, sub root
    "Dadd9":  (ns("D2 A2 E3 F#3 A3 D4 E4 F#4"), ns("F#3 A3 D4 E4"), n("D2")),
    "Bm7":    (ns("B1 F#2 D3 A3 B3 D4 F#4 A4"), ns("F#3 A3 B3 D4"), n("B1")),
    "Gmaj7":  (ns("G1 D2 B2 F#3 A3 B3 D4 F#4"), ns("F#3 A3 B3 D4"), n("G1")),
    "Asus4":  (ns("A1 E2 D3 E3 A3 B3 D4 E4"), ns("E3 A3 B3 D4"), n("A1")),
    "A":      (ns("A1 E2 C#3 E3 A3 C#4 E4 A4"), ns("E3 A3 C#4 E4"), n("A1")),
    "F#m7":   (ns("F#1 C#2 A2 E3 A3 C#4 E4 F#4"), ns("E3 A3 C#4 E4"), n("F#1")),
    "Em9":    (ns("E2 B2 D3 F#3 G3 B3 D4 F#4"), ns("D3 F#3 G3 B3"), n("E2")),
    "G/A":    (ns("A1 E2 G3 B3 D4 F#4 G4 B4"), ns("G3 B3 D4 F#4"), n("A1")),
    "Gmaj7#11": (ns("G1 D2 B2 F#3 C#4 D4 F#4 B4"), ns("F#3 B3 C#4 D4"), n("G1")),
}
PROG_A = ["Dadd9", "Bm7", "Gmaj7", "Asus4", "Dadd9", "Bm7", "Gmaj7", "A"]
PROG_B = ["Gmaj7", "A", "F#m7", "Bm7", "Em9", "G/A", "A", "A"]
SEC = {"intro": 0, "A": 4, "B": 12, "inter": 20, "A2": 24, "B2": 32, "out": 36}
END = 41
PROG = (["Dadd9", "Dadd9", "Gmaj7", "Gmaj7"] + PROG_A + PROG_B + ["Bm7", "Gmaj7", "Bm7", "A"] + PROG_A
        + PROG_B[:4] + ["Em9", "Gmaj7", "Dadd9", "Gmaj7#11", "Gmaj7#11"])
assert len(PROG) == END

HOME = shift(MOTIF_HOME, 0)
HOME_ANSWER = [(0, 2, n("D5")), (2, 1, n("A4")), (3, 1, n("B4")), (4, 2, n("F#5")), (6, 2, n("E5")),
               (8, 1, n("D5")), (9, 1, n("E5")), (10, 2, n("B4")), (12, 3, n("C#5")), (15, 1, n("E5"))]
B_TUNE = [(0, 2, "B4"), (2, 1, "D5"), (3, 1, "F#5"), (4, 3, "E5"), (7, 1, "C#5"), (8, 2, "A4"), (10, 2, "C#5"),
          (12, 4, "D5"), (16, 2, "G5"), (18, 1, "F#5"), (19, 1, "E5"), (20, 2, "D5"), (22, 2, "B4"),
          (24, 3, "C#5"), (27, 1, "E5"), (28, 4, "A4")]
B_TUNE = [(b, d, n(x)) for b, d, x in B_TUNE]

T = Tempo(rubato(64, drift=0.02, breath_every=8, breath=0.10, rit_from=37, rit_to=41, rit=0.6), lead_in=1.0)
tb = T.tb
FERMATA = 12.0
LENGTH = tb(END) + FERMATA + 3

piano = inst("grand")
pad = surge_pad(cutoff=2400.0, attack=2.6, release=5.0, detune=16.0, voices=4, reso=6.0)
pad2 = surge_pad(cutoff=1600.0, attack=3.5, release=6.0, detune=24.0, voices=3, shape=0.5, osc="Classic", vol=-8.0)
arp = surge_pluck(cutoff=1700.0, decay=0.9, release=0.7, shape=0.0, detune=10.0, voices=2)


def pn(p, s, d, v):
    s += H.t(0.009)
    piano.note(p, s, s + d, H.v(v))


def pedal(bar, bars=1):
    piano.pedal(tb(bar) + 0.04, tb(bar + bars) - 0.01)


def tune(bar0, motif, vel=50, octave=False, lag=0.02):
    for b, d, p in motif:
        st = tb(bar0, b) + lag
        en = tb(bar0, b + d)
        v = vel + (5 if b % 4 == 0 else 0)
        pn(p, st, en - st + 0.3, v)
        if octave:
            pn(p - 12, st + 0.01, en - st + 0.3, v - 14)


def broken(bar, ch, vel=34, pattern=(0, 2, 4, 3), step=1.0):
    pool = CH[ch][0]
    for i, k in enumerate(pattern):
        if k is None:
            continue
        st = tb(bar, i * step)
        pn(pool[k], st, tb(bar + 1) - st + 0.4, vel + (5 if i == 0 else 0))


# ---------------------------------------------------------------- piano
for bar in range(SEC["intro"], SEC["A"]):                       # low single roots in the fog
    pn(CH[PROG[bar]][0][0], tb(bar, 0.5), 4.0, 30)
    pedal(bar)
for bar in range(SEC["A"], SEC["B"]):
    broken(bar, PROG[bar], vel=31, pattern=(0, 2, None, 3) if bar < 8 else (0, 2, 4, 3))
    pedal(bar)
tune(SEC["A"], HOME, vel=48)
tune(SEC["A"] + 4, HOME_ANSWER, vel=48)
for bar in range(SEC["B"], SEC["inter"]):                        # half-time chords under the lead
    pool = CH[PROG[bar]][0]
    for i, k in enumerate((0, 3, 4)):
        pn(pool[k], tb(bar, 0) + 0.035 * i, 3.6, 30)
    pn(pool[5], tb(bar, 2.5), 1.8, 27)
    pedal(bar)
for bar in range(SEC["inter"], SEC["A2"]):                       # interlude: droplets
    pool = CH[PROG[bar]][0]
    for beat in (0.5, 2.0, 3.25):
        pn(H.r.choice(pool[4:]) + 12, tb(bar, beat), 2.0, 24 + H.r.randint(0, 5))
    pedal(bar)
for bar in range(SEC["A2"], SEC["B2"]):
    broken(bar, PROG[bar], vel=35, pattern=(0, 2, 4, 3), step=1.0)
    pn(CH[PROG[bar]][0][5], tb(bar, 2.5), 1.4, 28)
    pedal(bar)
tune(SEC["A2"], HOME, vel=54, octave=True)
tune(SEC["A2"] + 4, HOME_ANSWER, vel=54, octave=True)
for bar in range(SEC["B2"], SEC["out"]):
    broken(bar, PROG[bar], vel=31, pattern=(0, 3, None, 4))
    pedal(bar)
tune(SEC["B2"], B_TUNE[:9], vel=42)                              # piano remembers half of the lead's tune
# outro: the home tune in fragments, slower, then the open chords
for bar in range(SEC["out"], END):
    pn(CH[PROG[bar]][0][0], tb(bar), 4.0, 30)
    pn(CH[PROG[bar]][0][3], tb(bar, 1), 3.0, 26)
    pedal(bar)
for b, d, p in HOME[:4]:
    pn(p, tb(SEC["out"], b) + 0.04, d * 0.95 + 0.4, 40)
for b, d, p in HOME[4:6]:
    pn(p, tb(SEC["out"] + 2, b - 8) + 0.06, d * 0.95 + 0.4, 36)
fs = tb(END)
piano.pedal(fs - 0.04, fs + FERMATA)
for i, x in enumerate(ns("D2 A2 E3 F#3 A3 C#4")):             # Dadd9 with the #11 of the last bar still in it
    piano.note(x, fs + 0.08 * i, fs + FERMATA, 34 - i)
piano.note(n("A4"), fs + 1.6, fs + FERMATA, 30)
piano.note(n("E5"), fs + 4.4, fs + FERMATA, 25)

# ---------------------------------------------------------------- pads (two layers), arp, lead, bells, sub
for bar in range(0, END):
    for p in CH[PROG[bar]][1]:
        pad.note(p, tb(bar) - 0.06, tb(bar + 1) + 0.12, 85)
for bar in range(SEC["B"], SEC["out"]):
    for p in CH[PROG[bar]][1]:
        pad2.note(p + 12, tb(bar) - 0.06, tb(bar + 1) + 0.12, 70)
pad.note(n("D3"), fs - 0.05, fs + FERMATA, 70)
for p in ns("F#3 A3 E4"):
    pad.note(p, fs - 0.05, fs + FERMATA, 70)

ARP_UPDOWN = [0, 2, 3, 4, 5, 6, 5, 4]
for bar in list(range(SEC["A"] + 4, SEC["inter"] + 4)) + list(range(SEC["A2"], SEC["out"] + 2)):
    pool = CH[PROG[bar]][0]
    for i, k in enumerate(ARP_UPDOWN):
        st = tb(bar, i * 0.5)
        v = 92 if i == 0 else (78 if i % 2 == 0 else 66)
        arp.note(pool[k] + 12, st, st + 0.22, v)

lead_notes = [(p, tb(SEC["B"], b) + 0.02, tb(SEC["B"], b + d) - 0.03, 0.5) for b, d, p in B_TUNE]
bell_notes = []
for bar in range(0, SEC["A"]):
    for beat in (1.0, 3.0):
        bell_notes.append((H.r.choice(CH[PROG[bar]][1]) + 24, tb(bar, beat), 1, 0.3))
for bar0, motif in ((SEC["A2"], HOME), (SEC["A2"] + 4, HOME_ANSWER)):
    for b, d, p in motif:
        bell_notes.append((p + 12, tb(bar0, b) + 0.025, d, 0.35))
for bar in range(SEC["inter"], SEC["A2"]):
    bell_notes.append((CH[PROG[bar]][1][-1] + 24, tb(bar, 1.5), 1, 0.22))
sub_notes = [(CH[PROG[bar]][2] + 12, tb(bar), tb(bar + 1) - 0.04, 0.5) for bar in range(SEC["B"], SEC["out"] + 2)]

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in SEC.items()))
pno = piano.render(LENGTH)
pd = pad.render(LENGTH)
pd2 = pad2.render(LENGTH)
ar = arp.render(LENGTH)
lead = voice(lead_notes, LENGTH, harm=(1, 0.42, 0.22, 0.12, 0.07, 0.04), vib=16, glide=0.08, att=0.12, rel=0.8,
             detune=7, seed=3)
bells = fm_bell(bell_notes, LENGTH, ratio=3.5, index=1.6, decay=2.2, seed=4)
sub = voice(sub_notes, LENGTH, att=0.5, rel=1.2)

# pad filter: closed in the intro, opening through B, widest in A', closing in the outro (time-varying, no clicks)
nn = int(LENGTH * SR)
tt = np.arange(nn) / SR
cut = np.interp(tt, [0, tb(4), tb(12), tb(20), tb(24), tb(28), tb(32), tb(36), tb(END), LENGTH],
                [350, 700, 1100, 2300, 1500, 2800, 3200, 1800, 600, 400]).astype(np.float32)
pd = np.stack([rave.svf(c, cut, 0.8, "lp") for c in pd])
pd2 = np.stack([rave.svf(c, cut * 1.3, 0.7, "lp") for c in pd2])

pno = rig.fx2(Pedalboard([HighpassFilter(40), PeakFilter(250, 1.0, 0.8), PeakFilter(3000, -2.0, 0.9),
                          LowpassFilter(7500), Compressor(-26, 1.8, 20, 250)]), pno)
pd = rig.fx2(Pedalboard([HighpassFilter(90), Chorus(0.25, 0.2, 8, 0.0, 0.5)]), pd)
pd2 = rig.fx2(Pedalboard([HighpassFilter(200), Chorus(0.4, 0.3, 9, 0.0, 0.6)]), pd2)
ar = rig.fx2(Pedalboard([HighpassFilter(180), LowpassFilter(3500)]), ar)
echo = rig.fx2(Pedalboard([Delay(60 / 64 * 0.75, 0.42, 1.0), LowpassFilter(2200)]), ar)
ar = ar + np.stack([echo[1], echo[0]]) * 0.55                      # ping-pong-ish: echo swapped L/R
lead = rig.fx(Pedalboard([HighpassFilter(160), LowpassFilter(3000)]), lead)
bells = rig.fx(Pedalboard([HighpassFilter(300), LowpassFilter(7000)]), bells)
sub = rig.fx(Pedalboard([LowpassFilter(150)]), sub)

pno = rig.at_level(pno, -20)
pd = rig.at_level(pd, -25)
pd2 = rig.automate(rig.at_level(pd2, -31), [(0, tb(SEC["A2"]), -3.0)], ramp=4.0)
ar = rig.automate(rig.at_level(ar, -30), [(tb(SEC["inter"]), tb(SEC["A2"]), 2.5)], ramp=2.0)
lead_st = rig.pan(rig.at_level(lead, -23), 0.12)
bells_st = rig.pan(rig.at_level(bells, -31), -0.3)
sub_st = rig.pan(rig.at_level(sub, -27), 0)

synths = pd + pd2 + ar
dry = pno + synths + lead_st + bells_st + sub_st
room = (rig.hall(pno, decay=3.0, size=34, predelay=24, high_cut=6500, early=15, late=70)
        + rig.hall(synths + lead_st + bells_st, decay=6.5, size=55, predelay=45, high_cut=5500, early=4, late=95))
mix = dry + room

sections = [("intro", 0, tb(4)), ("A", tb(4), tb(12)), ("B", tb(12), tb(20)), ("interlude", tb(20), tb(24)),
            ("A'", tb(24), tb(32)), ("B'", tb(32), tb(36)), ("outro", tb(36), LENGTH)]
master(mix, "01_spawn_point", sections=sections,
       stems={"piano": pno, "pads": pd + pd2, "arp": ar, "lead": lead_st, "bells": bells_st, "sub": sub_st},
       fade_s=3.5, target_rms_db=-18.0)
