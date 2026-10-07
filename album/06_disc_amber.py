"""Disc: amber — track 6 of Volume Gamma. A music-disc lounge tune in the manner of "stal". Original material.

Ab Dorian (written a tone higher, in Bb, and transposed for the sax range), medium swing ~100 BPM. Tenor sax (MTG, played legato with expression swells and delayed vibrato) over
rootless Rhodes comping, a walking pizzicato double bass and a soft DRSKit played like brushes (swirled snare at
whisper velocities, hi-hat foot on 2 & 4) that moves to the ride for the solo.

16-bar form:  Bbm9 | Bbm9 | Ebm9 | Ab13 | Dbmaj9 | Gbmaj7#11 | Cm7b5 F7b9 | Bbm9 |
              Bbm9 | Eb13 | Abm9 Db13 | Gbmaj7 | Cm7b5 | F7b9 | Bbm9 | F7b9 |
Form: intro 4 (Rhodes + bass) | head 16 | sax solo 32 (two choruses, building) | head 16 | tag 4 + held chord.
"""
import math

from kit import *

h = Human(606)
NAME = "06_disc_amber"
BPM = 100
SWING = 0.63
KEY = -2          # written in Bb Dorian, sounds in Ab Dorian (keeps the sax under its top sample, E5)


class Chord:
    def __init__(self, root, tones, scale, voicing):
        self.root, self.tones, self.scale, self.voicing = root, tones, scale, voicing


DOR, MIX, ION, LYD, LOC, PHD = ([0, 2, 3, 5, 7, 9, 10], [0, 2, 4, 5, 7, 9, 10], [0, 2, 4, 5, 7, 9, 11],
                                [0, 2, 4, 6, 7, 9, 11], [0, 1, 3, 5, 6, 8, 10], [0, 1, 4, 5, 7, 8, 10])
# rootless voicings as intervals above the root (folded into the comping register later)
C = {
    "Bbm9": Chord(10, [0, 3, 7, 10, 14], DOR, [3, 7, 10, 14]),
    "Ebm9": Chord(3, [0, 3, 7, 10, 14], DOR, [3, 7, 10, 14]),
    "Abm9": Chord(8, [0, 3, 7, 10, 14], DOR, [3, 7, 10, 14]),
    "Ab13": Chord(8, [0, 4, 7, 10, 14, 21], MIX, [10, 14, 16, 21]),
    "Eb13": Chord(3, [0, 4, 7, 10, 14, 21], MIX, [10, 14, 16, 21]),
    "Db13": Chord(1, [0, 4, 7, 10, 14, 21], MIX, [10, 14, 16, 21]),
    "Dbmaj9": Chord(1, [0, 4, 7, 11, 14], ION, [4, 7, 11, 14]),
    "Gbmaj7#11": Chord(6, [0, 4, 7, 11, 18], LYD, [4, 6, 11, 14]),
    "Gbmaj7": Chord(6, [0, 4, 7, 11], ION, [4, 7, 11, 14]),
    "Cm7b5": Chord(0, [0, 3, 6, 10], LOC, [3, 6, 10, 12]),
    "F7b9": Chord(5, [0, 4, 7, 10, 13], PHD, [4, 10, 13, 20]),
}
FORM = [[("Bbm9", 4)], [("Bbm9", 4)], [("Ebm9", 4)], [("Ab13", 4)], [("Dbmaj9", 4)], [("Gbmaj7#11", 4)],
        [("Cm7b5", 2), ("F7b9", 2)], [("Bbm9", 4)],
        [("Bbm9", 4)], [("Eb13", 4)], [("Abm9", 2), ("Db13", 2)], [("Gbmaj7", 4)], [("Cm7b5", 4)], [("F7b9", 4)],
        [("Bbm9", 4)], [("F7b9", 4)]]
INTRO = [[("Bbm9", 4)], [("Bbm9", 4)], [("Bbm9", 4)], [("F7b9", 4)]]
TAG = [[("Cm7b5", 2), ("F7b9", 2)], [("Bbm9", 4)], [("Cm7b5", 2), ("F7b9", 2)], [("Bbm9", 4)]]
BARS = INTRO + FORM + FORM + FORM + FORM + TAG
SEC = {"intro": 0, "head": 4, "solo": 20, "solo2": 36, "head2": 52, "tag": 68}
END = len(BARS)                                        # 72; final chord at bar 72
assert END == 72

CHORDS = []
for i, bar in enumerate(BARS):
    b = 4 * i
    for c, nb in bar:
        CHORDS.append((b, nb, C[c]))
        b += nb


def chord_at(beat):
    for s, nb, c in CHORDS:
        if s <= beat + 1e-6 < s + nb:
            return c
    return C["Bbm9"]


# ---------------------------------------------------------------- swing time
def bpm(b):
    tp = BPM * (1 + 0.005 * math.sin(2 * math.pi * b / 37))
    if b > (END - 2) * 4:
        tp *= max(0.7, 1 - 0.3 * (b - (END - 2) * 4) / 8)
    return tp


T = Tempo(bpm, lead_in=0.6)


def t(beat, swing=True):
    b = math.floor(beat + 1e-9)
    f = beat - b
    trip = abs(f * 3 - round(f * 3)) < 1e-6 and round(f * 3) in (1, 2)
    if swing and not trip:
        f = f / 0.5 * SWING if f <= 0.5 else SWING + (f - 0.5) / 0.5 * (1 - SWING)
    return T.t(b + f)


def tbar(bar, beat=0.0):
    return t(bar * 4 + beat)


FS = tbar(END)
LENGTH = FS + 9.0

sax = Sampler(INST["tenor_sax"], transpose=KEY, legato=True, ccs={64: 127, 1: 0, 3: 50, 80: 30, 11: 100, 72: 30})
rhodes = inst("rhodes", transpose=KEY)
bass = Sampler(INST["contrabass_jazz"], transpose=KEY)
drums = rig.Drums()

# ---------------------------------------------------------------- Rhodes comping
_prev_center = [62.0]


def voicing(c):
    """Rootless voicing in E3..D5, voice-led towards the previous chord."""
    best, cost = None, 1e9
    for o in range(3, 6):
        base = c.root + 12 * o
        v = sorted(base + i for i in c.voicing)
        for inv in range(4):
            vv = sorted(v[inv:] + [x + 12 for x in v[:inv]])
            if vv[0] < 51 or vv[-1] > 75:
                continue
            k = abs(np.mean(vv) - _prev_center[0]) + abs(np.mean(vv) - 62) * 0.4
            if k < cost:
                best, cost = vv, k
    _prev_center[0] = float(np.mean(best))
    return best


COMP = [  # rhythmic cells per 2 beats: (offset, length) in beats
    [(0, 1.3)], [(0.5, 0.4)], [(-0.5, 1.5)], [(1, 0.8)], [(0, 0.4), (1.5, 0.45)], [], [(2 / 3, 1.2)],
]


def comp(start_beat, end_beat, vel=52, density=0.8):
    for s, nb, c in CHORDS:
        if not (start_beat <= s < end_beat):
            continue
        v = voicing(c)
        for half in range(0, nb, 2):
            cells = COMP if h.r.random() < density else [[]]
            for off, ln in h.r.choice(cells):
                b0 = s + half + off
                st = t(b0) + h.t(0.006)
                en = t(b0 + ln)
                vel_k = h.v(vel + (6 if off < 0 else 0), 6)
                for j, p in enumerate(v):
                    rhodes.note(p, st + 0.006 * j, en, vel_k - 2 * j)


comp(SEC["intro"] * 4, SEC["head"] * 4, vel=56, density=1.0)
comp(SEC["head"] * 4, SEC["solo"] * 4, vel=50, density=0.75)
comp(SEC["solo"] * 4, SEC["solo2"] * 4, vel=52, density=0.8)
comp(SEC["solo2"] * 4, SEC["head2"] * 4, vel=58, density=0.95)
comp(SEC["head2"] * 4, SEC["tag"] * 4, vel=50, density=0.75)
comp(SEC["tag"] * 4, END * 4, vel=48, density=0.7)
# intro: a little Rhodes pickup line on top
for b, d, nm in [(2.5, 0.5, "Db5"), (3, 0.5, "C5"), (3.5, 1.5, "Ab4"), (10, 0.5, "F4"), (10.5, 0.5, "Ab4"),
                 (11, 1, "C5"), (12, 2, "Bb4"), (14.5, 0.5, "A4"), (15, 1, "Eb5")]:
    rhodes.note(n(nm), t(b) + 0.01, t(b + d), h.v(60))
# final chord
for j, nm in enumerate(["Bb2", "Ab3", "Db4", "F4", "G4", "C5"]):
    rhodes.note(n(nm), FS + 0.05 * j, FS + 7.5, 54 - j)
rhodes.pedal(FS - 0.02, FS + 8)

# ---------------------------------------------------------------- walking bass
LO, HI = 28, 50
_bprev = [34]


def bnote(pitch, beat, beats, vel):
    s = t(beat) - 0.008 + h.t(0.004)
    e = t(beat + beats) - 0.02
    bass.note(pitch, s, max(s + 0.06, e), vel)


def near(pc, ref):
    cands = [pc + 12 * o for o in range(1, 6) if LO <= pc + 12 * o <= HI]
    return min(cands, key=lambda p: abs(p - ref) + h.r.random() * 3)


def walk(start, end, two_feel=False):
    spans = [(s, nb, c) for s, nb, c in CHORDS if start * 4 <= s < end * 4]
    for i, (s, nb, c) in enumerate(spans):
        nxt = spans[i + 1][2] if i + 1 < len(spans) else chord_at(s + nb)
        first = near(c.root, _bprev[0])
        target = near(nxt.root, first)
        app = target + h.r.choice([-1, 1, 1, -1, 7 if target + 7 <= HI else -1, -2])
        if two_feel:
            if nb == 4:
                bnote(first, s, 2, 96)
                bnote(near((c.root + 7) % 12, first) if h.r.random() < 0.6 else app, s + 2, 2, 88)
            else:
                bnote(first, s, nb, 94)
            _bprev[0] = first
            continue
        line = [first]
        pool = [p for p in range(LO, HI + 1) if (p - c.root) % 12 in c.scale]
        for k in range(1, nb - 1):
            prev = line[-1]
            step = [p for p in pool if 1 <= abs(p - prev) <= 4 and p != prev]
            tones = [p for p in step if (p - c.root) % 12 in c.tones]
            line.append(h.r.choice(tones if tones and h.r.random() < 0.6 else step or [prev]))
        if nb >= 2:
            line.append(app)
        for k, p in enumerate(line):
            bnote(p, s + k, 1, 90 + (6 if k % 2 else 0) + h.r.randint(-6, 6))
        _bprev[0] = line[-1]


walk(SEC["intro"], SEC["head"], two_feel=True)
walk(SEC["head"], SEC["head"] + 8, two_feel=True)
walk(SEC["head"] + 8, SEC["head2"])
walk(SEC["head2"], SEC["head2"] + 8, two_feel=True)
walk(SEC["head2"] + 8, END)
bass.note(n("Bb1"), FS, FS + 5.5, 96)


# ---------------------------------------------------------------- drums (brushes-ish -> ride for the solo)
def dh(name, beat, vel, swing=True):
    drums.hit(name, t(beat, swing) - 0.004 + h.t(0.004), vel + h.r.randint(-4, 4))


for bar in range(SEC["head"] - 1, END):
    b0 = bar * 4
    ride = SEC["solo"] <= bar < SEC["head2"]
    for k in range(4):
        b = b0 + k
        if ride:
            dh("ride", b, 58 + (6 if k in (1, 3) else 0) + (6 if bar >= SEC["solo2"] else 0))
            if k in (1, 3):
                dh("ride", b + 0.5, 44)
            if h.r.random() < (0.2 if bar < SEC["solo2"] else 0.35):
                dh("snare", b + h.r.choice([0.5, 2 / 3, 1 / 3]), h.r.randint(24, 42))
        else:  # "brushes": swirl of whisper-quiet snare triplets plus a soft slap on 2 & 4
            for f in (0, 1 / 3, 2 / 3):
                dh("snare", b + f, h.r.randint(4, 9), swing=False)
            if k in (1, 3):
                dh("snare", b, 22)
        if k in (1, 3):
            dh("hh_foot", b, 56)
        dh("kick", b, 18)
    if bar in (SEC["solo"] - 1, SEC["solo2"] - 1, SEC["head2"] - 1, SEC["tag"] - 1):
        dh("snare", b0 + 3 + 2 / 3, 46)
        dh("kick", b0 + 3.5, 54)
        drums.hit("crash_r", tbar(bar + 1), 58)
drums.hit("crash_r", FS, 52)
for i in range(50):                                          # soft cymbal swell on the held chord
    drums.hit("ride", FS + 0.09 * i, int(22 + 22 * math.sin(math.pi * i / 50)))


# ---------------------------------------------------------------- sax: the head
HEAD = [
    [(1, 0.5, "F4"), (1.5, 0.5, "Ab4"), (2, 1.5, "Db5"), (3.5, 0.5, "C5")],
    [(0, 3, "Bb4"), (3.5, 0.5, "Ab4")],
    [(0, 1.5, "Gb4"), (1.5, 0.5, "Bb4"), (2, 1, "Db5"), (3, 1, "F5")],
    [(0, 2, "Eb5"), (2, 0.5, "C5"), (2.5, 1.5, "F5")],
    [(0, 3, "Eb5"), (3.5, 0.5, "C5")],
    [(0, 1.5, "Bb4"), (1.5, 0.5, "C5"), (2, 2, "F5")],
    [(0, 1, "Eb5"), (1, 1, "C5"), (2, 1, "A4"), (3, 1, "Gb4")],
    [(0, 3, "F4")],
    [(1, 0.5, "Ab4"), (1.5, 0.5, "Bb4"), (2, 1.5, "F5"), (3.5, 0.5, "Eb5")],
    [(0, 2, "Db5"), (2, 1, "C5"), (3, 1, "G4")],
    [(0, 1, "Gb4"), (1, 1, "B4"), (2, 1, "Bb4"), (3, 1, "F4")],
    [(0, 2, "Bb4"), (2, 0.5, "Ab4"), (2.5, 1.5, "F5")],
    [(0, 2, "Eb5"), (2, 2, "Gb5")],
    [(0, 1, "F5"), (1, 0.5, "Eb5"), (1.5, 0.5, "Db5"), (2, 1, "C5"), (3, 1, "A4")],
    [(0, 4, "Bb4")],
    [(2, 0.5, "A4"), (2.5, 0.5, "C5"), (3, 0.5, "Eb5"), (3.5, 0.5, "Gb5")],
]
sax_lines = []                    # (pitch, start_beat, beats, vel)


def head(bar0, last_bar_tail=True):
    for i, notes in enumerate(HEAD):
        if i == 15 and not last_bar_tail:
            continue
        for b, d, nm in notes:
            sax_lines.append((n(nm), bar0 * 4 + i * 4 + b, d, 92 if b == 0 else 86))


head(SEC["head"])
head(SEC["head2"], last_bar_tail=False)


# ---------------------------------------------------------------- sax: the solo (seeded improviser)
CELLS = [  # rhythmic cells over 2 beats (offsets, durations)
    ([0, 0.5, 1, 1.5], [0.5] * 4),                  # four swung 8ths
    ([0, 1], [1, 1]),
    ([0, 1 / 3, 2 / 3, 1], [1 / 3, 1 / 3, 1 / 3, 1]),  # triplet into quarter
    ([0.5, 1, 1.5], [0.5, 0.5, 0.5]),               # off-beat start
    ([0], [2]),
    ([0, 1.5], [1.5, 0.5]),
    ([0, 0.5, 1], [0.5, 0.5, 1]),
]


def improvise(start_bar, bars, lo, hi, busy):
    beat = start_bar * 4 + h.r.choice([0, 0.5, 1])
    end = (start_bar + bars) * 4
    prev = h.r.choice([n("F4"), n("Bb4"), n("Db5")])
    phrase_left = h.r.randint(4, 8)
    while beat < end - 1:
        if phrase_left <= 0:                      # breathe
            beat += h.r.choice([1, 1.5, 2, 2.5, 3]) * (1.3 - busy * 0.6)
            phrase_left = h.r.randint(4, 7) + int(busy * 6)
            continue
        weights = [3 * busy + 0.5, 1.2, 1.5 * busy + 0.3, 1.0, 1.0 - busy * 0.6, 1.0, 1.5]
        offs, durs = h.r.choices(CELLS, weights)[0]
        for o, d in zip(offs, durs):
            b = beat + o
            if b >= end:
                break
            c = chord_at(b)
            strong = abs(b - round(b)) < 1e-6
            pool = [p for p in range(lo, hi + 1) if (p - c.root) % 12 in (c.tones if strong else c.scale)]
            # mostly steps, sometimes leaps; drift towards the middle of the range
            cand = [p for p in pool if 1 <= abs(p - prev) <= (5 if h.r.random() < 0.8 else 9)] or pool
            mid = (lo + hi) / 2
            p = min(cand, key=lambda x: abs(x - prev) * h.r.uniform(0.5, 1.5) + abs(x - mid) * 0.15
                    + (h.r.random() * 3))
            if not strong and h.r.random() < 0.12:            # chromatic passing tone
                p = prev + (1 if p > prev else -1)
            sax_lines.append((p, b, d * 0.95, h.r.randint(80, 100) + (6 if strong else 0)))
            prev = p
        beat += 2
        phrase_left -= 2
    # end on a long chord tone
    c = chord_at(end - 1)
    tone = min((p for p in range(lo, hi + 1) if (p - c.root) % 12 in c.tones[:4]), key=lambda x: abs(x - prev))
    sax_lines.append((tone, end - 1.5, 1.5, 90))


improvise(SEC["solo"], 8, n("Db4"), n("Db5"), 0.25)
improvise(SEC["solo"] + 8, 8, n("Eb4"), n("Eb5"), 0.45)
improvise(SEC["solo2"], 8, n("F4"), n("F5"), 0.65)
improvise(SEC["solo2"] + 8, 6, n("Ab4"), n("F#5"), 0.85)
# climb back into the head: a written break in the last two bars
for b, d, nm in [(0, 1, "Gb5"), (1, 0.5, "F5"), (1.5, 0.5, "Eb5"), (2, 0.5, "Db5"), (2.5, 0.5, "C5"),
                 (3, 1, "Bb4"), (4, 1.5, "A4"), (6, 0.5, "C5"), (6.5, 0.5, "Eb5"), (7, 0.5, "Gb5"), (7.5, 0.5, "F5")]:
    sax_lines.append((n(nm), (SEC["head2"] - 2) * 4 + b, d, 94))

# tag: answers in the gaps, then the long last note
for b, d, nm in [(2, 0.5, "Eb5"), (2.5, 0.5, "Db5"), (3, 1, "C5"), (4, 3, "Bb4"), (10, 0.5, "Gb4"), (10.5, 0.5, "A4"),
                 (11, 0.5, "C5"), (11.5, 0.5, "Eb5"), (12, 3.5, "Db5")]:
    sax_lines.append((n(nm), SEC["tag"] * 4 + b, d, 88))
sax_lines.append((n("F4"), END * 4 + 0.0, 0, 84))      # placeholder replaced below by the held final note

# drop overlapping notes (monophonic), set the CCs: expression swell per note, vibrato on long notes
sax_lines.sort(key=lambda x: x[1])
clean = []
for x in sax_lines:
    if clean and x[1] < clean[-1][1] + 1e-6:
        continue
    clean.append(x)
for i, (p, b, d, v) in enumerate(clean):
    if b >= END * 4:
        st = FS + 0.25
        sax.note(p, st, st + 6.0, v)
        sax.cc(st, 11, 70)
        for k in range(30):
            sax.cc(st + 0.2 * k, 11, int(70 + 30 * math.sin(math.pi * min(1, k / 12))) if k < 22 else 100 - 4 * (k - 21))
            sax.cc(st + 0.2 * k, 1, min(90, 10 + 6 * k))
        continue
    st = t(b) + 0.012 + h.t(0.008)
    en = t(b + d) + 0.01
    sax.note(p, st, en, v)
    long_ = en - st > 0.8
    sax.cc(st, 1, 0)
    sax.cc(st, 11, 92 if long_ else 104)
    if long_:
        sax.cc(st + 0.45, 1, 55)
        sax.cc(st + 0.25, 11, 108)
        sax.cc(en - 0.1, 11, 88)

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s  head {tbar(4):.1f}  solo {tbar(20):.1f}  head2 {tbar(52):.1f}  tag {tbar(68):.1f}")
sx = sax.render(LENGTH)
rh = rhodes.render(LENGTH)
bs = bass.render(LENGTH).mean(0)
ch = drums.render(LENGTH)

_m = sx.mean(0)
_sil = [nt for nt in sax.notes if np.sqrt(np.mean(_m[int(nt.start * SR):int(min(nt.end, nt.start + 0.3) * SR)] ** 2)) < 1e-4]
print(f"sax notes {len(sax.notes)}, silent {len(_sil)}", [(x.pitch, round(x.start, 1)) for x in _sil[:8]])
sx = rig.fx2(Pedalboard([HighpassFilter(90), PeakFilter(300, -2, 1.0), PeakFilter(2500, 1.5, 1.0),
                         HighShelfFilter(9000, -2), Compressor(-22, 2.5, 10, 160)]), sx)
rh = rig.fx2(Pedalboard([HighpassFilter(80), PeakFilter(400, -2, 1), Chorus(0.6, 0.2, 7, 0, 0.35),
                         Compressor(-24, 2, 15, 200)]), rh)
bs = rig.fx(Pedalboard([HighpassFilter(35), PeakFilter(90, 3, 1), PeakFilter(700, 2, 1.2),
                        Compressor(-22, 3, 8, 150)]), bs)
kit_ = rig.drum_bus(ch, close=0.6, room=0.9, kick_db=-10, snare_db=-3, hat_db=-2, tom_db=-2, oh_db=3)
kit_ = rig.fx2(Pedalboard([HighpassFilter(40), LowpassFilter(9000), Compressor(-22, 2, 20, 200)]), kit_)

sx = rig.at_level(sx, -18.5)
rh = rig.at_level(rh, -22)
bs = rig.pan(rig.at_level(bs, -21), 0.05)
kit_ = rig.at_level(kit_, -26)
kit_ = rig.automate(kit_, [(0, tbar(SEC["solo"]), -3.0), (tbar(SEC["head2"]), LENGTH, -3.0)], ramp=0.5)
sx_st = np.stack([sx[0] * 1.05, sx[1] * 0.92]) if sx.ndim == 2 else rig.pan(sx, -0.1)
rh_st = np.stack([rh[0] * 0.8, rh[1] * 1.15])
dry = sx_st + rh_st + bs + kit_
room = (rig.hall(0.5 * sx_st + 0.4 * rh_st + 0.25 * kit_ + 0.06 * bs, decay=1.6, size=18, predelay=14,
                 high_cut=6500, early=25, late=55))
mix = dry + room

sections = [("intro", 0, tbar(4)), ("head", tbar(4), tbar(20)), ("solo1", tbar(20), tbar(36)),
            ("solo2", tbar(36), tbar(52)), ("head2", tbar(52), tbar(68)), ("tag+end", tbar(68), LENGTH)]
master(mix, NAME, sections, {"sax": sx_st, "rhodes": rh_st, "bass": bs, "drums": kit_}, fade_s=3.0,
       target_rms_db=-16.5, tape_kw={"wow_cents": 4.0, "flutter_cents": 1.2, "hiss_db": -64})
