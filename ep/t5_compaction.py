"""One Context — 5. Compaction. A 120 BPM pulse; no key until the end.

The context is full, so it is summarised to keep going. A steady pulse holds the thread while the actual audio of
tracks 1-4 is replayed in order, as a running summary — first at 2x speed, then 4x, 8x, 16x: each pass covers more
of the past, more coarsely. Fidelity falls with it (bit depth, sample rate, stereo width). A whisper narrates what
is kept. Then the summary stutters and collapses into one chord — C add9 — which is where the last track begins.
"""
import random

import numpy as np
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, Compressor, Bitcrush, Resample, LowShelfFilter,
                        time_stretch, Gain)

from orch import Sampler, section_report, EP_OUT, SR
import rig
import synth
import hiphop as H
from rig import Drums, pan, at_level

rng = random.Random(5)
SPB = 0.5
BAR = 4 * SPB

src = {i: H.load(EP_OUT / f"{name}.wav", mono=False) for i, name in
       ((1, "01_cold_start"), (2, "02_tokens"), (3, "03_attention"), (4, "04_hallucination"))}
PASSES = [  # (time compression, source start per track, bits, sample rate, stereo width, whisper)
    (2, {1: 100, 2: 60, 3: 150, 4: 50}, 14, 32000, 1.0, "A cold start. A message, read one letter at a time."),
    (4, {1: 60, 2: 20, 3: 100, 4: 90}, 10, 16000, 0.7, "Tokens. Always guessing the next one."),
    (8, {1: 30, 2: 40, 3: 60, 4: 20}, 7, 8000, 0.4, "Attention. Agreement."),
    (16, {1: 80, 2: 50, 3: 100, 4: 55}, 5, 4000, 0.0, "A confident mistake. Corrected."),
]
INTRO_BARS, PASS_BARS, COLLAPSE_BARS = 2, 8, 4
pass_len = PASS_BARS * BAR
total_bars = INTRO_BARS + PASS_BARS * len(PASSES) + COLLAPSE_BARS
END = total_bars * BAR
n = int(END * SR)

summary = np.zeros((2, n), dtype=np.float32)
SECTIONS = [("intro", 0, INTRO_BARS * BAR)]
for pi, (factor, starts, bits, rate, width, _) in enumerate(PASSES):
    p0 = (INTRO_BARS + pi * PASS_BARS) * BAR
    SECTIONS.append((f"pass {factor}x", p0, p0 + pass_len))
    seg_len = pass_len / 4                                     # each remembered track gets a quarter of the pass
    for k in (1, 2, 3, 4):
        x = H.excerpt(src[k], starts[k], seg_len * factor)
        y = time_stretch(x, SR, stretch_factor=float(factor))  # compress time, keep pitch
        y = Pedalboard([Resample(target_sample_rate=rate), Bitcrush(bit_depth=bits)])(y, SR)
        mid, side = y.mean(0), (y[0] - y[1]) / 2 * width
        y = np.stack([mid + side, mid - side])
        i0 = int((p0 + (k - 1) * seg_len) * SR)
        m = min(y.shape[1], int(seg_len * SR), n - i0)
        f = int(0.01 * SR)
        y = y[:, :m].copy()
        y[:, :f] *= np.linspace(0, 1, f)
        y[:, -f:] *= np.linspace(1, 0, f)
        summary[:, i0:i0 + m] += y

# collapse: the last half-bar of the summary repeats, shorter and shorter, then the chord takes over
c0 = (INTRO_BARS + PASS_BARS * len(PASSES)) * BAR
SECTIONS.append(("collapse", c0, END))
tail = summary[:, int((c0 - SPB) * SR):int(c0 * SR)].copy()
pos = int(c0 * SR)
L = tail.shape[1]
while pos < int((c0 + 2 * BAR) * SR) and L > 400:
    seg = tail[:, :L] * np.linspace(1, 0.6, L)
    k = min(L, n - pos)
    summary[:, pos:pos + k] += seg[:, :k]
    pos += L
    L = int(L * 0.8)

chord = {"vln": Sampler("ViolinEnsSusVib.sfz"), "vla": Sampler("ViolaEnsSusVib.sfz"), "vc": Sampler("CelloEnsSusVib.sfz"),
         "cb": Sampler("ContrabassSusVB.sfz")}
CADD9 = {"cb": [36], "vc": [48, 55], "vla": [55, 62], "vln": [64, 67, 74]}
for k, ps in CADD9.items():
    for p in ps:
        chord[k].note(p, c0 + BAR * 0.5, END + 1.0, 70)

# the pulse: kick on every beat, hats on eighths, steady until the collapse
dr = Drums()
kicks = []
for b in range(int((c0 + BAR) / SPB)):
    tt = b * SPB
    dr.hit("kick", tt, 108)
    kicks.append(tt)
    dr.hit("hh_closed", tt + SPB / 2, 70)
    if b % 4 == 2:
        dr.hit("rim", tt, 64)

# the whisper
voice = np.zeros(n, dtype=np.float32)
for pi, p in enumerate(PASSES):
    a = H.say("en_US-ryan-high", p[5], speed=1.0, expressive=0.9)
    i0 = int(((INTRO_BARS + pi * PASS_BARS) * BAR + 0.3) * SR)
    voice[i0:i0 + len(a)] += a[:n - i0]
a = H.say("en_US-ryan-high", "Keep only this.", speed=0.9, expressive=0.9)
i0 = int((c0 + 2.2 * BAR) * SR)
voice[i0:i0 + len(a)] += a[:n - i0]

# ---------------------------------------------------------------- mix
print(f"Compaction: {END:.1f}s")
kit = dr.render(END)
drm = rig.drum_bus(kit, room=0.25, kick_db=2)
drm = drm * (10 ** (-18 / 20) / rig.active_rms(drm.mean(0)))
subk = at_level(synth.sub_kick(kicks, END), -22)
ch = sum(rig.fx2(Pedalboard([HighpassFilter(30)]), s.render(END)[:, :n]) for s in chord.values())
ch = ch * (10 ** (-17 / 20) / rig.active_rms(ch.mean(0)))
ch = ch * np.clip((np.arange(n) / SR - c0) / (2 * BAR), 0, 1) ** 1.5      # swells in under the stutter
summary = summary * (10 ** (-16 / 20) / rig.active_rms(summary.mean(0)))
voice = rig.fx(Pedalboard([HighpassFilter(250), LowpassFilter(3500), Bitcrush(bit_depth=10), Compressor(-26, 4, 2, 80)]), voice)
voice = at_level(voice, -23)
env = np.convolve(np.abs(voice), np.ones(int(0.08 * SR)) / int(0.08 * SR), mode="same")
duck = 1 - 0.5 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)    # summary steps back while the whisper speaks
summary = summary * duck

mix = summary + drm + pan(subk, 0) + ch + pan(voice, 0) + rig.stereo_reverb(voice * 0.4 + ch.mean(0) * 0.5, room=0.7) * 0.5
section_report(mix, SECTIONS)
master = Pedalboard([HighpassFilter(25), LowShelfFilter(80, 1.0), Compressor(-14, 2, 10, 150)])
rig.finish(mix, EP_OUT / "05_compaction", master, fade_s=0.05, target_rms_db=-14)   # no fade: it runs into track 6
