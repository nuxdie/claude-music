"""One Context — 3. Attention. D minor, 66 BPM. String choir, piano, tubular bell.

A mensuration canon: one melody — descending phrases from A that grow by one note each time (A; A G; A G F; ...),
long-short rhythm — played simultaneously by solo violin (1x), violins (1/2x), violas (1/4x), cellos (1/8x) and
basses (1/16x), each an octave lower. The piano is a tintinnabuli voice: every melody note is answered by the
nearest note of D minor's triad (D F A). The attention rule: every 50 ms, each voice's level rises with the
number of other voices sounding the same pitch class — agreement blooms. A long crescendo; everyone converges
on D; hard cut; the hall keeps ringing; the bell.
"""
import random

import numpy as np
from pedalboard import Pedalboard, HighpassFilter, LowShelfFilter, Compressor, PeakFilter, HighShelfFilter

from orch import Sampler, Layer, vpo, GRAND, section_report, EP_OUT, SR
import rig

rng = random.Random(3)
SPB = 60 / 66


def t(b):
    return b * SPB


AEOLIAN = [62, 64, 65, 67, 69, 70, 72]                 # D E F G A Bb C
SCALE = sorted(p + 12 * o for p in AEOLIAN for o in range(-4, 3))
TRIAD = sorted(p + 12 * o for p in (62, 65, 69) for o in range(-4, 3))


def m_line(top, phrases):
    """(beat, dur, pitch) for the growing descending phrases, long-short rhythm, starting each phrase on `top`."""
    i_top = SCALE.index(top)
    out, b = [], 0.0
    for k in range(1, phrases + 1):
        for j in range(k):
            dur = 2.0 if j % 2 == 0 else 1.0
            out.append((b, dur, SCALE[i_top - j]))
            b += dur
        b += 1.0                                         # a breath between phrases
    return out


BASE = m_line(81, 16)                                    # A5 down, sixteen phrases
VOICES = [  # name, sfz, speed divisor, transpose, lowest playable
    ("solo", "SViolinVib.sfz", 1, 0, 55),
    ("vln", "ViolinEnsSusVib.sfz", 2, -12, 55),
    ("vla", "ViolaEnsSusVib.sfz", 4, -24, 48),
    ("vc", "CelloEnsSusVib.sfz", 8, -36, 36),
    ("cb", "ContrabassSusVB.sfz", 16, -48, 28),
]
CONVERGE = 176.0                                         # beat where everyone gathers on D
CUT = CONVERGE + 8
END = t(CUT) + 9.0

samp = {}
timeline = {}                                            # voice -> list of (start_s, end_s, pitch)
for name, sfz, div, tr, low in VOICES:
    samp[name] = Sampler(sfz, legato=(name == "solo"))
    if name == "vln":
        samp[name] = Layer((samp[name], 0), (Sampler(vpo("Strings/1st-violin-SEC-sustain.sfz")), -7))
    elif name == "vc":
        samp[name] = Layer((samp[name], 0), (Sampler(vpo("Strings/cello-SEC-sustain.sfz")), -7))
    timeline[name] = []
    for b, d, p in BASE:
        b, d = b * div, d * div
        if b >= CONVERGE:
            break
        p = p + tr
        while p < low:
            p += 12
        e = min(b + d, CONVERGE)
        vel = 50 + 60 * (b / CONVERGE)                   # the long crescendo is also played, not just mixed
        samp[name].note(p, t(b) + rng.gauss(0, 0.02), t(e) + 0.15, vel)
        timeline[name].append((t(b), t(e), p))

# tintinnabuli: piano answers the two fastest voices — above the solo violin, below the violins
piano = Sampler(str(GRAND))
for name, above in (("solo", True), ("vln", False)):
    for s, e, p in timeline[name]:
        q = min((x for x in TRIAD if (x > p if above else x < p)), key=lambda x: abs(x - p))
        q = q - 12 if above else q
        vel = 40 + 50 * (s / t(CONVERGE))
        piano.note(q, s + 0.01, e + 0.6, vel)
        timeline.setdefault("piano", []).append((s, e, q))

solo_on = sorted(s for s, _, _ in timeline["solo"])
for a, b in zip(solo_on, solo_on[1:] + [t(CONVERGE)]):    # re-pedal with each melody note: resonance, no smear
    piano.pedal(a + 0.05, b - 0.03)

# convergence: D everywhere (with the A above it in the upper voices), then the cut
FINAL = {"solo": [74], "vln": [62, 69], "vla": [50, 57], "vc": [38], "cb": [26]}
for name, ps in FINAL.items():
    for p in ps:
        samp[name].note(p, t(CONVERGE), t(CUT), 96)
        timeline[name].append((t(CONVERGE), t(CUT), p))
for p in (38, 50, 62, 65, 69):
    piano.note(p, t(CONVERGE), t(CUT), 78)
samp["choir"] = Sampler(vpo("Vocals/choir-MIXED-sustain.sfz"))   # at the convergence, voices: D and A
timeline["choir"] = []
for p in (50, 57, 62, 69):
    samp["choir"].note(p, t(CONVERGE), t(CUT), 92)
    timeline["choir"].append((t(CONVERGE), t(CUT), p))
bell = Sampler("TubularBells.sfz")
for k in range(3):                                       # three strikes to open
    bell.note(62, t(1.5 * k), t(1.5 * k) + 6, 80 - 14 * k)
for b in np.arange(16, CONVERGE, 16):
    bell.note(62, t(b), t(b) + 6, 50 + 30 * b / CONVERGE)
bell.note(62, t(CUT) + 3.5, t(CUT) + 9, 60)               # after the cut, once

# ---------------------------------------------------------------- attention weights
RES = 0.05
frames = int(END / RES) + 1
pcs = {}
for name, notes in timeline.items():
    a = np.full(frames, -1, dtype=int)
    for s, e, p in notes:
        a[int(s / RES):int(e / RES)] = p % 12
    pcs[name] = a
weights = {}
for name in pcs:
    match = sum(((pcs[name] == pcs[o]) & (pcs[name] >= 0)).astype(float) for o in pcs if o != name)
    db = 6.0 * (1 - np.exp(-match / 1.5))               # agreement swells, saturating near +6 dB
    db = np.convolve(db, np.ones(8) / 8, mode="same")     # ~0.4 s smoothing: swells, not switches
    weights[name] = db

# ---------------------------------------------------------------- render & mix
print(f"Attention: {END:.1f}s")
n = int(END * SR)
progress = lambda tt: np.clip(tt / t(CONVERGE), 0, 1) ** 1.3       # soft strings bloom into full bows
st = {k: s.render_dynamic(END, progress)[:, :n] for k, s in samp.items()}
st["piano"] = piano.render(END)[:, :n]
bl = bell.render(END)[:, :n]

LV = {"solo": -20, "vln": -21, "vla": -23, "vc": -22, "cb": -25, "piano": -22, "choir": -21}
POS = {"solo": -0.25, "vln": -0.6, "vla": 0.1, "vc": 0.45, "cb": 0.65, "piano": 0.0, "choir": 0.0}
dry = np.zeros((2, n), dtype=np.float32)
send = np.zeros(n, dtype=np.float32)
for k, x in st.items():
    x = rig.fx2(Pedalboard([HighpassFilter(30 if k == "cb" else 60)]), x)
    x = x * (10 ** (LV[k] / 20) / rig.active_rms(x.mean(0)))
    g = 10 ** (np.interp(np.arange(n) / SR, np.arange(frames) * RES, weights[k]) / 20)
    x = x * g
    m = x.mean(0)
    side = (x[0] - x[1]) * 0.1
    l, r = rig.pan(m, POS[k])
    dry += np.stack([l + side, r - side])
    send += m
crescendo = 10 ** (np.interp(np.arange(n) / SR, [0, t(CONVERGE), t(CUT)], [-7, 0, -2]) / 20)
dry *= crescendo
send *= crescendo
cut_i = int(t(CUT) * SR)
fade = int(0.04 * SR)
dry[:, cut_i:cut_i + fade] *= np.linspace(1, 0, fade)
dry[:, cut_i + fade:] = 0                                  # the hard cut...
send[cut_i + fade:] = 0
wet = rig.stereo_reverb(send, room=0.92, damping=0.4) * 0.45    # ...but the hall keeps ringing
wm, ws = (wet[0] + wet[1]) / 2, (wet[0] - wet[1]) / 2 * 0.5      # a narrower hall: keep a centre
wet = np.stack([wm + ws, wm - ws])
bl = bl * (10 ** (-23 / 20) / rig.active_rms(bl.mean(0)))
mix = dry + wet + bl + rig.stereo_reverb(bl.mean(0), room=0.9) * 0.5

SECTIONS = [("opening", 0, t(40)), ("middle", t(40), t(110)), ("swelling", t(110), t(CONVERGE)),
            ("converge", t(CONVERGE), t(CUT)), ("hall", t(CUT), END)]
section_report(mix, SECTIONS)
master = Pedalboard([HighpassFilter(25), PeakFilter(330, -2.5, 0.8), HighShelfFilter(5000, 3.0), HighShelfFilter(12000, 2.0),
                     Compressor(-16, 1.6, 40, 300)])
rig.finish(mix, EP_OUT / "03_attention", master, fade_s=3.0, target_rms_db=-15)
