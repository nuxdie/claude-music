"""Last Train Home — an original tune for jazz piano trio. Medium swing in E-flat, 32-bar AABA.

Salamander grand, VSCO solo contrabass (pizz, short release), DRSKit played like a jazz kit (ride, hi-hat foot on
2 and 4, feathered kick, snare chatter). Form: rubato piano intro on the last four bars of A -> head (two-feel in
the A sections, walking from the bridge) -> one piano chorus -> trading fours with the drums -> head out from the
bridge -> tag x2 -> E-flat major 7 #11 fermata.
"""
import math
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "ep"))
import rig  # noqa: E402
from rig import SR  # noqa: E402
from orch import Sampler, GRAND  # noqa: E402

rng = random.Random(1923)
np_rng = np.random.default_rng(1923)
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

BPM = 138
SWING = 0.63                        # long-short ratio of swung eighths at this tempo (2:1 would be 0.667)

# ---------------------------------------------------------------- pitches & chords
PC = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11,
      "Cb": 11, "C#": 1, "D#": 3, "F#": 6, "G#": 8, "A#": 10}


def n(name):
    """'Eb5' -> 75"""
    i = 2 if len(name) > 2 and name[1] in "b#" else 1
    return PC[name[:i]] + 12 * (int(name[i:]) + 1)


QUAL = {  # chord tones, scale (for passing tones), rootless voicings A and B (intervals above root)
    "maj7":  ([0, 4, 7, 11], [0, 2, 4, 7, 9, 11, 5], [4, 7, 11, 14], [11, 14, 16, 19]),
    "maj7#11": ([0, 4, 7, 11], [0, 2, 4, 6, 7, 9, 11], [4, 6, 11, 14], [11, 14, 16, 18]),
    "m7":    ([0, 3, 7, 10], [0, 2, 3, 5, 7, 9, 10], [3, 7, 10, 14], [10, 14, 15, 19]),
    "7":     ([0, 4, 7, 10], [0, 2, 4, 5, 7, 9, 10], [10, 14, 16, 21], [4, 9, 10, 14]),
    "7b9":   ([0, 4, 7, 10], [0, 1, 3, 4, 6, 7, 9, 10], [10, 13, 16, 21], [4, 9, 10, 13]),
    "7alt":  ([0, 4, 10], [0, 1, 3, 4, 6, 8, 10], [10, 13, 16, 20], [4, 8, 10, 15]),
    "7sus":  ([0, 5, 7, 10], [0, 2, 5, 7, 9, 10], [10, 14, 17, 21], [5, 9, 10, 14]),
    "7#11":  ([0, 4, 7, 10], [0, 2, 4, 6, 7, 9, 10], [10, 14, 16, 18], [4, 6, 10, 14]),
}


class Chord:
    def __init__(self, sym):
        self.sym = sym
        i = 2 if len(sym) > 1 and sym[1] in "b#" else 1
        self.root = PC[sym[:i]]
        self.q = sym[i:]
        self.tones, self.scale, self.va, self.vb = QUAL[self.q]

    def pcs(self, ivs):
        return {(self.root + i) % 12 for i in ivs}

    def __repr__(self):
        return self.sym


def bars(*rows):
    """'Ebmaj7' or 'Abm7 Db7' per bar -> list of bars, each a list of (Chord, beats)."""
    out = []
    for r in rows:
        syms = r.split()
        out.append([(Chord(s), 4 // len(syms)) for s in syms])
    return out


A_HEAD = ["Ebmaj7", "Abm7 Db7", "Gm7", "Gbm7 B7", "Fm7", "Bb7sus Bb7"]
A1 = bars(*A_HEAD, "Ebmaj7 C7b9", "Fm7 Bb7")
A2 = bars(*A_HEAD, "Ebmaj7", "Bbm7 Eb7")
B = bars("Abmaj7", "Db7#11", "Gm7", "C7b9", "Fm7", "Bb7", "Gm7 C7alt", "Fm7 Bb7")
CHORUS = A1 + A2 + B + A1
TAG = bars("Gm7 C7b9", "Fm7 Bb7", "Gm7 C7b9", "Fm7 Bb7")
FINAL = bars("Ebmaj7#11")

# melody, per bar: (beat in bar, beats, note)
MEL_A = [
    [(0, 3, "D5"), (3, .5, "C5"), (3.5, .5, "Bb4")],
    [(0, 1.5, "Cb5"), (1.5, .5, "Bb4"), (2, .5, "Ab4"), (2.5, .5, "F4"), (3, .5, "Ab4"), (3.5, 1.5, "F5")],
    [(1, .5, "D5"), (1.5, .5, "Bb4"), (2, 1.5, "A4")],
    [(.5, .5, "Db5"), (1, 1, "E5"), (2, .5, "D#5"), (2.5, .5, "C#5"), (3, 1, "A4")],
    [(0, 2, "Ab4"), (2, .5, "C5"), (2.5, .5, "Eb5"), (3, 1, "G5")],
    [(0, 2, "F5"), (2, .5, "Eb5"), (2.5, .5, "D5"), (3, .5, "C5"), (3.5, .5, "Ab4")],
]
MEL_A1_END = [[(0, 2, "G4"), (2, .5, "Bb4"), (2.5, .5, "Db5"), (3, 1, "E5")],
              [(0, 2.5, "Eb5")]]
MEL_A2_END = [[(0, 3.5, "Eb5")],
              [(1, .5, "Db5"), (1.5, .5, "C5"), (2, .5, "Bb4"), (2.5, .5, "Ab4"), (3, .5, "G4"), (3.5, .5, "Db5")]]
MEL_B = [
    [(0, 3, "C5"), (3, .5, "Eb5"), (3.5, .5, "G5")],
    [(0, 2, "G5"), (2, .5, "F5"), (2.5, .5, "Eb5"), (3, 1, "Cb5")],
    [(0, 2, "Bb4"), (2, .5, "D5"), (2.5, .5, "F5"), (3, 1, "A5")],
    [(0, 1.5, "G5"), (1.5, .5, "E5"), (2, .5, "Db5"), (2.5, .5, "Bb4"), (3, 1, "G4")],
    [(0, 3, "Ab4"), (3, 1, "C5")],
    [(0, 1.5, "D5"), (1.5, .5, "F5"), (2, 1, "Ab5"), (3, 1, "G5")],
    [(0, 1, "F5"), (1, 1, "D5"), (2, .5, "Ab4"), (2.5, .5, "Gb4"), (3, 1, "E4")],
    [(0, 1.5, "F4"), (1.5, .5, "Ab4"), (2, .5, "C5"), (2.5, .5, "D5"), (3, 1, "Bb4")],
]
MEL_TAG = [MEL_A1_END[0], [(0, 2, "Eb5")], MEL_A1_END[0], [(0, 1, "Eb5"), (1.5, .5, "F5"), (2, 1, "G5")]]

# ---------------------------------------------------------------- time
# beat durations: rubato intro (16 beats, ritardando into a fermata), two-beat hi-hat count-in, then a tempo
INTRO_BEATS = 16
intro = [0.80 + 0.06 * math.sin(i * 1.3) for i in range(INTRO_BEATS)]
intro[11:15] = [0.86, 0.92, 1.0, 1.1]
intro[15] = 3.2                                 # fermata on the last chord
beat_len = intro + [60 / BPM] * 2               # count-in
HEAD = len(beat_len)                            # global beat where the head starts
form = (CHORUS                       # head in
        + CHORUS                     # piano solo
        + A1 + A2                    # trading fours (piano / drums)
        + B + A1[:6] + TAG + FINAL)  # head out from the bridge, tag, end
SEC = {"head": 0, "solo": 128, "trade": 256, "out": 320}
SEC = {k: HEAD + v for k, v in SEC.items()}
END = HEAD + 4 * (len(form) - 1)               # first beat of the final bar
beat_len += [60 / BPM] * (4 * len(form))
# gentle ritardando on the last tag bar
for k in range(8):
    beat_len[END - 8 + k] *= 1 + 0.035 * (k + 1)
beat_len += [60 / BPM * 1.4] * 8
CUM = np.concatenate([[0.0], np.cumsum(beat_len)])
LENGTH = CUM[-1] + 7.0


def t(beat, swing=True):
    """Global beat (float) -> seconds, with swung eighths. Triplet positions are left straight."""
    b = math.floor(beat + 1e-9)
    f = beat - b
    if swing and not (abs(f * 3 - round(f * 3)) < 1e-6 and round(f * 3) in (1, 2)):
        f = f / 0.5 * SWING if f <= 0.5 else SWING + (f - 0.5) / 0.5 * (1 - SWING)
    b = min(b, len(CUM) - 2)
    return CUM[b] + f * (CUM[b + 1] - CUM[b])


def hum(sd=0.006):
    return float(np_rng.normal(0, sd))


# chord timeline (global beat -> Chord)
CHORDS = []                # (start_beat, beats, Chord)
for i, bar in enumerate(form):
    b = HEAD + 4 * i
    for c, nb in bar:
        CHORDS.append((b, nb, c))
        b += nb


def chord_at(beat):
    for s, nb, c in CHORDS:
        if s <= beat + 1e-6 < s + nb:
            return c
    return CHORDS[-1][2]


# ---------------------------------------------------------------- instruments
piano = Sampler(str(GRAND))
bass = Sampler("ContrabassPizzJazz.sfz")
drums = rig.Drums()


def pnote(pitch, beat, beats, vel, late=0.008, swing=True):
    s = t(beat, swing) + late + hum(0.005)
    e = t(beat + beats, swing) + late
    piano.note(pitch, s, max(s + 0.05, e - 0.02), vel)


# ---------------------------------------------------------------- voicings & comping
_prev_voicing = [55, 58, 62, 65]


def voicing(c, below=None):
    """Rootless voicing (A or B form, any octave with the lowest note in D3..D#4) closest to the previous one."""
    global _prev_voicing
    best, cost = None, 1e9
    for ivs in (c.va, c.vb):
        for octv in range(3, 6):
            v = [c.root + 12 * octv + i for i in ivs]
            if not 50 <= v[0] <= 63:
                continue
            if below is not None:
                v = [p - 12 if p >= below - 1 else p for p in v]
                v = sorted(v)
                if v[0] < 45:
                    continue
            d = sum(abs(a - b) for a, b in zip(sorted(v), sorted(_prev_voicing))) + rng.random() * 2
            if d < cost:
                best, cost = v, d
    if best is None:
        return voicing(c)
    _prev_voicing = best
    return best


COMP_4 = [  # one-chord bar rhythms: (beat, beats, accent)
    [(0, .6, 0), (1.5, .45, 4)],                   # Charleston
    [(1, .4, 0), (2.5, .9, 4)],
    [(.5, .4, 2), (2, .8, 0)],
    [(0, 1.4, 0)],
    [(1.5, .4, 2), (3, .6, 0)],
    [(2.5, .4, 3)],
    [],
]
COMP_2 = [[(0, .6, 0)], [(.5, .4, 2)], [(0, .4, 0), (1.5, .4, 3)], []]


def comp_bar(bar_beat, bar, vel=52, density=0.8, mel=None, anticipate=True):
    """Left-hand comping for one bar; `mel` = list of (beat, beats, pitch) to keep the voicing under."""
    b = bar_beat
    hits = []
    for c, nb in bar:
        pats = COMP_4 if nb == 4 else COMP_2
        pat = rng.choice(pats[:-1] if rng.random() < density else pats)
        for pos, dur, acc in pat:
            hits.append((b + pos, dur, acc, c))
        b += nb
    # sometimes push the next bar's first chord to the "and" of 4
    if anticipate and rng.random() < 0.3 and hits and hits[-1][0] < bar_beat + 3.5:
        nxt = chord_at(bar_beat + 4)
        hits.append((bar_beat + 3.5, .6, 5, nxt))
    for pos, dur, acc, c in hits:
        top = None
        if mel:
            sounding = [p for s, d, p in mel if s <= pos + .01 < s + d + .5]
            top = min(sounding) if sounding else None
        v = voicing(c, below=top)
        roll = 0.0
        for p in v:
            pnote(p, pos, dur, vel + acc + rng.randint(-5, 4), late=0.012 + roll)
            roll += rng.choice([0, 0.003, 0.006])


# ---------------------------------------------------------------- walking bass
LO, HI = 28, 50


def bnote(pitch, beat, beats, vel, ghost=False):
    s = t(beat) - 0.008 + hum(0.004)
    e = t(beat + beats) - 0.02
    bass.note(pitch, s, max(s + 0.06, e), vel if not ghost else 40)


def near(pc, ref, lo=LO, hi=HI):
    cands = [pc + 12 * o for o in range(1, 6) if lo <= pc + 12 * o <= hi]
    return min(cands, key=lambda p: abs(p - ref) + rng.random() * 3)


def walk(start, end, two_feel=False):
    """Walking (or two-feel) bass over chord spans in [start, end)."""
    spans = [(s, nb, c) for s, nb, c in CHORDS if start <= s < end]
    prev = 39
    for i, (s, nb, c) in enumerate(spans):
        nxt = spans[i + 1][2] if i + 1 < len(spans) else chord_at(s + nb)
        first = near(c.root if rng.random() < 0.9 else (c.root + c.tones[1]) % 12, prev)
        target = near(nxt.root, first)
        r = rng.random()
        app = target - 1 if r < .35 else target + 1 if r < .65 else target + 7 if target + 7 <= HI and r < .85 \
            else target - 2
        if two_feel:
            if nb == 4:
                second = near((c.root + 7) % 12, first) if rng.random() < 0.6 else app
                bnote(first, s, 2, 96)
                bnote(second, s + 2, 2, 88)
                if rng.random() < 0.25:
                    bnote(second, s + 3.5, .5, 0, ghost=True)
            else:
                bnote(first, s, nb, 94)
            prev = first
            continue
        line = [first]
        if nb == 4:
            pool = [p for p in range(LO, HI + 1) if (p - c.root) % 12 in c.scale[:7]]
            best, cost = None, 1e9
            for x in pool:
                for y in pool:
                    steps = [abs(x - first), abs(y - x), abs(app - y)]
                    k = sum(max(0, d - 4) * 2 + (6 if d == 0 else 0) for d in steps)
                    k += 0 if (y - c.root) % 12 in c.tones else 2
                    k += rng.random() * 4
                    if k < cost:
                        best, cost = (x, y), k
            line += list(best)
        if nb >= 2:
            line.append(app)
        for k, p in enumerate(line):
            bnote(p, s + k, 1, 92 + (5 if k % 2 else 0) + rng.randint(-6, 6))
            if rng.random() < 0.06 and k < len(line) - 1:       # raked ghost on the triplet "a"
                bnote(p, s + k + 2 / 3, 1 / 3, 0, ghost=True)
        prev = line[-1]


# ---------------------------------------------------------------- drums
def dh(name, beat, vel, swing=True, early=0.004):
    drums.hit(name, t(beat, swing) - early + hum(0.004), vel + rng.randint(-5, 5))


def time_feel(start, end, chatter=0.25, ride=True, rim4=False, loud=0):
    for b in range(start, end):
        pos = (b - HEAD) % 4
        if ride:
            dh("ride", b, 66 + loud + (6 if pos in (1, 3) else 0))
            if pos in (1, 3):
                dh("ride", b + .5, 50 + loud)
        else:  # closed hats with an open-close "chick" texture for the quiet A sections
            dh("hh_closed", b, 42 + (8 if pos in (1, 3) else 0))
            if pos in (1, 3):
                dh("hh_closed", b + .5, 34)
        if pos in (1, 3):
            dh("hh_foot", b, 62)
        dh("kick", b, 26)                                       # feathered
        if rim4 and pos == 3:
            dh("rim", b, 56)
        if not rim4 and rng.random() < chatter:
            dh("snare", b + rng.choice([.5, 2 / 3, 1 / 3]), rng.randint(28, 48) + loud)
            if rng.random() < 0.3:
                dh("snare", b + 2 / 3, rng.randint(22, 38))


def fill_into(beat, big=False):
    """Fill on the last beat before `beat`, crash on it."""
    k = rng.choice(["trip", "bomb", "two"])
    if k == "trip":
        for i, f in enumerate((0, 1 / 3, 2 / 3)):
            dh("snare" if i < 2 else "tom2", beat - 1 + f, 52 + 10 * i)
    elif k == "bomb":
        dh("kick", beat - .5, 82)
        dh("snare", beat - 1 + 2 / 3, 46)
    else:
        dh("snare", beat - 2 + 2 / 3, 44)
        dh("snare", beat - .5, 60)
    dh("crash_l" if big else "crash_r", beat, 78 if big else 62)
    dh("kick", beat, 70)


def drum_four(start):
    """A four-bar drum break: triplet phrasing around the kit, ends into a crash on the piano's downbeat."""
    toms = ["tom1", "tom2", "tom3"]
    for bar in range(4):
        b0 = start + 4 * bar
        dh("hh_foot", b0 + 1, 62)
        dh("hh_foot", b0 + 3, 62)
        if bar == 0:
            for i in range(12):
                f = b0 + i / 3
                dh("snare", f, 40 + (40 if i % 3 == 0 else 0) + (20 if i in (5, 8) else 0))
            dh("kick", b0, 90)
            dh("crash_l", b0, 74)
        elif bar == 1:
            for i, nm in enumerate(["snare", "tom1", "tom1", "tom2", "tom2", "tom3", "kick", "tom3", "snare",
                                    "ride_bell", "kick", "snare"]):
                dh(nm, b0 + i / 3, 88 if i % 3 == 0 else 64)
        elif bar == 2:
            for i in range(8):
                f = b0 + i / 2
                dh("ride", f, 70)
                if i % 2:
                    dh("snare", f, 80 if i == 7 else 58)
                else:
                    dh("kick", f, 76)
            dh("crash_r", b0 + 2.5, 84)
        else:
            for i in range(9):
                dh(toms[min(2, i // 3)] if i < 9 else "snare", b0 + i / 3, 70 + 3 * i)
            dh("snare", b0 + 3, 96)
            dh("snare", b0 + 3 + 1 / 3, 70)
            dh("snare", b0 + 3 + 2 / 3, 84)


# ---------------------------------------------------------------- solo line generator
def line(start, end, p0, direction=1, trip=0.12, lo=58, hi=84, vel=70):
    """Swung eighth-note bebop line from `start` to `end`: chord tones (or 9ths) land on the beats, passing tones
    and chromatic approaches on the off-beats, enclosures when the next target is a step away, occasional
    triplet turns. Returns the landing pitch (a chord tone of the chord at `end`)."""
    c0 = chord_at(start)
    p = min((q for q in range(lo, hi + 1) if q % 12 in c0.pcs(c0.tones)), key=lambda q: abs(q - p0))
    b = start
    while b < end - 0.01:
        c, c1 = chord_at(b), chord_at(b + 1)
        tones = [q for q in range(lo, hi + 1) if q % 12 in c1.pcs(c1.tones + [14])]
        cand = [q for q in tones if (q - p) * direction > 0 and 1 <= abs(q - p) <= 5]
        if not cand or rng.random() < 0.1:
            direction *= -1
            cand = [q for q in tones if (q - p) * direction > 0 and 1 <= abs(q - p) <= 5] or [p]
        cand.sort(key=lambda q: abs(q - p))
        d1 = cand[0] if rng.random() < 0.65 or len(cand) == 1 else cand[1]
        scale = c.pcs(c.scale)
        between = [q for q in range(min(p, d1) + 1, max(p, d1)) if q % 12 in scale]
        v = vel + int((p - 70) * 0.8)
        if b == start and rng.random() < 0.5:
            pass                                                  # breathe: start on the "and"
        else:
            pnote(p, b, .55, v - 4 + rng.randint(-4, 4), late=0.014)
        m1 = (between[0] if direction > 0 else between[-1]) if between else p
        m2 = d1 - direction
        if abs(d1 - p) >= 3 and len({p, m1, m2}) == 3 and rng.random() < trip:
            pnote(m1, b + 1 / 3, 1 / 3, v - 8, swing=False, late=0.014)
            pnote(m2, b + 2 / 3, 1 / 3, v - 2, swing=False, late=0.014)
        else:
            if abs(d1 - p) >= 2:
                u = d1 - direction if rng.random() < 0.5 or not between else \
                    (between[-1] if direction > 0 else between[0])
            else:
                above = [q for q in range(d1 + 1, d1 + 4) if q % 12 in scale]
                u = above[0] if above and rng.random() < .6 else d1 - 1
            pnote(u, b + .5, .5, v + 5 + rng.randint(-3, 3), late=0.014)   # off-beats a touch accented
        p = d1
        b += 1
        if p >= hi - 2:
            direction = -1
        elif p <= lo + 2:
            direction = 1
    return p


def land(p, beat, beats, vel=74, drop=None):
    """Phrase ending: a held note, or a short 'doo-DAT' ending to a lower chord tone."""
    if drop is not None:
        pnote(p, beat, .4, vel)
        pnote(drop, beat + .5, .35, vel + 8)
    else:
        pnote(p, beat, beats, vel)


def melody(start, bar_lists, octave=0, vel=74, double=False, lh=True, density=0.7):
    for k, notes in enumerate(bar_lists):
        b0 = start + 4 * k
        mel = []
        for pos, dur, nm in notes:
            p = n(nm) + octave
            mel.append((b0 + pos, dur, p))
            vv = vel + int((p - 72) * 0.6) + rng.randint(-3, 3)
            pnote(p, b0 + pos, dur * 0.95, vv)
            if double:
                pnote(p - 12, b0 + pos, dur * 0.95, vv - 12)
        if lh:
            bar = form[(b0 - HEAD) // 4]
            comp_bar(b0, bar, vel=48, density=density, mel=[(s, d, p - (12 if double else 0)) for s, d, p in mel])


def hand(start, notes, vel=74):
    """Hand-written solo phrase: (beat offset, beats, note name)."""
    for pos, dur, nm in notes:
        p = n(nm)
        pnote(p, start + pos, dur * 0.92, vel + int((p - 72) * 0.6) + rng.randint(-3, 3), late=0.014)


# ================================================================= the performance
# --- intro: rubato piano on the last four bars of A, with pedal
INTRO_CH = [("Fm7", ["F2", "C3"], ["Ab3", "Eb4", "G4"]), ("Bb7sus", ["Bb1", "F2"], ["Ab3", "C4", "Eb4"]),
            ("Bb7", ["Bb1"], ["Ab3", "D4", "G4"]),
            ("Ebmaj7", ["Eb2", "Bb2"], ["G3", "D4", "F4"]), ("C7b9", ["C2"], ["Bb3", "Db4", "E4"]),
            ("Fm7", ["F2", "C3"], ["Ab3", "Eb4", "G4"]), ("Bb7", ["Bb1"], ["Ab3", "Db4", "D4", "G4"])]
INTRO_POS = [0, 4, 6, 8, 10, 12, 14]
for (sym, lh, rh), pos in zip(INTRO_CH, INTRO_POS):
    s = t(pos, False)
    dur_end = t(pos + (2 if pos >= 4 else 4), False) if pos < 14 else t(16, False) - 0.15
    piano.pedal(s + 0.04, dur_end - 0.02)
    for i, nm in enumerate(lh):
        piano.note(n(nm), s + 0.01 * i, dur_end, 50)
    for i, nm in enumerate(rh):
        piano.note(n(nm), s + 0.05 + 0.035 * i, dur_end, 40)
for pos, dur, nm in (MEL_A[4] + [(4 + a, d, x) for a, d, x in MEL_A[5]] + [(8 + a, d, x) for a, d, x in MEL_A1_END[0]]
                     + [(12, 1.5, "Eb5"), (13.5, .5, "F5"), (14, 1.6, "G5")]):
    s = t(pos, False) + 0.02
    piano.note(n(nm), s, t(pos + dur, False) - 0.03, 62 + int((n(nm) - 70) * 0.8))
# little cadenza run over the fermata Bb7 (Bb7(b9,13) colours), sweeping up and back to F5
run = ["Bb4", "Cb5", "Db5", "D5", "F5", "G5", "Ab5", "Cb6", "Bb5", "G5", "F5"]
s0 = t(15, False) + 0.6
for i, nm in enumerate(run):
    s = s0 + i * 0.105 + (0.25 if i == len(run) - 1 else 0)
    piano.note(n(nm), s, s + (0.9 if i == len(run) - 1 else 0.15), 52 + 3 * min(i, 7))
# count-in: hi-hat foot on beats 3 and 4
dh("hh_foot", HEAD - 2, 70, early=0)
dh("hh_foot", HEAD - 1, 70, early=0)

H = SEC["head"]
# --- head in. A sections: two-feel, hats + cross-stick on 4. Bridge and last A: walking, ride.
for i, sec in enumerate(["A1", "A2", "B", "A3"]):
    b0 = H + 32 * i
    mel = (MEL_A + (MEL_A1_END if sec != "A2" else MEL_A2_END)) if sec != "B" else MEL_B
    melody(b0, mel, vel=72, density=0.6 if sec in ("A1", "A2") else 0.75)
    if sec in ("A1", "A2"):
        walk(b0, b0 + 32, two_feel=True)
        time_feel(b0, b0 + 32, ride=False, rim4=True)
    else:
        walk(b0, b0 + 32)
        time_feel(b0, b0 + 32, chatter=0.18)
    if i:
        fill_into(b0, big=sec == "B")
fill_into(SEC["solo"], big=True)

# --- piano solo chorus
S = SEC["solo"]
walk(S, S + 128)
time_feel(S, S + 96, chatter=0.3, loud=4)
time_feel(S + 96, S + 128, chatter=0.38, loud=7)
for k in (32, 64, 96):
    fill_into(S + k, big=k == 64)
for bar in range(32):
    comp_bar(S + 4 * bar, form[(S - HEAD) // 4 + bar], vel=46, density=0.55)

hand(S, [(.5, .5, "Bb4"), (1, 1, "D5"), (2, .5, "F5"), (2.5, 1.5, "D5"),
         (4.5, .5, "Eb5"), (5, 1, "Cb5"), (6, .5, "Ab4"), (6.5, 1.5, "F4")])
hand(S + 8, [(.5, .5, "Bb4"), (1, .5, "D5"), (1.5, .5, "F5"), (2, 1.5, "A5"),
             (4, .5, "A5"), (4.5, .5, "E5"), (5, .5, "Db5"), (5.5, .5, "E5"), (6, .5, "D#5"), (6.5, .5, "F#5"),
             (7, 1, "A5")])
p = line(S + 16, S + 27, 68, direction=1)
land(p, S + 27, 1.5)
p = line(S + 30, S + 40, p, direction=-1, trip=0.2)
land(p, S + 40, .5, drop=p - 5)
p = line(S + 41, S + 46, p + 3, direction=1)
land(p, S + 46, 1.5)
riff = [(0, .5, "F5"), (.5, .5, "Ab5"), (1, .5, "Bb5"), (1.5, 1, "Ab5"), (2.5, .5, "F5"), (3, 1, "Eb5")]
hand(S + 48, riff, vel=80)
hand(S + 52, [(0, .5, "F5"), (.5, .5, "Ab5"), (1, .5, "Bb5"), (1.5, .5, "C6"), (2, .5, "Bb5"), (2.5, .5, "Ab5"),
              (3, 1, "F5")], vel=82)
p = line(S + 57, S + 64, 77, direction=-1)
land(p, S + 64, 1.5, vel=80)
p = line(S + 66, S + 76, p, direction=1, trip=0.35, hi=88, vel=78)
land(p, S + 76, .5, vel=84, drop=p - 7)
p = line(S + 77, S + 92, p - 3, direction=-1, trip=0.3, hi=88, vel=78)
land(p, S + 92, 1.5, vel=78)
p = line(S + 94, S + 96, p, direction=1, vel=80)
# last A: quote the head an octave up, then wind down to the turnaround
hand(S + 96, [(a, d, nm[:-1] + str(int(nm[-1]) + 1)) for a, d, nm in MEL_A[0]]
     + [(4 + a, d, nm[:-1] + str(int(nm[-1]) + 1)) for a, d, nm in MEL_A[1][:4]], vel=82)
p = line(S + 104, S + 116, 79, direction=-1, trip=0.25, vel=76)
land(p, S + 116, 1.5, vel=74)
p = line(S + 118, S + 124, p, direction=1, vel=72)
land(p, S + 124, .5, vel=76, drop=p - 4)

# --- trading fours: piano 4 bars (with bass and drums), drums 4 bars alone
T = SEC["trade"]
TRADE_PIANO = [T, T + 32]
TRADE_DRUMS = [T + 16, T + 48]
p = 72
for b0 in TRADE_PIANO:
    walk(b0, b0 + 16)
    time_feel(b0, b0 + 16, chatter=0.35, loud=6)
    for bar in range(4):
        comp_bar(b0 + 4 * bar, form[(b0 - HEAD) // 4 + bar], vel=46, density=0.5, anticipate=False)
    hand(b0, [(.5, .5, "G5"), (1, .5, "Bb5"), (1.5, .5, "D6"), (2, 1, "Eb6"), (3, .5, "D6"), (3.5, .5, "Bb5")],
         vel=86)
    p = line(b0 + 4, b0 + 14, 82, direction=-1, trip=0.3, hi=90, vel=80)
    land(p, b0 + 14, .5, vel=84, drop=p - 5)
for b0 in TRADE_DRUMS:
    drum_four(b0)
dh("crash_l", T + 32, 80)
dh("kick", T + 32, 80)

# --- head out from the bridge, melody in octaves; tag; ending
O = SEC["out"]
melody(O, MEL_B, vel=74, double=True, density=0.8)
melody(O + 32, MEL_A, vel=72, double=True, density=0.7)
melody(O + 56, MEL_TAG, vel=70, double=True, density=0.7)
dh("crash_l", O, 84)
dh("kick", O, 84)
walk(O, END)
time_feel(O, O + 32, chatter=0.3, loud=5)
time_feel(O + 32, END, chatter=0.22, loud=2)
fill_into(O + 32)
fill_into(O + 56)

# final chord: E-flat major 7 #11, rolled, pedal down; bass low E-flat; soft ride roll swelling and fading
fs = t(END, False)
piano.pedal(fs - 0.02, LENGTH - 0.5)
for i, nm in enumerate(["Eb2", "Bb2", "G3", "D4", "F4", "A4", "D5", "G5"]):
    piano.note(n(nm), fs + 0.045 * i, LENGTH - 0.5, 54 + 2 * i)
pnote(n("Bb5"), END + 2.6, 4, 58, swing=False)
bass.note(n("Eb1"), fs, fs + 4.5, 96)
drums.hit("crash_r", fs, 66)
drums.hit("kick", fs, 60)
for i in range(60):
    tt = fs + 0.3 + i * 0.075
    drums.hit("ride", tt, int(28 + 30 * math.sin(math.pi * i / 60)))

# ================================================================= render & mix
print(f"length {LENGTH:.1f}s; head {t(SEC['head']):.1f}, solo {t(SEC['solo']):.1f}, trades {t(SEC['trade']):.1f}, "
      f"out {t(SEC['out']):.1f}, end {fs:.1f}")
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowShelfFilter, PeakFilter, HighShelfFilter,
                        Gain)  # noqa: E402

pno = piano.render(LENGTH)
bs = bass.render(LENGTH).mean(0)
ch = drums.render(LENGTH)

pno = rig.fx2(Pedalboard([HighpassFilter(45), PeakFilter(250, -2, 1), HighShelfFilter(9000, 1.5),
                          Compressor(-20, 2, 15, 200)]), pno)
bs = rig.fx(Pedalboard([HighpassFilter(35), PeakFilter(90, 3, 1), PeakFilter(700, 2, 1.2),
                        Compressor(-22, 3, 8, 150)]), bs)
kit = rig.drum_bus(ch, close=0.7, room=0.9, kick_db=-9, snare_db=-5, hat_db=-2, tom_db=-2, oh_db=4)
kit = rig.fx2(Pedalboard([HighpassFilter(40), Compressor(-22, 2, 20, 200)]), kit)

pno = rig.at_level(pno, -19)
bs = rig.pan(rig.at_level(bs, -20), 0.1)
kit = rig.at_level(kit, -23)
dry = pno + bs + kit
room = rig.stereo_reverb(0.35 * pno + 0.15 * kit + 0.08 * np.stack([bs[0] + bs[1]] * 2) / 2, room=0.42,
                         damping=0.55)
mix = dry + room

sections = [("intro", 0, t(HEAD)), ("head A", t(H), t(H + 64)), ("head B+A", t(H + 64), t(S)),
            ("solo", t(S), t(T)), ("trades", t(T), t(O)), ("out", t(O), fs), ("end", fs, LENGTH)]
rig.section_table({"piano": pno, "bass": bs, "drums": kit, "mix": mix}, sections)
master = Pedalboard([HighpassFilter(25), LowShelfFilter(120, 0.5), Compressor(-16, 1.6, 30, 250)])
rig.finish(mix, OUT / "last_train_home", master, fade_s=2.5, target_rms_db=-16.0)
print("written", OUT / "last_train_home.mp3")
