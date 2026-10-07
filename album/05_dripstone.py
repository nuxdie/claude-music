"""05 Dripstone — cave ambience in D Phrygian. Original material.

A low drone (Surge, ladder filter nearly shut) breathes under irregular cave drips and a faint draught of wind.
Distant grand-piano notes fall into a very long hall, each one announced by its own reversed shadow. In the middle
a fragile tune appears (D Phrygian, the Eb leaning on D), is repeated an octave higher with celesta dust, then
comes apart note by note until only the drips and the drone's Eb-D rub are left.

Form (s):  0 drone + drips | 34 distant notes | 86 tune | 122 tune high | 152 dissolving | 196 drone alone, end ~222.
"""
import random

from kit import *

h = Human(1305)
r = random.Random(1305)
LENGTH = 222.0
S = {"open": 0, "notes": 34, "tune": 86, "tune2": 122, "dissolve": 152, "tail": 196}

# ---------------------------------------------------------------- drone: D/A, sliding to Eb/Bb (phrygian rub) and back
drone = surge_pad(cutoff=260.0, attack=6.0, release=8.0, detune=10.0, voices=3, shape=0.0, reso=18.0, drift=60.0,
                  vol=-6.0)
DR = [(0, 48, ns("D2 A2 D3")), (48, 70, ns("Eb2 Bb2 D3")), (70, 120, ns("D2 A2 F3")), (120, 150, ns("Bb1 F2 D3")),
      (150, 176, ns("Eb2 Bb2 G3")), (176, 214, ns("D2 A2 D3"))]
for s, e, ps in DR:
    for p in ps:
        drone.note(p, s + h.t(0.2), e + 1.5, 70)
sub = voice([(n("D1"), 2, 212, 0.5)], LENGTH, harm=(1.0, 0.25), att=12.0, rel=8.0)

# ---------------------------------------------------------------- drips: irregular clusters, thinning in the tune
drip_t = []
t = 1.5
while t < LENGTH - 4:
    dense = 0.55 if (S["tune"] <= t < S["dissolve"]) else 1.0
    t += r.expovariate(0.55 * dense)
    drip_t.append(t)
    if r.random() < 0.25:                         # a drip and its echo off another stone
        drip_t.append(t + r.uniform(0.18, 0.5))
drips_l = drips(LENGTH, drip_t[::2], seed=1, lo=1300, hi=3200, amp=0.3)
drips_r = drips(LENGTH, drip_t[1::2], seed=2, lo=1600, hi=3800, amp=0.3)
# a few deep, slow drips: like water into a pool far below
deep = drips(LENGTH, [r.uniform(10, 210) for _ in range(14)], seed=3, lo=500, hi=800, amp=0.35)

air = wind(LENGTH, seed=5, lo=180, hi=700, rate=0.035, q=3.0)

# ---------------------------------------------------------------- distant grand notes
grand = inst("grand")
celesta = inst("celesta")
rev_src = []                                     # (pitch, entry_time) -> reversed shadows rendered separately


def pn(p, s, dur, vel, shadow=False):
    grand.note(p, s + h.t(0.02), s + dur, h.v(vel, 2))
    if shadow:
        rev_src.append((p, s))


distant = [(36, "A4", 30), (41, "D4", 28), (47.5, "Eb5", 26), (53, "F4", 30), (58, "A3", 27), (63.5, "Bb4", 28),
           (69, "G4", 26), (74, "D5", 25), (79.5, "C5", 27), (83, "A4", 29)]
for i, (s, nm, v) in enumerate(distant):
    pn(n(nm), s, 6.0, v, shadow=(i % 3 == 0))
for s in (36, 58, 74):
    grand.pedal(s - 0.1, s + 7)

# the tune (seconds from section start, dur, note) — slow, irregular, like counting drips
TUNE = [(0.0, 1.6, "A4"), (1.6, 0.8, "Bb4"), (2.4, 2.4, "A4"), (5.2, 1.2, "F4"), (6.4, 1.2, "G4"), (7.6, 3.2, "Eb4"),
        (11.6, 1.2, "D4"), (12.8, 1.2, "F4"), (14.0, 1.6, "A4"), (15.6, 0.8, "C5"), (16.4, 3.6, "Bb4"),
        (21.0, 1.2, "A4"), (22.2, 1.2, "G4"), (23.4, 1.6, "F4"), (25.0, 1.2, "Eb4"), (26.4, 6.0, "D4")]
BASS = [(0.0, "D3"), (7.6, "Eb3"), (11.6, "Bb2"), (16.4, "G2"), (21.0, "Eb3"), (26.4, "D2")]


def tune(t0, octave, vel, cel=False, keep=1.0, slow=1.0):
    for b, d, nm in TUNE:
        if r.random() > keep:
            continue
        p = n(nm) + 12 * octave
        st = t0 + b * slow
        pn(p, st, d * slow + 1.5, vel + (3 if d > 2 else 0))
        if cel and p + 12 <= n("C8"):
            celesta.note(p + 12, st + 0.03, st + d * slow + 0.5, h.v(vel - 6))
    for b, nm in BASS:
        if r.random() > keep + 0.1:
            continue
        pn(n(nm), t0 + b * slow, 6.0, vel - 8)
    grand.pedal(t0 - 0.05, t0 + 33 * slow)


tune(S["tune"] + 1.0, 0, 38)
rev_src.append((n("A5"), S["tune2"]))
tune(S["tune2"], 1, 33, cel=True)
tune(S["dissolve"] + 1.0, 0, 30, keep=0.55, slow=1.25)
# last notes, far apart
for s, nm, v in [(196, "A4", 24), (203, "Eb5", 22), (209.5, "D4", 24)]:
    pn(n(nm), s, 9.0, v, shadow=(nm == "D4"))
grand.pedal(195.9, 220)

# ---------------------------------------------------------------- render
print("rendering...")
g = grand.render(LENGTH)
cel = celesta.render(LENGTH)
dr = drone.render(LENGTH)

# reversed shadows: render each shadow note alone (long), reverse its hall tail, end it at the note's entry
shadow = np.zeros((2, int(LENGTH * SR)), dtype=np.float32)
for p, s in rev_src:
    one = inst("grand")
    one.note(p, 0.0, 6.0, 52)
    one.pedal(0.0, 6.0)
    x = one.render(7.0)
    x = x + rig.hall(x, decay=6.0, size=45, predelay=10, high_cut=5000, late=100) * 1.5
    shadow += reverse_swell(x, s - 3.2, 3.2, LENGTH)

# ---------------------------------------------------------------- mix
g = rig.fx2(Pedalboard([HighpassFilter(60), LowpassFilter(3800), PeakFilter(250, 1.5, 0.8)]), g)
cel = rig.fx2(Pedalboard([HighpassFilter(500), LowpassFilter(6000)]), cel)
dr = rig.fx2(Pedalboard([HighpassFilter(45), LowpassFilter(1400)]), dr)
dr = rig.automate(dr, [(0, 14, -14), (14, 30, -5), (86, 150, -3), (210, LENGTH, -12)], ramp=10.0)
shadow = rig.fx2(Pedalboard([HighpassFilter(120), LowpassFilter(3000)]), shadow)
sub = rig.fx(Pedalboard([LowpassFilter(120)]), sub)
air = rig.fx(Pedalboard([HighpassFilter(150), LowpassFilter(2200)]), air)

g = rig.at_level(g, -24)
cel = rig.at_level(cel, -33)
dr = rig.at_level(dr, -27)
shadow = rig.at_level(shadow, -32)
sub = rig.pan(rig.at_level(sub, -30), 0)
dl = rig.pan(rig.at_level(drips_l, -36), -0.55)
drr = rig.pan(rig.at_level(drips_r, -36), 0.6)
dp = rig.pan(rig.at_level(deep, -34), 0.15)
air_st = np.stack([air, np.roll(air, 2400)])
air_st = rig.at_level(air_st, -40)

drip_bus = dl + drr + dp
music = g + cel
# the cave: everything distant, drips get a short slap + long tail
room = (rig.hall(music, decay=9.0, size=60, predelay=60, high_cut=4200, early=6, late=100) * 1.6
        + rig.hall(drip_bus, decay=4.5, size=50, predelay=25, high_cut=7000, early=40, late=80) * 1.2
        + rig.hall(dr + shadow, decay=7.0, size=55, predelay=30, high_cut=3000, early=5, late=90) * 0.6)
mix = music * 0.55 + cel * 0.3 + dr + shadow + sub + drip_bus + air_st + room

fi = int(6 * SR)
mix[:, :fi] *= np.linspace(0, 1, fi) ** 2                  # the cave fades up out of silence

sections = [(k, S[k], ([*S.values()] + [LENGTH])[i + 1]) for i, k in enumerate(S)]
master(mix, "05_dripstone", sections=sections,
       stems={"piano": g, "celesta": cel, "drone": dr, "shadow": shadow, "drips": drip_bus, "wind": air_st},
       fade_s=6.0, target_rms_db=-20.0, top_db=-4.0, tape_kw={"wow_cents": 4.0, "hiss_db": -64.0})
