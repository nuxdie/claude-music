"""Lantern Waltz — track 4. A 3/4 lullaby in Ab major built on MOTIF_LANTERN, in the spirit of C418's
'Mice on Venus' / 'Subwoofer Lullaby' but as a waltz. Original material.

88 BPM. A music box starts alone; celesta takes the tune over a harp waltz (bass on one, chords on two and three)
and a sine sub that pulses on every downbeat; the upright piano sings it the second time with celesta answering;
the B section turns to F minor with harp and music-box arpeggios; a full last statement; then the music box is
left alone, winding down like a spring running out.

Form (bars): intro 8 | A1 16 | A2 16 | B 16 | A3 16 | outro 8 + fermata.
"""
from kit import *

H = Human(404)

# ---------------------------------------------------------------- harmony: (bass, mid chord, high arp pool)
CH = {
    "Ab":    (n("Ab2"), ns("C4 Eb4 Ab4"), ns("Ab5 C6 Eb6 Ab6")),
    "Eb":    (n("Eb2"), ns("Bb3 Eb4 G4"), ns("G5 Bb5 Eb6 G6")),
    "Db":    (n("Db2"), ns("Db4 F4 Ab4"), ns("F5 Ab5 Db6 F6")),
    "Fm":    (n("F2"), ns("C4 F4 Ab4"), ns("F5 Ab5 C6 F6")),
    "Bbm7":  (n("Bb1"), ns("Db4 F4 Ab4"), ns("F5 Ab5 Db6 F6")),
    "Eb7":   (n("Eb2"), ns("Db4 G4 Bb4"), ns("G5 Bb5 Db6 Eb6")),
    "Ab/C":  (n("C3"), ns("Eb4 Ab4 C5"), ns("Ab5 C6 Eb6 Ab6")),
    "Cm":    (n("C3"), ns("Eb4 G4 C5"), ns("G5 C6 Eb6 G6")),
    "Eb/Db": (n("Db2"), ns("Bb3 Eb4 G4"), ns("G5 Bb5 Eb6 G6")),
    "Ebsus": (n("Eb2"), ns("Ab3 Bb3 Eb4"), ns("Ab5 Bb5 Eb6 Ab6")),
}
PROG_A = ["Ab", "Eb", "Db", "Ab", "Fm", "Db", "Bbm7", "Eb7",
          "Ab", "Eb", "Db", "Ab", "Db", "Ab/C", "Bbm7", "Ab"]
PROG_B = ["Fm", "Db", "Ab", "Eb", "Fm", "Db", "Bbm7", "Eb",
          "Db", "Eb/Db", "Cm", "Fm", "Bbm7", "Eb", "Db", "Ebsus"]

M = MOTIF_LANTERN
MOTIF = [[(b - 3 * k, d, x) for b, d, x in M if 3 * k <= b < 3 * k + 3] for k in range(4)]
MEL_A = MOTIF + [
    [(0, 2, "C5"), (2, 1, "Eb5")],
    [(0, 2, "F5"), (2, 1, "Eb5")],
    [(0, 1, "Db5"), (1, 1, "C5"), (2, 1, "Db5")],
    [(0, 3, "Eb5")],
] + MOTIF + [
    [(0, 1, "F5"), (1, 1, "Eb5"), (2, 1, "Db5")],
    [(0, 2, "C5"), (2, 1, "Bb4")],
    [(0, 1, "Ab4"), (1, 1, "Bb4"), (2, 1, "G4")],
    [(0, 3, "Ab4")],
]
MEL_B = [
    [(0, 3, "C6")], [(0, 2, "Ab5"), (2, 1, "F5")], [(0, 3, "Eb5")], [(0, 2, "G5"), (2, 1, "Bb5")],
    [(0, 3, "Ab5")], [(0, 2, "F5"), (2, 1, "Db5")], [(0, 1, "Db5"), (1, 1, "F5"), (2, 1, "Ab5")], [(0, 3, "G5")],
    [(0, 2, "F5"), (2, 1, "Ab5")], [(0, 3, "G5")], [(0, 2, "Eb5"), (2, 1, "G5")], [(0, 3, "F5")],
    [(0, 1, "Db5"), (1, 1, "F5"), (2, 1, "Bb5")], [(0, 2, "G5"), (2, 1, "Eb5")], [(0, 2, "F5"), (2, 1, "Ab5")],
    [(0, 3, "G5")],
]
COUNTER = {1: [(1, 2, "G5")], 3: [(1, 2, "C6")], 5: [(1, 2, "Ab5")], 7: [(1, 2, "Bb5")],     # celesta answers in A2
           9: [(1, 2, "G5")], 11: [(1, 2, "Eb6")], 13: [(1, 2, "Ab5")], 15: [(1, 2, "C6")]}

SEC = {"intro": 0, "A1": 8, "A2": 24, "B": 40, "A3": 56, "outro": 72}
END_BAR = 80
PROG = ["Ab", "Db", "Ab", "Db", "Ab", "Db", "Bbm7", "Eb7"] + PROG_A * 2 + PROG_B + PROG_A + \
       ["Ab", "Db", "Ab", "Db", "Ab", "Fm", "Db", "Ebsus"]
assert len(PROG) == END_BAR

T = Tempo(rubato(88, drift=0.015, breath_every=8, breath=0.10, meter=3, rit_from=72, rit_to=80, rit=0.42),
          meter=3, lead_in=0.8)
tb = T.tb
FERMATA = 9.0
LENGTH = tb(END_BAR) + FERMATA + 3

celesta = inst("celesta")
harp = inst("harp")
upright = inst("upright")
pad = surge_pad(cutoff=900.0, attack=2.5, release=4.0, detune=16.0, voices=4, reso=8.0, shape=0.0)
mbox_notes, sub_notes = [], []


def harp_waltz(bar, vel=50, chord_beats=(1, 2)):
    bass, mid, _ = CH[PROG[bar]]
    s = tb(bar) + H.t(0.006)
    harp.note(bass, s, s + 2.5, H.v(vel + 6))
    for b in chord_beats:
        for i, p in enumerate(mid[:2] if b == 2 else mid):
            s = tb(bar, b) + 0.012 * i + H.t(0.006)
            harp.note(p, s, s + 1.2, H.v(vel - 6 - 2 * i))


def harp_arp(bar, vel=46):                       # rising eighths across the bar, low to high
    bass, mid, high = CH[PROG[bar]]
    pool = [bass, bass + 7, mid[0], mid[1], mid[2], high[0]]
    for i, p in enumerate(pool):
        s = tb(bar, 0.5 * i) + H.t(0.006)
        harp.note(p, s, s + 2.0, H.v(vel + (6 if i == 0 else 0) - i))


def mbox_arp(bar, amp=0.16, pattern=(0, 2, 1, 3, 2, 1)):
    high = CH[PROG[bar]][2]
    for i, k in enumerate(pattern):
        if k is None:
            continue
        mbox_notes.append((high[k], tb(bar, 0.5 * i) + H.t(0.004), 0.5, amp * (1.2 if i == 0 else 1.0)))


def melody(target, bar0, mel, vel=60, up=0, amp=None, lag=0.015):
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + lag + H.t(0.006)
            en = tb(bar0 + i, b + d)
            if target == "mbox":
                mbox_notes.append((n(nm) + up, st, en - st, amp))
            else:
                target.note(n(nm) + up, st, en + 0.25, H.v(vel + (5 if b == 0 else 0)))


def sub_pulse(bar, amp=0.5):
    sub_notes.append((CH[PROG[bar]][0] - 12 if CH[PROG[bar]][0] >= n("Eb2") else CH[PROG[bar]][0],
                      tb(bar), tb(bar, 1.2), amp))


def upright_chords(bar, vel=34):
    _, mid, _ = CH[PROG[bar]]
    for b in (1, 2):
        for i, p in enumerate(mid):
            s = tb(bar, b) + 0.01 * i + H.t(0.006)
            upright.note(p - 12 if p > n("Ab4") else p, s, tb(bar, b + 0.85), H.v(vel - 2 * (b == 2)))


# --- intro: music box alone on an Ab/Db rocking figure, the sub pulse arrives halfway
for i in range(8):
    bar = SEC["intro"] + i
    mbox_arp(bar, amp=0.18)
    if i >= 4:
        sub_pulse(bar, amp=0.3)

# --- A1: celesta tune over harp waltz
for i in range(16):
    bar = SEC["A1"] + i
    harp_waltz(bar, vel=48)
    sub_pulse(bar, 0.45)
melody(celesta, SEC["A1"], MEL_A, vel=58)

# --- A2: upright sings, celesta answers on the held notes, pad enters
for i in range(16):
    bar = SEC["A2"] + i
    harp_waltz(bar, vel=46, chord_beats=(1, 2) if i % 4 != 3 else (1,))
    sub_pulse(bar, 0.5)
    for b, d, nm in COUNTER.get(i, []):
        st = tb(bar, b) + H.t(0.006)
        celesta.note(n(nm), st, tb(bar, b + d) + 0.2, H.v(44))
melody(upright, SEC["A2"], MEL_A, vel=52)
for bar in range(SEC["A2"], SEC["A2"] + 16):
    upright.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)

# --- B: F minor turn; harp and music box arpeggios, celesta high
for i in range(16):
    bar = SEC["B"] + i
    harp_arp(bar, vel=44)
    mbox_arp(bar, amp=0.11, pattern=(None, 2, None, 3, None, 1))
    sub_pulse(bar, 0.55)
melody(celesta, SEC["B"], MEL_B, vel=56)

# --- A3: everything; upright chords, celesta + music box an octave up on the tune
for i in range(16):
    bar = SEC["A3"] + i
    harp_waltz(bar, vel=52)
    upright_chords(bar, vel=32)
    sub_pulse(bar, 0.55)
    upright.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)
melody(celesta, SEC["A3"], MEL_A, vel=62)
melody("mbox", SEC["A3"], MEL_A, up=12, amp=0.12)

# --- outro: the music box alone, running down
for i in range(8):
    bar = SEC["outro"] + i
    mbox_arp(bar, amp=0.17 - 0.008 * i, pattern=(0, 2, 1, 3, 2, 1) if i < 6 else (0, None, 1, None, 2, None))
    if i < 4:
        sub_pulse(bar, 0.35 - 0.06 * i)
melody("mbox", SEC["outro"], MOTIF, up=12, amp=0.14)
fs = tb(END_BAR)
for i, p in enumerate(ns("Ab5 Eb6 C6 Ab6")):
    mbox_notes.append((p, fs + 0.35 * i * (1 + 0.3 * i), 2.0, 0.15 - 0.02 * i))
harp.note(n("Ab2"), fs, fs + 6, 36)
harp.note(n("Eb3"), fs + 0.05, fs + 6, 32)

# --- pad: from A2 to the end of A3
for bar in range(SEC["A2"], SEC["outro"] + 2):
    _, mid, _ = CH[PROG[bar]]
    for p in mid:
        pad.note(p, tb(bar) - 0.05, tb(bar + 1) + 0.1, 80)

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in SEC.items()) + f"  end {fs:.1f}")
cel = celesta.render(LENGTH)
hp = harp.render(LENGTH)
up = upright.render(LENGTH)
pd = pad.render(LENGTH)
mb = music_box(mbox_notes, LENGTH, seed=4)
sub = voice(sub_notes, LENGTH, harm=(1.0, 0.15), att=0.02, rel=0.5)

cel = rig.fx2(Pedalboard([HighpassFilter(200), PeakFilter(5000, -2, 0.8), LowpassFilter(9000)]), cel)
hp = rig.fx2(Pedalboard([HighpassFilter(60), PeakFilter(300, 1.5, 0.8), LowpassFilter(8000)]), hp)
up = rig.fx2(Pedalboard([HighpassFilter(60), PeakFilter(2800, -3, 0.9), LowpassFilter(5500),
                         Compressor(-26, 1.8, 20, 250)]), up)
pd = rig.fx2(Pedalboard([HighpassFilter(150), LowpassFilter(2400), Chorus(0.35, 0.3, 7, 0.0, 0.5)]), pd)
mb = rig.fx(Pedalboard([HighpassFilter(500), LowpassFilter(9500)]), mb)
sub = rig.fx(Pedalboard([LowpassFilter(150)]), sub)

cel = rig.at_level(cel, -22)
hp = rig.at_level(hp, -23)
up = rig.at_level(up, -22)
pd = rig.automate(rig.at_level(pd, -30), [(tb(SEC["B"]), tb(SEC["A3"]), 2.0)], ramp=4.0)
mb_st = rig.pan(rig.at_level(mb, -24), 0.25)
sub = rig.pan(rig.at_level(sub, -26), 0)

keys = cel + hp + up + mb_st
dry = keys + pd + sub
room = (rig.hall(keys, decay=2.8, size=30, predelay=20, high_cut=7000, early=14, late=78)
        + rig.hall(pd + mb_st * 0.6, decay=5.5, size=48, predelay=40, high_cut=6000, early=4, late=92) * 0.9)
mix = dry + room

sections = [(k, tb(v), tb(list(SEC.values())[i + 1]) if i + 1 < len(SEC) else LENGTH) for i, (k, v) in
            enumerate(SEC.items())]
master(mix, "04_lantern_waltz", sections=sections,
       stems={"celesta": cel, "harp": hp, "upright": up, "mbox": mb_st, "pad": pd, "sub": sub}, fade_s=3.0)
