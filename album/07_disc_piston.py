"""Disc: piston — track 7 of Volume Gamma. A quirky electronic-funk music disc in the manner of "blocks"/"chirp".
Original material.

D Dorian funk, 112 BPM with lightly swung 16ths. Hohner Pianet off-beat stabs, a Wurlitzer comping with tremolo,
a syncopated Surge saw bass, DRSKit funk kit with ghost notes, and a pulse-wave chiptune lead (kit.square_lead).
The breakdown strips to kick, rim and a filtered bass under chirping 16th blips, builds back with a snare roll and an
opening filter, and the end is a fake-out: the band stops dead and the lead gets the last word.

Form (bars): intro 4 | groove 16 | lead A 16 | B 8 | breakdown 8 + build 4 | lead A' 16 | outro 4 | stop + tag.
"""
import math

from kit import *

h = Human(707)
NAME = "07_disc_piston"
BPM = 112
SW16 = 0.555

CH = {  # (pianet/wurli voicing, bass root, chord type for the bass pattern)
    "Dm9": (ns("F3 A3 C4 E4"), n("D2"), "m"),
    "G13": (ns("F3 B3 E4 A4"), n("G1"), "7"),
    "Bbmaj7": (ns("F3 A3 D4 F4"), n("Bb1"), "M"),
    "C7": (ns("E3 Bb3 D4 G4"), n("C2"), "7"),
    "A7#9": (ns("G3 C#4 C5 E4"), n("A1"), "7"),
    "Am7": (ns("G3 C4 E4 A4"), n("A1"), "m"),
    "Gm7": (ns("F3 Bb3 D4 G4"), n("G1"), "m"),
    "Fmaj7": (ns("E3 A3 C4 F4"), n("F1"), "M"),
    "E7#9": (ns("D4 G#3 G4 B3"), n("E2"), "7"),
    "A7sus": (ns("G3 D4 E4 A4"), n("A1"), "s"),
    "A7": (ns("G3 C#4 E4 A4"), n("A1"), "7"),
}
VAMP = ["Dm9", "Dm9", "G13", "G13"]
LEADP = ["Dm9", "G13", "Dm9", "G13", "Bbmaj7", "C7", "Dm9", "A7#9"]
BP = ["Bbmaj7", "Am7", "Gm7", "C7", "Fmaj7", "E7#9", "A7sus", "A7"]
SEC = {"intro": 0, "groove": 4, "leadA": 20, "B": 36, "bd": 44, "build": 52, "leadA2": 56, "out": 72}
END = 76
PROG = VAMP + VAMP * 4 + LEADP * 2 + BP + VAMP * 3 + LEADP * 2 + VAMP
assert len(PROG) == END, len(PROG)


def bpm(b):
    return BPM


T = Tempo(bpm, lead_in=0.5)


def t(beat):
    """Beat -> seconds with swung 16ths."""
    q = math.floor(beat * 2 + 1e-9) / 2           # eighth-note cell
    f = (beat - q) * 2                              # 0..1 within the eighth
    f = f / 0.5 * SW16 if f <= 0.5 else SW16 + (f - 0.5) / 0.5 * (1 - SW16)
    return T.t(q + f / 2)


def tb(bar, beat=0.0):
    return t(bar * 4 + beat)


STOP = tb(END)
LENGTH = STOP + 8.0

pianet = inst("pianet")
wurli = inst("wurli")
bass = surge_bass(cutoff=900.0, shape=0.0, attack=0.003, release=0.08, vol=-4.0)
drums = rig.Drums()


def in_sec(bar, a, b):
    return SEC[a] <= bar < SEC[b]


# ---------------------------------------------------------------- Pianet stabs
STABS = [  # per bar, (beat, length) — two alternating patterns
    [(0.5, 0.18), (1.75, 0.12), (2.5, 0.18), (3.25, 0.12), (3.75, 0.2)],
    [(0.5, 0.18), (1.5, 0.12), (2.25, 0.12), (2.75, 0.3), (3.75, 0.12)],
]
for bar in range(END):
    if in_sec(bar, "bd", "build"):
        if bar % 2 == 1:                                  # breakdown: one echoing stab every two bars
            for p in CH[PROG[bar]][0]:
                pianet.note(p + 12, tb(bar, 2.5), tb(bar, 2.7), 70)
        continue
    pat = STABS[bar % 2]
    vel = 80 if bar >= SEC["groove"] else 70
    for b, ln in pat:
        st = tb(bar, b) + h.t(0.004)
        for j, p in enumerate(CH[PROG[bar]][0]):
            pianet.note(p, st + 0.003 * j, st + ln, h.v(vel - 2 * j, 4))

# ---------------------------------------------------------------- Wurlitzer: held chords in the lead sections + B
for bar in range(END):
    if in_sec(bar, "leadA", "bd") or in_sec(bar, "leadA2", "out"):
        v = CH[PROG[bar]][0]
        for b, ln in ((0, 1.6), (2, 1.4)) if bar % 2 == 0 else ((0, 3.6),):
            st = tb(bar, b) + h.t(0.006)
            for j, p in enumerate(v):
                wurli.note(p - 12 if j == 0 else p, st, tb(bar, b + ln), h.v(60))
# A' countermelody on the Wurli (low, lazy)
COUNTER = [(0, 1.5, "A3"), (2, 1, "C4"), (3, 1, "D4"), (4, 2, "B3"), (6, 2, "G3"), (8, 1.5, "F3"), (10, 2, "A3"),
           (12, 3, "B3"), (16, 2, "D4"), (18, 2, "F4"), (20, 1.5, "E4"), (22, 2, "C4"), (24, 2, "A3"), (26, 2, "D4"),
           (28, 3, "C#4")]
for rep in (0, 8):
    for b, d, nm in COUNTER:
        st = T.t((SEC["leadA2"] + rep) * 4 + b) + 0.02
        wurli.note(n(nm), st, T.t((SEC["leadA2"] + rep) * 4 + b + d), 74)

# ---------------------------------------------------------------- bass
BASS_PAT = {  # (beat, interval, length)
    "m": [(0, 0, 0.45), (0.75, 12, 0.2), (1.5, 10, 0.2), (2, 7, 0.4), (2.75, 0, 0.2), (3, 3, 0.2), (3.5, 5, 0.35)],
    "7": [(0, 0, 0.45), (0.75, 12, 0.2), (1.5, 10, 0.2), (2, 7, 0.4), (2.75, 0, 0.2), (3, 4, 0.2), (3.5, 5, 0.35)],
    "M": [(0, 0, 0.45), (0.75, 12, 0.2), (1.5, 11, 0.2), (2, 7, 0.4), (2.75, 0, 0.2), (3, 4, 0.2), (3.5, 7, 0.35)],
    "s": [(0, 0, 0.45), (0.75, 12, 0.2), (1.5, 10, 0.2), (2, 7, 0.4), (2.75, 0, 0.2), (3, 5, 0.2), (3.5, 7, 0.35)],
}
for bar in range(END):
    if bar < SEC["groove"]:
        continue
    root, typ = CH[PROG[bar]][1], CH[PROG[bar]][2]
    pat = BASS_PAT[typ]
    if in_sec(bar, "bd", "build"):
        pat = [x for x in pat if x[0] in (0, 2, 2.75)]
    for b, iv, ln in pat:
        st = tb(bar, b) + h.t(0.003)
        bass.note(root + iv, st, st + ln * 60 / BPM, h.v(100 if b == 0 else 88, 6))
    # fills into the next phrase: chromatic walk up
    if bar % 8 == 7 and not in_sec(bar, "bd", "build"):
        nxt = CH[PROG[(bar + 1) % END]][1]
        for k, iv in enumerate((-3, -2, -1)):
            st = tb(bar, 3.25 + 0.25 * k)
            bass.note(nxt + iv, st, st + 0.1, 92)


# ---------------------------------------------------------------- drums
def dh(name, beat, vel):
    drums.hit(name, t(beat) - 0.003 + h.t(0.003), vel + h.r.randint(-5, 5))


for bar in range(END):
    b0 = bar * 4
    if bar < SEC["groove"]:                              # intro: just hats coming in
        for i in range(16 if bar >= 2 else 8):
            step = i * (0.25 if bar >= 2 else 0.5)
            dh("hh_tight", b0 + step, 40 + (14 if (step * 2) % 1 == 0 else 0) + 3 * bar)
        if bar == SEC["groove"] - 1:
            for k, tom in enumerate(("tom1", "tom2", "tom3")):
                dh(tom, b0 + 3 + k * 0.25, 80)
        continue
    if in_sec(bar, "bd", "build"):                       # breakdown: kick, rim, foot hat
        dh("kick", b0, 92)
        dh("kick", b0 + 2.5, 70)
        dh("rim", b0 + 1, 70)
        dh("rim", b0 + 3, 74)
        for k in range(4):
            dh("hh_foot", b0 + k + 0.5, 50)
        continue
    if in_sec(bar, "build", "leadA2"):                   # build: snare 8ths -> 16ths, crescendo
        k = bar - SEC["build"]
        step = 0.5 if k < 2 else 0.25
        nsteps = int(4 / step)
        for i in range(nsteps):
            dh("snare", b0 + i * step, int(40 + 15 * k + 12 * i / nsteps))
        dh("kick", b0, 90)
        dh("kick", b0 + 2, 84)
        if bar == SEC["leadA2"] - 1:
            dh("kick", b0 + 3.5, 100)
        continue
    big = bar >= SEC["leadA"]
    # kick
    for b, v in ((0, 104), (0.75, 70), (2.5, 92), (3.25, 64)) if bar % 2 == 0 else ((0, 104), (1.75, 76), (2.5, 90)):
        dh("kick", b0 + b, v)
    # snare + ghosts
    dh("snare", b0 + 1, 100)
    dh("snare", b0 + 3, 104)
    for g in (0.5, 1.75, 2.25, 3.75) if bar % 2 else (1.25, 2.75, 3.5):
        if h.r.random() < 0.8:
            dh("snare", b0 + g, h.r.randint(20, 34))
    # hats: 16ths with accents, open on the "and" of 4
    for i in range(16):
        b = b0 + i * 0.25
        if i == 14:
            dh("hh_open", b, 70)
            continue
        if i == 15:
            dh("hh_foot", b, 50)
            continue
        dh("hh_closed" if i % 2 == 0 else "hh_tight", b, (66 if i % 4 == 0 else 54 if i % 2 == 0 else 38) +
           (6 if big else 0))
    if bar % 8 == 0:
        dh("crash_l" if bar % 16 == 0 else "crash_r", b0, 84)
    if bar % 8 == 7:                                      # small fill
        dh("tom1", b0 + 3.0, 70)
        dh("tom2", b0 + 3.25, 74)
        dh("tom3", b0 + 3.5, 80)
# the stop
drums.hit("kick", STOP, 110)
drums.hit("crash_l", STOP, 100)
drums.hit("crash_r", STOP + 0.01, 90)
drums.hit("hh_closed", STOP + 4.45, 60)
drums.hit("kick", STOP + 4.45, 70)

# final Pianet stab on the stop
for j, p in enumerate(CH["Dm9"][0]):
    pianet.note(p, STOP + 0.003 * j, STOP + 0.35, 96)
bass.note(n("D2"), STOP, STOP + 0.5, 110)

# ---------------------------------------------------------------- square lead
LEAD = [
    [(0, 0.75, "D5"), (0.75, 0.25, "F5"), (1, 0.5, "A5"), (1.5, 0.5, "G5"), (2.5, 0.5, "F5"), (3, 1, "E5")],
    [(0, 0.5, "D5"), (0.5, 0.5, "B4"), (1, 1, "C5"), (2.5, 0.25, "E5"), (2.75, 0.25, "F5"), (3, 1, "G5")],
    [(0, 0.75, "A5"), (0.75, 0.25, "C6"), (1, 0.5, "A5"), (1.5, 0.5, "G5"), (2, 0.5, "F5"), (2.5, 0.5, "D5"),
     (3.5, 0.5, "E5")],
    [(0, 1.5, "F5"), (1.5, 0.5, "E5"), (2, 2, "B4")],
    [(0, 0.5, "D5"), (0.5, 0.5, "F5"), (1, 0.5, "A5"), (1.5, 1.5, "Bb5"), (3.5, 0.5, "A5")],
    [(0, 1, "G5"), (1, 0.5, "E5"), (1.5, 0.5, "C5"), (2, 2, "E5")],
    [(0, 0.5, "F5"), (0.5, 0.5, "E5"), (1, 0.5, "D5"), (1.5, 0.5, "A4"), (2, 1, "C5"), (3, 1, "D5")],
    [(0, 0.5, "C#5"), (0.5, 0.5, "E5"), (1, 0.5, "G5"), (1.5, 0.5, "C6"), (2, 0.5, "Bb5"), (2.5, 1.5, "A5")],
]
LEAD_B = [
    [(0, 1, "F5"), (1, 1, "D5"), (2, 0.5, "A5"), (2.5, 1, "F5")],
    [(0, 1, "E5"), (1, 1, "C5"), (2, 0.5, "G5"), (2.5, 1, "E5")],
    [(0, 1, "D5"), (1, 1, "Bb4"), (2, 0.5, "F5"), (2.5, 1, "D5")],
    [(0, 0.5, "E5"), (0.5, 0.5, "G5"), (1, 0.5, "Bb5"), (1.5, 0.5, "C6"), (2, 2, "E6")],
    [(0, 3, "A5"), (3, 0.5, "G5"), (3.5, 0.5, "F5")],
    [(0, 1, "G#5"), (1, 0.5, "G5"), (1.5, 0.5, "E5"), (2, 2, "B4")],
    [(0, 1, "D5"), (1, 1, "E5"), (2, 2, "G5")],
    [(0, 2, "C#5"), (2, 0.5, "E5"), (2.5, 0.5, "G5"), (3, 1, "Bb5")],
]


def mel(bar0, m, amp=0.5, octave=0, stacc=0.85):
    out = []
    for i, notes in enumerate(m):
        for b, d, nm in notes:
            st = tb(bar0 + i, b) + h.t(0.003)
            out.append((n(nm) + octave, st, st + (tb(bar0 + i, b + d) - st) * stacc, amp))
    return out


lead_n = (mel(SEC["leadA"], LEAD) + mel(SEC["leadA"] + 8, LEAD) + mel(SEC["B"], LEAD_B, 0.5, stacc=0.95)
          + mel(SEC["leadA2"], LEAD) + mel(SEC["leadA2"] + 8, LEAD))
lead_lo = mel(SEC["leadA2"], LEAD, 0.35, -12) + mel(SEC["leadA2"] + 8, LEAD, 0.35, -12) + \
    mel(SEC["B"], LEAD_B, 0.3, -12, stacc=0.95)
# grace-note "chirps" on long notes: a 1/32 flick from a step below
for p, s, e, a in list(lead_n):
    if e - s > 0.4 and h.r.random() < 0.35:
        lead_n.append((p - 2, s - 0.045, s - 0.005, a * 0.8))

# breakdown blips: random 16th arpeggio across the Dm9/G13 chord tones, two octaves up, sparse
blips = []
for bar in range(SEC["bd"], SEC["leadA2"]):
    tones = [p + 24 for p in CH[PROG[bar]][0]] + [CH[PROG[bar]][1] + 36]
    dens = 0.35 + 0.5 * (bar - SEC["bd"]) / 12
    for i in range(16):
        if h.r.random() < dens:
            st = tb(bar, i * 0.25)
            blips.append((h.r.choice(tones), st, st + 0.06, 0.3))
# the tag after the stop: a descending chromatic giggle and one low boop
tag = [(n(x), STOP + 1.6 + 0.11 * k, STOP + 1.6 + 0.11 * k + 0.08, 0.5) for k, x in
       enumerate(["D6", "C#6", "C6", "B5", "Bb5", "A5"])]
tag += [(n("A5"), STOP + 2.5, STOP + 2.62, 0.45), (n("D6"), STOP + 2.75, STOP + 3.6, 0.5)]
boop = [(n("D2"), STOP + 4.45, STOP + 4.75, 0.6)]

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  groove {tb(4):.1f}  leadA {tb(20):.1f}  B {tb(36):.1f}  bd {tb(44):.1f}  "
      f"A2 {tb(56):.1f}  stop {STOP:.1f}")
pn = pianet.render(LENGTH)
wu = wurli.render(LENGTH)
bs = bass.render(LENGTH)
ch = drums.render(LENGTH)
ld = square_lead(lead_n, LENGTH, duty=0.25, att=0.005, rel=0.06, vib=18, seed=1)
ld_lo = square_lead(lead_lo, LENGTH, duty=0.5, att=0.005, rel=0.06, seed=2)
bl = square_lead(blips, LENGTH, duty=0.125, att=0.002, rel=0.03, seed=3)
tg = square_lead(tag, LENGTH, duty=0.25, att=0.003, rel=0.05, vib=25, seed=4) + voice(boop, LENGTH, harm=(1, .3),
                                                                                        att=0.005, rel=0.1)

# intro: Pianet through an opening low-pass; breakdown: bass under a closing/opening filter
nn = int(LENGTH * SR)
tt = np.arange(nn) / SR
fc_p = np.full(nn, 18000.0, np.float32)
i_open = int(tb(SEC["groove"]) * SR)
fc_p[:i_open] = (300 * (60 ** np.linspace(0, 1, i_open) ** 1.5)).astype(np.float32)
pn = np.stack([rave.svf(c, fc_p, 1.4, "lp") for c in pn])
fc_b = np.full(nn, 18000.0, np.float32)
a, b_, c_ = int(tb(SEC["bd"]) * SR), int(tb(SEC["build"]) * SR), int(tb(SEC["leadA2"]) * SR)
fc_b[a:b_] = (350 + 150 * np.sin(2 * np.pi * 0.25 * tt[a:b_]) ** 2).astype(np.float32)
fc_b[b_:c_] = (500 * (30 ** np.linspace(0, 1, c_ - b_) ** 2)).astype(np.float32)
bs = np.stack([rave.svf(c, fc_b, 2.2, "lp") for c in bs])
wu = np.stack([rave.svf(c, np.minimum(fc_b, 18000).astype(np.float32), 1.0, "lp") for c in wu])

# wurli tremolo / autopan
trem = 0.5 + 0.5 * np.sin(2 * np.pi * 5.2 * tt)
wu = np.stack([wu[0] * (0.6 + 0.4 * trem), wu[1] * (1.0 - 0.4 * trem)])

pn = rig.fx2(Pedalboard([HighpassFilter(120), PeakFilter(1800, 2, 1), Compressor(-22, 3, 5, 100)]), pn)
wu = rig.fx2(Pedalboard([HighpassFilter(90), Chorus(0.5, 0.2, 7, 0, 0.3)]), wu)
bs = rig.fx2(Pedalboard([HighpassFilter(30), PeakFilter(100, 3, 1), Distortion(6), LowpassFilter(3500),
                         Compressor(-20, 4, 5, 80)]), bs)
kit_ = rig.drum_bus(ch, close=1.0, room=0.5, kick_db=0, snare_db=-1, hat_db=0, tom_db=-2, oh_db=0)
kit_ = rig.fx2(Pedalboard([HighpassFilter(35), Compressor(-18, 3, 10, 120)]), kit_)
ld = rig.fx(Pedalboard([HighpassFilter(250), LowpassFilter(7000)]), ld)
ld_lo = rig.fx(Pedalboard([HighpassFilter(200), LowpassFilter(4000)]), ld_lo)
bl = rig.fx(Pedalboard([HighpassFilter(500)]), bl)

pn = rig.at_level(pn, -21.5)
wu = rig.at_level(wu, -27)
bs = rig.at_level(bs, -19)
kit_ = rig.at_level(kit_, -19.5)
ld_st = rig.pan(rig.at_level(ld, -19.5), 0) + rig.pan(rig.at_level(ld_lo, -28), 0.2)
bl_st = rig.fx2(Pedalboard([Delay(0.4018, 0.45, 0.4)]), rig.pan(rig.at_level(bl, -29), -0.35))
tg_st = rig.pan(rig.at_level(tg, -21), 0)
pn_st = np.stack([pn[0] * 1.15, pn[1] * 0.8])

dry = pn_st + wu + bs + kit_ + ld_st + bl_st + tg_st
wet = rig.hall(0.6 * pn_st + 0.4 * wu + 0.35 * ld_st + 0.6 * bl_st + 0.15 * kit_ + 0.7 * tg_st, decay=1.4,
               size=20, predelay=12, high_cut=8000, early=20, late=60)
mix = dry + wet

sections = [("intro", 0, tb(4)), ("groove", tb(4), tb(20)), ("leadA", tb(20), tb(36)), ("B", tb(36), tb(44)),
            ("breakdown", tb(44), tb(52)), ("build", tb(52), tb(56)), ("leadA2", tb(56), tb(72)),
            ("outro", tb(72), STOP), ("stop+tag", STOP, LENGTH)]
master(mix, NAME, sections, {"pianet": pn_st, "wurli": wu, "bass": bs, "drums": kit_, "lead": ld_st,
                             "blips": bl_st}, fade_s=1.5, target_rms_db=-16.0,
       tape_kw={"wow_cents": 2.5, "flutter_cents": 1.0, "hiss_db": -70})
