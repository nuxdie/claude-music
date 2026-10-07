"""Birch — track 2. A slow, spacious grand-piano piece in E minor (aeolian), in the manner of C418's 'Sweden'.
Original material built on MOTIF_BIRCH.

72 BPM with rubato. Low open fifths held in the pedal, chord tones stepping upward under a plain melody of long
notes; the B section lifts to C major; a string section and celli swell in under the third statement; a quieter
string-led reprise of B; the coda stops on an E minor add9 left to ring.

Form (bars): intro 4 | A1 8 | A2 8 | B 8 | interlude 4 | A3 8 (strings, peak) | B2 8 (strings lead) | coda 6 + fermata.
"""
from kit import *

H = Human(1709)

# ---------------------------------------------------------------- harmony: (bass dyad, mid voicing)
CH = {
    "Em":    (ns("E2 B2"), ns("G3 B3 D4")),
    "Em9":   (ns("E2 B2"), ns("G3 B3 F#4")),
    "Cmaj7": (ns("C2 G2"), ns("E3 G3 B3")),
    "G":     (ns("G1 D2"), ns("B2 D3 G3")),
    "D/F#":  (ns("F#1 D2"), ns("A2 D3 F#3")),
    "Am7":   (ns("A1 E2"), ns("C3 G3 C4")),
    "Bsus":  (ns("B1 F#2"), ns("E3 F#3 A3")),
    "B7":    (ns("B1 F#2"), ns("D#3 F#3 A3")),
    "C":     (ns("C2 G2"), ns("E3 G3 C4")),
    "G/B":   (ns("B1 G2"), ns("D3 G3 B3")),
    "Em/G":  (ns("G1 E2"), ns("B2 E3 G3")),
    "D":     (ns("D2 A2"), ns("F#3 A3 D4")),
    "Bm7":   (ns("B1 F#2"), ns("D3 F#3 A3")),
}
PROG_A = ["Em", "Cmaj7", "G", "D/F#", "Em", "Cmaj7", "Am7", "Bsus"]
PROG_B = ["C", "G/B", "Am7", "Em/G", "C", "D", "Bm7", "B7"]

MEL_A = [  # MOTIF_BIRCH, then its answer
    [(0, 3, "B4"), (3, 1, "E5")],
    [(0, 2, "D5"), (2, 2, "B4")],
    [(0, 3, "A4"), (3, 1, "G4")],
    [(0, 4, "E4")],
    [(0, 2, "G4"), (2, 1, "A4"), (3, 1, "B4")],
    [(0, 3, "E5"), (3, 1, "D5")],
    [(0, 2, "C5"), (2, 1, "B4"), (3, 1, "A4")],
    [(0, 4, "B4")],
]
MEL_B = [
    [(0, 3, "E5"), (3, 1, "G5")],
    [(0, 4, "D5")],
    [(0, 2, "C5"), (2, 2, "E5")],
    [(0, 4, "B4")],
    [(0, 1, "C5"), (1, 1, "D5"), (2, 2, "E5")],
    [(0, 3, "F#5"), (3, 1, "A5")],
    [(0, 2, "G5"), (2, 2, "F#5")],
    [(0, 4, "F#5")],
]

SEC = {"intro": 0, "A1": 4, "A2": 12, "B": 20, "inter": 28, "A3": 32, "B2": 40, "coda": 48}
END_BAR = 54
PROG = (["Em9", "Cmaj7", "Em9", "Cmaj7"] + PROG_A + PROG_A + PROG_B + ["Em9", "Cmaj7", "Em9", "Cmaj7"]
        + PROG_A + PROG_B + ["Em", "Cmaj7", "Em", "Cmaj7", "Am7", "Cmaj7"])
assert len(PROG) == END_BAR

T = Tempo(rubato(72, drift=0.022, breath_every=4, breath=0.13, rit_from=50, rit_to=54, rit=0.6), lead_in=1.0)
tb = T.tb
FERMATA = 12.0
LENGTH = tb(END_BAR) + FERMATA + 4

piano = inst("grand")
strings = inst("strings")
celli = inst("celli")
violins = inst("violins")
pad = surge_pad(cutoff=650.0, attack=3.0, release=5.0, detune=10.0, voices=3, reso=6.0)


def pnote(pitch, start, dur, vel):
    s = start + H.t(0.009)
    piano.note(pitch, s, s + dur, H.v(vel))


def pedal_bar(bar, half=False):
    if half:
        piano.pedal(tb(bar) + 0.03, tb(bar, 2) - 0.01)
        piano.pedal(tb(bar, 2) + 0.03, tb(bar + 1) - 0.01)
    else:
        piano.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)


def left(bar, style, vel=38):
    bass, mid = CH[PROG[bar]]
    end = tb(bar + 1) + 0.2
    for i, p in enumerate(bass):
        pnote(p, tb(bar) + 0.02 * i, end - tb(bar), vel + 4 - 3 * i)
    if style == "hold":                                # rolled chord with the bass, all held
        for i, p in enumerate(mid):
            pnote(p, tb(bar, 0.12 + 0.06 * i), end - tb(bar), vel - 6)
    elif style == "step":                              # chord tones climbing on beats 2, 3, 4
        for i, p in enumerate(mid):
            pnote(p, tb(bar, 1 + i), end - tb(bar, 1 + i), vel - 4 - (i == 1) * 2)
    elif style == "pulse":                             # dyads on 2 and 3&
        pnote(mid[0], tb(bar, 1), end - tb(bar, 1), vel - 5)
        pnote(mid[1], tb(bar, 1) + 0.015, end - tb(bar, 1), vel - 6)
        pnote(mid[2], tb(bar, 2.5), end - tb(bar, 2.5), vel - 6)
        pnote(mid[1], tb(bar, 3.5), end - tb(bar, 3.5), vel - 9)
    elif style == "bass":
        pass
    pedal_bar(bar)


def melody(bar0, mel, vel=52, octave=False, lag=0.02, up=0):
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + lag
            en = tb(bar0 + i, b + d)
            v = vel + (4 if b == 0 else 0) + (3 if d >= 3 else 0)
            pnote(n(nm) + up, st, en - st + 0.3, v)
            if octave:
                pnote(n(nm) + up - 12, st + 0.014, en - st + 0.3, v - 13)


# --- intro: low open fifths alone, single high notes falling in like light through branches
for i in range(4):
    left(SEC["intro"] + i, "bass", vel=34)
for bar, beat, nm, v in [(0, 2.0, "B5", 30), (1, 1.0, "G5", 28), (1, 3.0, "E5", 26), (2, 0.5, "F#5", 30),
                         (2, 2.5, "D5", 27), (3, 1.0, "E5", 30), (3, 3.0, "B4", 26)]:
    pnote(n(nm), tb(bar, beat), 3.0, v)

# --- A1: held chords, the motif plainly
for i in range(8):
    left(SEC["A1"] + i, "hold", vel=36)
melody(SEC["A1"], MEL_A, vel=48)

# --- A2: chord tones step upward under the tune; octave colour in the answer
for i in range(8):
    left(SEC["A2"] + i, "step", vel=38)
melody(SEC["A2"], MEL_A[:4], vel=50)
melody(SEC["A2"] + 4, MEL_A[4:], vel=52, octave=True)
pnote(n("G5"), tb(SEC["A2"] + 3, 2.0), 2.0, 32)             # little echo after the motif cadence

# --- B: the lift to C major
for i in range(8):
    left(SEC["B"] + i, "pulse" if i % 2 == 0 else "step", vel=40)
melody(SEC["B"], MEL_B, vel=55, octave=True)

# --- interlude: the motif in the high register, slowly, over held fifths
for i in range(4):
    left(SEC["inter"] + i, "bass", vel=32)
for bar, beat, nm, v in [(28, 0.5, "B5", 34), (28, 3.0, "E6", 30), (29, 0.5, "D6", 32), (29, 2.5, "B5", 28),
                         (30, 0.5, "A5", 31), (30, 3.0, "G5", 28), (31, 0.5, "E5", 30)]:
    pnote(n(nm), tb(bar, beat), 3.5, v)

# --- A3: the peak — melody up an octave in octaves, fuller left hand, strings underneath
for i in range(8):
    left(SEC["A3"] + i, "pulse", vel=44)
melody(SEC["A3"], MEL_A, vel=60, octave=True, up=12)

# --- B2: strings sing the B tune; piano keeps time softly and answers high
for i in range(8):
    left(SEC["B2"] + i, "hold" if i % 2 else "step", vel=35)
for i, notes in enumerate(MEL_B):
    for b, d, nm in notes:
        if b == 0 and i % 2 == 1:
            pnote(n(nm) + 12, tb(SEC["B2"] + i, b + 2.5), 2.0, 30)

# --- coda: fragments of the motif, then the rolled Em add9
for i in range(6):
    left(SEC["coda"] + i, "hold" if i < 4 else "bass", vel=33 - i)
melody(SEC["coda"], MEL_A[:2], vel=44)
melody(SEC["coda"] + 2, [[(0, 3, "A4"), (3, 1, "G4")]], vel=40)
pnote(n("B4"), tb(SEC["coda"] + 4, 0.2), 4.0, 36)
pnote(n("A4"), tb(SEC["coda"] + 5, 1.0), 3.0, 32)
fs = tb(END_BAR)
piano.pedal(fs - 0.03, fs + FERMATA)
for i, nm in enumerate(["E1", "B1", "E2", "B2", "G3", "B3", "F#4", "G4"]):
    piano.note(n(nm), fs + 0.08 * i, fs + FERMATA, 38 - 2 * i)
piano.note(n("B5"), fs + 1.6, fs + FERMATA, 34)
piano.note(n("E5"), fs + 4.5, fs + FERMATA, 28)

# ---------------------------------------------------------------- strings: chords from A3 through the coda
S_BARS = range(SEC["A3"] - 1, SEC["coda"] + 4)
for bar in S_BARS:
    bass, mid = CH[PROG[bar]]
    for p in mid:
        strings.note(p + 12, tb(bar) - 0.08, tb(bar + 1) + 0.1, 70)
    celli.note(bass[0] + 12, tb(bar) - 0.1, tb(bar + 1) + 0.05, 72)
for i, notes in enumerate(MEL_B):                    # violins sing B2's tune
    for b, d, nm in notes:
        violins.note(n(nm), tb(SEC["B2"] + i, b) - 0.05, tb(SEC["B2"] + i, b + d) + 0.08, 72)
violins.legato = True


def swell(t):
    """0..1 dynamic: grows through A3, eases for B2, dies in the coda."""
    return np.interp(t, [tb(31), tb(34), tb(38), tb(40), tb(44), tb(48), tb(52)],
                     [0.0, 0.45, 0.9, 0.55, 0.6, 0.35, 0.0])


# ---------------------------------------------------------------- pad + sub under everything after the intro
for bar in range(SEC["A1"], END_BAR):
    _, mid = CH[PROG[bar]]
    for p in mid:
        pad.note(p + 12, tb(bar) - 0.05, tb(bar + 1) + 0.1, 80)
for p in ns("E3 B3 G4"):
    pad.note(p, fs, fs + FERMATA - 3, 80)
sub_notes = [(CH[PROG[bar]][0][0] + 12, tb(bar), tb(bar + 1) - 0.05, 0.5) for bar in range(SEC["A2"], SEC["coda"] + 4)]

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in SEC.items()) + f"  end {fs:.1f}")
pno = piano.render(LENGTH)
st = strings.render_dynamic(LENGTH, swell, lo=40, hi=100)
ce = celli.render_dynamic(LENGTH, swell, lo=40, hi=96)
vn = violins.render_dynamic(LENGTH, lambda t: np.clip(swell(t) + 0.15, 0, 1), lo=50, hi=96)
pd = pad.render(LENGTH)
sub = voice(sub_notes, LENGTH, att=0.5, rel=1.2)

pno = rig.fx2(Pedalboard([HighpassFilter(35), PeakFilter(250, 1.0, 0.8), PeakFilter(3000, -2.0, 0.9),
                          LowpassFilter(9000), Compressor(-24, 1.6, 25, 250)]), pno)
st = rig.fx2(Pedalboard([HighpassFilter(120), PeakFilter(2500, -3, 0.8), LowpassFilter(7000)]), st)
ce = rig.fx2(Pedalboard([HighpassFilter(55), LowpassFilter(4000)]), ce)
vn = rig.fx2(Pedalboard([HighpassFilter(200), PeakFilter(3000, -2, 0.8), LowpassFilter(8000)]), vn)
pd = rig.fx2(Pedalboard([HighpassFilter(140), LowpassFilter(2600), Chorus(0.25, 0.2, 8, 0.0, 0.5)]), pd)
sub = rig.fx(Pedalboard([LowpassFilter(140)]), sub)

# string level follows the swell (render_dynamic changes timbre; this shapes loudness)
sw = np.clip(swell(np.arange(int(LENGTH * SR)) / SR), 0, 1).astype(np.float32)
str_gain = (0.15 + 0.85 * sw) * (sw > 0.001)

pno = rig.at_level(pno, -19)
st = rig.at_level(st, -25) * str_gain
ce = rig.at_level(ce, -26.5) * str_gain
vn = rig.at_level(vn, -25)
pd = rig.automate(rig.at_level(pd, -31), [(tb(SEC["A1"]) - 2, tb(SEC["A2"]), -4), (tb(SEC["coda"] + 2), LENGTH, -6)],
                  ramp=3.0)
sub = rig.pan(rig.at_level(sub, -30), 0)

strings_bus = st + ce + vn
dry = pno + strings_bus + pd + sub
room = (rig.hall(pno, decay=3.2, size=34, predelay=24, high_cut=6500, early=15, late=80)
        + rig.hall(strings_bus + pd, decay=4.5, size=45, predelay=35, high_cut=5500, early=8, late=95))
mix = dry + room

sections = [(k, tb(v), tb(list(SEC.values())[i + 1]) if i + 1 < len(SEC) else LENGTH) for i, (k, v) in
            enumerate(SEC.items())]
master(mix, "02_birch", sections=sections, stems={"piano": pno, "strings": strings_bus, "pad": pd, "sub": sub},
       fade_s=4.0, tape_kw={"wow_cents": 4.0})
