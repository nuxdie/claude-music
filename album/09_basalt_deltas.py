"""09 Basalt Deltas — the Nether. C, with the tritone (F#) as the second home. Original material.

A distorted saw drone smoulders on C; inharmonic FM clangs ring like iron struck in the dark. The recurring figure
is a bowed low riff (basses + celli): C – Db – C – F#, G — the half-step grinding up and the tritone dropping out
under it. Slow tribal pulses (timpani plus a synthesized low drum) push it forward, a low male choir breathes
tritone clusters, trombones join the riff at the climax, and a ghostly high piano drifts above it all.

Form (bars, 4/4, 52 BPM): intro 6 | riff 8 | choir 8 | break 4 | climax 10 | outro 6, tail.
"""
from kit import *
import kit

h = Human(666)
BPM = 52
T = Tempo(rubato(BPM, drift=0.012), meter=4, lead_in=1.0)
tb = T.tb
S = {"intro": 0, "riff": 6, "choir": 14, "break": 22, "climax": 26, "outro": 36}
END = 42
LENGTH = tb(END) + 14.0

# ---------------------------------------------------------------- the figure (2 bars): (beat, beats, note)
RIFF = [(0, 2.5, "C2"), (2.5, 1.5, "Db2"), (4, 1.5, "C2"), (5.5, 1.0, "F#1"), (6.5, 1.5, "G1")]
RIFF_B = [(0, 2.5, "C2"), (2.5, 1.5, "Db2"), (4, 1.0, "Eb2"), (5, 1.5, "Db2"), (6.5, 1.5, "F#1")]

basses = inst("basses")
celli = inst("celli")
trombones = inst("trombones")


def riff(bar, var, vel, cello=True, tbn=False):
    for b, d, nm in var:
        p = n(nm)
        s, e = tb(bar, b) + h.t(0.012), tb(bar, b + d) + 0.08
        basses.note(p, s, e, h.v(vel))
        if cello:
            celli.note(p + 12, s + 0.01, e, h.v(vel - 6))
        if tbn and p + 24 >= 42:
            trombones.note(p + 24, s + 0.02, e - 0.05, h.v(vel - 4))


for bar in range(S["riff"], S["break"], 2):
    riff(bar, RIFF if (bar // 2) % 2 == 0 else RIFF_B, 70 if bar < S["choir"] else 82, cello=bar >= S["riff"] + 4)
for bar in range(S["climax"], S["outro"], 2):
    riff(bar, RIFF if (bar // 2) % 2 == 0 else RIFF_B, 98, tbn=True)
for i, bar in enumerate(range(S["outro"], S["outro"] + 4, 2)):     # outro: the figure, breaking down
    riff(bar, RIFF[:3], 66 - 12 * i, cello=False)

# ---------------------------------------------------------------- drone: distorted saw, C -> F# in the break
drone = kit._surge_base(a_osc_1_type="Classic", a_osc_1_unison_voices=3, a_osc_1_unison_detune=22.0, a_osc_1_shape=0.0,
                    a_osc_drift=70.0, a_filter_1_type="LP Vintage Ladder", a_filter_1_cutoff=420.0,
                    a_filter_1_resonance=25.0, a_amp_eg_attack=4.0, a_amp_eg_sustain=100.0, a_amp_eg_release=6.0,
                    a_amp_eg_envelope_mode="Analog", a_volume=-6.0)
DRONE = [(0, S["break"], ns("C1 C2 G2")), (S["break"], S["climax"], ns("F#1 C2 F#2")),
         (S["climax"], S["outro"] + 4, ns("C1 C2 G2 Db3")), (S["outro"] + 4, END + 1, ns("C1 C2"))]
for b0, b1, ps in DRONE:
    for p in ps:
        drone.note(p, tb(b0) - 0.2, tb(b1) + 0.3, 80)

# ---------------------------------------------------------------- choir: low tritone clusters (range A2..F#4)
choir = inst("choir_m")
CHOIR = [(S["choir"], 4, ns("C3 G3 C4")), (S["choir"] + 4, 4, ns("C3 F#3 Db4")),
         (S["break"], 4, ns("A2 F#3 C4 Eb4")),
         (S["climax"], 2, ns("C3 G3 C4 Db4")), (S["climax"] + 2, 2, ns("Db3 Ab3 C4")),
         (S["climax"] + 4, 2, ns("C3 G3 C4 Db4")), (S["climax"] + 6, 4, ns("C3 F#3 C4 F#4")),
         (S["outro"], 4, ns("C3 G3"))]
for bar, bars, ps in CHOIR:
    for p in ps:
        choir.note(p, tb(bar) + h.t(0.05), tb(bar + bars) + 0.4, h.v(78))

# ---------------------------------------------------------------- drums: timpani + synth low drum, tribal pattern
timp = inst("timpani")
low_hits = []
PAT_A = [(0, 1.0, 100), (2.5, 0.6, 80), (3.0, 0.8, 90)]                 # per bar: beat, len, vel
PAT_B = [(0, 1.0, 110), (1.5, 0.6, 76), (2.5, 0.6, 86), (3.0, 0.8, 96), (3.5, 0.5, 70)]
for bar in range(S["riff"] + 2, END - 2):
    if S["break"] <= bar < S["climax"]:
        continue
    pat = PAT_B if S["climax"] <= bar < S["outro"] else PAT_A
    if bar >= S["outro"]:
        pat = PAT_A[:1]
    for b, d, v in pat:
        t0 = tb(bar, b) + h.t(0.008)
        pitch = n("C2") if b == 0 else (n("G2") if b == 3.0 else n("F#2"))
        timp.note(pitch, t0, t0 + d, h.v(v - (10 if bar < S["choir"] else 0)))
        if b in (0, 3.0):
            low_hits.append((t0, v / 127))


def low_drum(hits, length):
    """Big low drum: sine with a fast pitch drop, plus a felt-beater thump of filtered noise."""
    nn = int(length * SR)
    out = np.zeros(nn, dtype=np.float32)
    rng = np.random.default_rng(3)
    for t0, a in hits:
        i0 = int(t0 * SR)
        L = int(1.6 * SR)
        i1 = min(nn, i0 + L)
        tt = np.arange(i1 - i0) / SR
        f = 48 + 70 * np.exp(-tt / 0.045)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.45)
        thump = rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.012) * 0.3
        out[i0:i1] += (a * (body + thump)).astype(np.float32)
    return rig.fx(Pedalboard([LowpassFilter(900)]), out)


# ---------------------------------------------------------------- clangs: inharmonic FM, the iron of the place
clang_notes = []
CL = {"intro": [(1, 0), (2, 2.5), (3, 1), (4, 3), (5, 0.5)],
      "riff": [(b, 3.5) for b in range(S["riff"] + 1, S["choir"], 2)],
      "choir": [(b, k) for b in range(S["choir"], S["break"], 2) for k in (1.5, 3.5)],
      "break": [(S["break"] + 1, 0), (S["break"] + 3, 2)],
      "climax": [(b, k) for b in range(S["climax"], S["outro"]) for k in (1.0, 3.5)],
      "outro": [(S["outro"] + 1, 2), (S["outro"] + 3, 0), (S["outro"] + 5, 1)]}
for sec, hits in CL.items():
    for bar, beat in hits:
        p = h.r.choice(ns("C4 F#4 C5 Db5 G4"))
        clang_notes.append((p, tb(bar, beat) + h.t(0.01), 1, h.r.uniform(0.15, 0.3)))
clang_a = fm_bell(clang_notes[::2], LENGTH, ratio=1.414, index=4.5, decay=1.6, idecay=0.25, seed=1)
clang_b = fm_bell(clang_notes[1::2], LENGTH, ratio=2.76, index=3.5, decay=1.2, idecay=0.2, seed=2)

# ---------------------------------------------------------------- ghost piano: high, slow, a tritone apart
grand = inst("grand")
GHOST = [(1, 1, "C6"), (2, 3, "F#6"), (4, 2, "Db6"), (9, 0, "G6"), (11, 2, "C7"), (17, 1, "F#6"), (19, 3, "Eb6"),
         (S["break"], 0, "C6"), (S["break"], 2, "F#6"), (S["break"] + 1, 1, "Db7"), (S["break"] + 2, 0, "G6"),
         (S["break"] + 3, 0, "C6"), (S["break"] + 3, 2.5, "B5"), (31, 2, "F#6"), (S["outro"] + 2, 0, "C6"),
         (S["outro"] + 3, 2, "F#6"), (S["outro"] + 5, 0, "C7")]
for bar, beat, nm in GHOST:
    t0 = tb(bar, beat)
    grand.note(n(nm), t0, t0 + 4, h.v(40))
    grand.pedal(t0 - 0.02, t0 + 5)

# ---------------------------------------------------------------- render & mix
print(f"length {LENGTH:.1f}s  " + "  ".join(f"{k} {tb(v):.1f}" for k, v in S.items()))
bs = basses.render(LENGTH) + celli.render(LENGTH) * 0.8
tbn = trombones.render(LENGTH)
dr = drone.render(LENGTH)
ch = choir.render(LENGTH)
tp = timp.render(LENGTH)
ld = low_drum(low_hits, LENGTH)
gh = grand.render(LENGTH)
cl = rig.pan(clang_a, -0.45) + rig.pan(clang_b, 0.45)

dr = rig.fx2(Pedalboard([Distortion(14), HighpassFilter(35), LowpassFilter(1800), PeakFilter(300, -3, 0.8)]), dr)
tt = np.arange(dr.shape[1]) / SR                       # the heat haze: slow wandering filter on the drone
fc = 500 + 380 * (0.5 + 0.5 * np.sin(2 * np.pi * tt / 23.0)) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 7.1))
dr = rave.svf(dr, fc, q=1.3, mode="lp")
dr = rig.automate(dr, [(0, tb(2), -8), (tb(S["break"]), tb(S["climax"]), -3), (tb(S["climax"]), tb(S["outro"]), 2.5),
                       (tb(S["outro"] + 4), LENGTH, -5)], ramp=5.0)
bs = rig.fx2(Pedalboard([HighpassFilter(35), PeakFilter(180, 2, 0.9), Distortion(4), LowpassFilter(3500)]), bs)
tbn = rig.fx2(Pedalboard([HighpassFilter(60), LowpassFilter(3000)]), tbn)
ch = rig.fx2(Pedalboard([HighpassFilter(90), LowpassFilter(4000), PeakFilter(700, -2, 1)]), ch)
tp = rig.fx2(Pedalboard([HighpassFilter(40), PeakFilter(90, 3, 1.0), Compressor(-20, 3, 5, 150)]), tp)
gh = rig.fx2(Pedalboard([HighpassFilter(800), LowpassFilter(7000)]), gh)
cl = rig.fx2(Pedalboard([HighpassFilter(250), LowpassFilter(6000)]), cl)

bs = rig.at_level(bs, -21)
tbn = rig.at_level(tbn, -25)
dr = rig.at_level(dr, -24)
ch = rig.at_level(ch, -24)
tp = rig.at_level(tp, -22)
ld = rig.pan(rig.at_level(ld, -21), 0)
gh = rig.at_level(gh, -32)
cl = rig.at_level(cl, -31)

drums = tp + ld
dry = bs + tbn + dr + ch + drums + gh + cl
room = (rig.hall(bs + tbn + ch, decay=4.5, size=50, predelay=25, high_cut=4000, early=15, late=85) * 0.9
        + rig.hall(drums, decay=3.5, size=55, predelay=15, high_cut=3500, early=35, late=70) * 0.9
        + rig.hall(gh + cl, decay=8.0, size=60, predelay=60, high_cut=6000, early=5, late=100) * 1.6)
mix = dry + room
fi = int(5 * SR)
mix[:, :fi] *= np.linspace(0, 1, fi) ** 2

sec_list = [(k, tb(v), tb(([*S.values()] + [END])[i + 1])) for i, (k, v) in enumerate(S.items())]
sec_list[-1] = ("outro", tb(S["outro"]), LENGTH)
master(mix, "09_basalt_deltas", sections=sec_list,
       stems={"strings": bs, "trombone": tbn, "drone": dr, "choir": ch, "drums": drums, "ghost": gh, "clang": cl},
       fade_s=6.0, target_rms_db=-19.0, top_db=-3.0, tape_kw={"wow_cents": 3.0, "drive": 2.0})
