"""08 Kelp Forest — underwater, Gb Lydian. Original material.

Everything sits below the surface: a chorused Surge pad on Lydian chords over a Gb pedal, harp ripples rising
like bubbles of light, a Rhodes with heavy chorus and slow pitch wobble singing a pentatonic tune, a sine bass,
bubbles, and slow whale-like glides. The whole music bus is behind a lowpass that rises toward the surface
(the B section is the brightest, nearly breaking through) and sinks again at the end.

Form (bars, 4/4, 64 BPM): intro 8 | A 8 | A2 8 | B 12 (whales) | A3 8 | outro 8, tail.
"""
from kit import *

h = Human(808)
BPM = 64
T = Tempo(rubato(BPM, drift=0.02, breath_every=8, breath=0.06), meter=4, lead_in=1.5)
tb = T.tb
S = {"intro": 0, "A": 8, "A2": 16, "B": 24, "A3": 36, "outro": 44}
END = 52
TAIL = 14.0
LENGTH = tb(END) + TAIL

# ---------------------------------------------------------------- harmony (2 bars each)
CH = {
    "Gb":   (ns("Gb3 Db4 F4 Bb4 C5"), n("Gb1"), ns("Gb3 Bb3 Db4 F4 C5 Db5 F5")),
    "Ab/Gb": (ns("Gb3 C4 Eb4 Ab4 Bb4"), n("Gb1"), ns("Gb3 Ab3 C4 Eb4 Ab4 Bb4 Eb5")),
    "Ebm9": (ns("Eb3 Gb3 Bb3 Db4 F4"), n("Eb1"), ns("Eb3 Bb3 Db4 F4 Gb4 Bb4 Db5")),
    "Dbsus": (ns("Db3 Ab3 Eb4 Gb4 Ab4"), n("Db2"), ns("Db3 Ab3 Db4 Eb4 Gb4 Ab4 Eb5")),
    "Ebm7": (ns("Eb3 Bb3 Db4 Gb4"), n("Eb1"), ns("Eb3 Gb3 Bb3 Db4 Gb4 Bb4 Db5")),
    "Abadd9": (ns("Ab2 Eb3 Bb3 C4 Eb4"), n("Ab1"), ns("Ab3 C4 Eb4 Bb4 C5 Eb5 Ab5")),
    "Bbm7": (ns("Bb2 F3 Ab3 Db4 F4"), n("Bb1"), ns("Bb3 Db4 F4 Ab4 Db5 F5")),
    "Db6": (ns("Db3 Ab3 Bb3 F4 Ab4"), n("Db2"), ns("Db4 F4 Ab4 Bb4 Db5 F5 Ab5")),
}
CYC_A = ["Gb", "Ab/Gb", "Ebm9", "Dbsus"]
CYC_B = ["Ebm7", "Abadd9", "Bbm7", "Db6"]
PROG = []                                   # chord per bar
for sec, cyc, bars in [("intro", CYC_A, 8), ("A", CYC_A, 8), ("A2", CYC_A, 8), ("B", CYC_B, 12), ("A3", CYC_A, 8),
                       ("outro", ["Gb", "Ab/Gb", "Gb", "Gb"], 8)]:
    for i in range(bars):
        PROG.append(cyc[(i // 2) % len(cyc)])
assert len(PROG) == END

MEL = [
    [(0, 1.5, "Db5"), (1.5, 0.5, "Eb5"), (2, 2, "F5")],
    [(0, 3, "C5"), (3, 1, "Bb4")],
    [(0, 1.5, "Bb4"), (1.5, 0.5, "Db5"), (2, 2, "Gb4")],
    [(0, 4, "F4")],
    [(0, 1.5, "Ab4"), (1.5, 0.5, "Bb4"), (2, 2, "Db5")],
    [(0, 2, "Eb5"), (2, 2, "C5")],
    [(0, 3, "Bb4"), (3, 1, "Ab4")],
    [(0, 4, "Ab4")],
]
MEL_END = [(0, 4, "Gb4")]

# ---------------------------------------------------------------- instruments
pad = surge_pad(cutoff=1500.0, attack=3.0, release=5.0, detune=18.0, voices=4, shape=0.3, reso=8.0, drift=50.0)
rhodes = inst("rhodes")
harp = inst("harp")
grand = inst("grand")

for bar in range(END):
    if bar % 2 == 0:
        for p in CH[PROG[bar]][0]:
            pad.note(p, tb(bar) - 0.1, tb(bar + 2) + 0.2, 75)

# harp ripples: a rising run at the start of each chord, faster/longer in B
for bar in range(0, END, 2):
    if bar >= S["outro"] + 6:
        break
    pool = CH[PROG[bar]][2]
    long_run = S["B"] <= bar < S["A3"]
    run = pool + ([p + 12 for p in pool[2:]] if long_run else [])
    st = tb(bar) + 0.02
    step = 0.085 if long_run else 0.11
    for k, p in enumerate(run):
        if p > n("G7"):
            break
        harp.note(p, st + k * step + h.t(0.006), st + k * step + 3.5, h.v(52 + k * 2 if long_run else 46 + k))
    # an answering high pair a bar later
    if bar >= S["A"]:
        for j, p in enumerate(h.r.sample(pool[-3:], 2)):
            harp.note(p + 12, tb(bar + 1, 1.5 + j), tb(bar + 1, 1.5 + j) + 3, h.v(40))


def melody(bar0, mel, vel, inst_, octave=0, lag=0.02):
    for i, notes in enumerate(mel):
        for b, d, nm in notes:
            s = tb(bar0 + i, b) + lag + h.t(0.012)
            e = tb(bar0 + i, b + d)
            inst_.note(n(nm) + 12 * octave, s, e + 0.15, h.v(vel + (5 if b == 0 else 0)))


melody(S["A"], MEL, 58, rhodes)
melody(S["A2"], MEL[:7] + [MEL_END], 62, rhodes)
melody(S["A3"], MEL[:7] + [MEL_END], 54, rhodes)
melody(S["A3"], MEL[:7] + [MEL_END], 36, grand, octave=1, lag=0.04)
# rhodes comping in B: soft low dyads
for bar in range(S["B"], S["A3"]):
    v = CH[PROG[bar]][0]
    for k, beat in enumerate((0, 2.5)):
        for p in v[1:3]:
            rhodes.note(p, tb(bar, beat) + h.t(0.01), tb(bar, beat + 1.8), h.v(40 - 4 * k))
for i in range(4):                           # outro: a last fragment, slower and lower
    for b, d, nm in MEL[i]:
        rhodes.note(n(nm) - 12, tb(S["outro"] + 2 * i, b * 1.5), tb(S["outro"] + 2 * i, (b + d) * 1.5), h.v(44))
for bar in range(S["A3"], S["outro"]):
    grand.pedal(tb(bar) + 0.03, tb(bar + 1) - 0.01)

# bass: sine on the chord roots, slow attack
bass_notes = [(CH[PROG[bar]][1] + 12, tb(bar) + 0.02, tb(bar + 2) - 0.05, 0.5)
              for bar in range(S["A"], S["outro"] + 4, 2)]
bass = voice(bass_notes, LENGTH, harm=(1.0, 0.15), att=0.6, rel=1.5)

# whale calls: connected notes with slow portamento (glide), low and far
WHALES = [
    (S["intro"] + 3, ["Db3", "Gb3", "F3", "Db3"], [1.6, 2.2, 1.0, 3.0]),
    (S["B"] + 1, ["Bb2", "Eb3", "Db3", "Gb3", "F3"], [1.2, 2.0, 1.0, 2.5, 3.0]),
    (S["B"] + 5, ["Ab3", "Db4", "C4", "Ab3"], [1.4, 1.8, 1.0, 3.2]),
    (S["B"] + 9, ["Gb3", "Bb3", "Ab3", "Eb3", "Db3"], [1.0, 2.2, 1.0, 1.6, 3.6]),
    (S["outro"] + 2, ["Db3", "Gb3", "Eb3"], [2.0, 2.0, 4.5]),
]
whale_notes = []
for bar, names, durs in WHALES:
    t0 = tb(bar, 1)
    for nm, d in zip(names, durs):
        whale_notes.append((n(nm), t0, t0 + d, 0.5))
        t0 += d
whale = voice(whale_notes, LENGTH, harm=(1.0, 0.45, 0.2, 0.08), vib=18, vib_rate=3.2, vib_delay=0.6, glide=0.32,
              att=0.5, rel=1.4, seed=8)
bub = bubbles(LENGTH, rate=0.9, seed=81, amp=0.2)
bub2 = bubbles(LENGTH, rate=0.5, seed=82, amp=0.2)


def wobble(x, cents=14.0, rate=0.55, seed=0):
    """Slow pitch wobble (stereo, the two channels drift apart) — the 'seen through water' warble."""
    r = np.random.default_rng(seed)
    nn = x.shape[1]
    tt = np.arange(nn) / SR
    out = []
    for c in range(2):
        ph = r.random() * 6
        cc = cents * (np.sin(2 * np.pi * rate * tt + ph) + 0.4 * np.sin(2 * np.pi * rate * 2.7 * tt + ph * 2))
        rate_ = 2 ** (cc / 1200)
        pos = np.clip(np.cumsum(rate_) - rate_[0], 0, nn - 1)
        out.append(np.interp(pos, np.arange(nn), x[c]))
    return np.stack(out).astype(np.float32)


# ---------------------------------------------------------------- render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in S.items()))
pd = pad.render(LENGTH)
rh = rhodes.render(LENGTH)
hp = harp.render(LENGTH)
gr = grand.render(LENGTH)

pd = rig.fx2(Pedalboard([HighpassFilter(90), Chorus(0.25, 0.6, 9, 0.2, 0.6), LowpassFilter(4500)]), pd)
pd = rig.automate(pd, [(0, tb(2), -8.0), (tb(S["outro"] + 4), LENGTH, -4.0)], ramp=6.0)
rh = rig.fx2(Pedalboard([HighpassFilter(80), Chorus(0.8, 0.55, 6, 0.25, 0.65), PeakFilter(2500, -2, 1.0)]), rh)
rh = wobble(rh, cents=16, rate=0.45, seed=1)
gr = wobble(rig.fx2(Pedalboard([HighpassFilter(200), Chorus(0.6, 0.5, 5, 0.2, 0.5)]), gr), cents=10, seed=2)
hp = rig.fx2(Pedalboard([HighpassFilter(120), Chorus(0.4, 0.3, 8, 0.0, 0.4)]), hp)
whale = rig.fx(Pedalboard([HighpassFilter(90), LowpassFilter(1800)]), whale)
bass = rig.fx(Pedalboard([LowpassFilter(200)]), bass)

pd = rig.at_level(pd, -25)
rh = rig.at_level(rh, -22)
gr = rig.at_level(gr, -31)
hp = rig.at_level(hp, -26)
wh = rig.at_level(whale, -27)
wh_st = np.stack([wh, np.roll(wh, int(0.021 * SR))]) * 0.75
bass = rig.pan(rig.at_level(bass, -25), 0)
bubs = rig.pan(rig.at_level(bub, -38), -0.4) + rig.pan(rig.at_level(bub2, -40), 0.5)

music = pd + rh + gr + hp
# the surface: lowpass on the music bus rising toward the B section and sinking at the end
pts = [(0, 380), (tb(S["A"]), 900), (tb(S["A2"]), 1700), (tb(S["B"]), 2600), (tb(S["B"] + 8), 7000),
       (tb(S["A3"]), 3200), (tb(S["outro"]), 1600), (tb(END), 420), (LENGTH, 300)]
tt = np.arange(music.shape[1]) / SR
fc = np.exp(np.interp(tt, [p[0] for p in pts], [np.log(p[1]) for p in pts]))
music = rave.svf(music, fc, q=0.9, mode="lp")
music = rig.automate(music, [(0, tb(S["A"]), -6.0), (tb(S["B"] + 2), tb(S["A3"]), 2.5),
                             (tb(S["outro"]), LENGTH, -2.0)], ramp=8.0)

dry = music + wh_st + bass + bubs
room = (rig.hall(music, decay=5.5, size=48, predelay=35, high_cut=6000, early=8, late=100) * 1.2
        + rig.hall(wh_st + bubs * 0.6, decay=8.0, size=60, predelay=50, high_cut=3500, early=4, late=100) * 1.4)
mix = dry + room
fi = int(4 * SR)
mix[:, :fi] *= np.linspace(0, 1, fi) ** 2

sec_list = [(k, tb(v), tb(([*S.values()] + [END])[i + 1])) for i, (k, v) in enumerate(S.items())]
sec_list[-1] = ("outro", tb(S["outro"]), LENGTH)
master(mix, "08_kelp_forest", sections=sec_list,
       stems={"pad": pd, "rhodes": rh, "piano": gr, "harp": hp, "whale": wh_st, "bass": bass, "bubbles": bubs},
       fade_s=6.0, target_rms_db=-19.5, top_db=-3.5, tape_kw={"wow_cents": 5.0})
