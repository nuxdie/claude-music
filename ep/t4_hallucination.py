"""One Context — 4. Hallucination. E-flat minor -> (confidently, wrongly) E major. Trip-hop, 84 BPM.

Lo-fi half-time drums and sub bass hold steady while the music around them slowly drifts: a tape-wow on the
music bus deepens through the track. A solo violin sings in E-flat minor. At the pivot, C-flat7 — which in this
key should fall to B-flat — is re-read as its enharmonic twin B7, the dominant of E, and the whole band lands in
E major with total conviction. The bass refuses for one bar, then agrees. Tape stop. Silence. Then, dry and
quiet, the true chord: E-flat minor. A correction.
"""
import math
import random

import numpy as np
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, Compressor, PeakFilter, LowShelfFilter, Bitcrush,
                        Distortion, Resample)

from orch import Sampler, section_report, EP_OUT, SR
import rig
import synth
import hiphop as H
from rig import Drums, pan, at_level

rng = random.Random(4)
SPB = 60 / 84


def t(b):
    return b * SPB


piano, vln, vla, vc, solo = (Sampler(f) for f in ("UprightPiano.sfz", "ViolinEnsSusVib-Quiet.sfz",
                                                  "ViolaEnsSusVib-Quiet.sfz", "CelloEnsSusVib-Quiet.sfz", "SViolinVib.sfz"))
solo.legato = True                                      # the violin sings slurred lines
dr = Drums()
bass_notes = []

CH = {  # (bass root, piano voicing, string voicing)
    "Ebm9": (27, [51, 58, 61, 65, 66], [58, 61, 65, 70]),
    "Cbmaj7": (35, [47, 54, 58, 63, 65], [58, 63, 66, 70]),
    "Abm7": (32, [44, 54, 59, 63, 66], [56, 59, 63, 68]),
    "Bb7": (34, [46, 56, 58, 62, 65], [56, 62, 65, 68]),
    "Cb7": (35, [47, 57, 59, 63, 66], [57, 63, 66, 71]),     # = B7: the pivot
    "Emaj9": (28, [52, 59, 63, 66, 68], [63, 66, 68, 71]),
    "C#m9": (37, [49, 56, 59, 63, 64], [59, 63, 64, 68]),
    "Amaj7": (33, [45, 56, 61, 64, 68], [61, 64, 68, 73]),
    "B7sus": (35, [47, 57, 61, 64, 66], [57, 61, 64, 69]),
}
MINOR = ["Ebm9", "Cbmaj7", "Abm7", "Bb7"]
MAJOR = ["Emaj9", "C#m9", "Amaj7", "B7sus"]


def to_major(p):
    """Re-hear an E-flat minor melody note in E major: up a semitone, minor degrees raised."""
    rel = (p - 63) % 12
    mapping = {0: 0, 2: 2, 3: 4, 5: 5, 7: 7, 8: 9, 10: 11, 11: 11, 4: 4, 9: 9, 1: 1, 6: 6}
    return p - rel + mapping[rel] + 1


MEL_A = [[(1, 1, 70), (2, 1, 73), (3, 1, 75)], [(0, 3, 77), (3, 1, 75)], [(0, 1.5, 73), (1.5, .5, 71), (2, 2, 70)],
         [(0, 2, 68), (2, 1, 66), (3, 1, 65)], [(0, 3, 66), (3, 1, 70)], [(0, 2, 75), (2, 1, 73), (3, 1, 71)],
         [(0, 1, 70), (1, 1, 68), (2, 2, 66)], [(0, 4, 65)]]
MEL_B = [[(0, 2, 78), (2, 1, 77), (3, 1, 75)], [(0, 3, 82), (3, 1, 80)], [(0, 1.5, 78), (1.5, .5, 77), (2, 2, 75)],
         [(0, 2, 73), (2, 2, 74)], [(0, 4, 75)], [(0, 2, 77), (2, 2, 78)], [(0, 1, 80), (1, 1, 78), (2, 2, 77)],
         [(0, 4, 74)]]


def hit(name, beat, vel, sd=0.006):
    dr.hit(name, t(beat) + rng.gauss(0, sd), vel + rng.gauss(0, 4))


def sw(step):
    return step * 0.25 + (0.05 if step % 2 else 0)


def groove(b0, i):
    stop_time = i % 8 == 6                                   # every 8th bar the floor drops out for a moment
    kicks = (0, 7, 10) if i % 2 == 0 else (0, 3, 10, 11)
    for st in kicks + ((14,) if i % 4 == 3 else ()):
        if not (stop_time and st > 0):
            hit("kick", b0 + sw(st), 112)
    for st in (4, 12):
        hit("snare", b0 + sw(st), 116)
    for st in (6, 9, 15) if i % 2 else (9,):
        hit("snare", b0 + sw(st), 30 + rng.random() * 12)    # ghosts
    for st in range(16):
        if i % 4 == 3 and st == 14:
            hit("hh_open", b0 + sw(st), 80)
        elif not (i % 4 == 3 and st == 15):
            hit("hh_closed", b0 + sw(st), 70 if st % 4 == 0 else (48 if st % 2 == 0 else 30))
    if i % 8 == 7:
        hit("snare", b0 + sw(15), 70)


def chord_bar(b0, name, piano_vel=58, strings_vel=48, solo_line=None, bass_root=None, strings=True):
    root, pv, sv = CH[name]
    for k, p in enumerate(pv):                             # slightly rolled, like a hand
        piano.note(p, t(b0) + k * 0.02 + rng.gauss(0, 0.01), t(b0 + 3.8), piano_vel - k * 2)
    piano.note(pv[-1] + 12, t(b0 + 2.5), t(b0 + 3.8), piano_vel - 14)
    if strings:
        for p in sv:
            (vln if p >= 62 else vla).note(p, t(b0), t(b0 + 4) + 0.2, strings_vel)
        vc.note(root + 12 if root + 12 >= 36 else root + 24, t(b0), t(b0 + 4) + 0.2, strings_vel)
    r = bass_root if bass_root is not None else root
    for st, d in ((0, 1.6), (2.5, 0.9), (3.5, 0.45)):
        bass_notes.append((r, t(b0 + st), t(b0 + st + d), 100))
    for beat, dur, p in (solo_line or []):
        solo.note(p, t(b0 + beat) + rng.gauss(0, 0.012), t(b0 + beat + dur) + 0.05, 74 + (8 if dur >= 2 else 0))


SECTIONS = []
bar = 0


def mark(name, n):
    SECTIONS.append((name, t(bar * 4), t((bar + n) * 4)))


mark("intro", 4)
for i in range(4):
    chord_bar(bar * 4, MINOR[i % 4], piano_vel=50, strings=(i >= 2))
    bar += 1
mark("A", 8)
for i in range(8):
    chord_bar(bar * 4, MINOR[i % 4], solo_line=MEL_A[i]); groove(bar * 4, i); bar += 1
mark("B", 8)
for i in range(8):
    chord_bar(bar * 4, MINOR[i % 4], strings_vel=60, solo_line=MEL_B[i]); groove(bar * 4, i); bar += 1
mark("drift", 4)
for i in range(4):
    chord_bar(bar * 4, MINOR[i % 4], piano_vel=44, solo_line=[(0, 4, 70)] if i % 2 == 0 else [])
    bar += 1
mark("C (pivot)", 8)
for i in range(8):
    name = MINOR[i % 4]
    line = [(b, d, p + 12 if p < 70 else p) for b, d, p in MEL_A[i]]
    if i == 7:
        name, line = "Cb7", [(0, 2, 75), (2, 2, 78)]          # F#/Gb over B7: the door opens
    chord_bar(bar * 4, name, strings_vel=62, solo_line=line); groove(bar * 4, i); bar += 1
mark("D wrong key", 8)
for i in range(8):
    line = [(b, d, to_major(p)) for b, d, p in (MEL_B[i])]
    chord_bar(bar * 4, MAJOR[i % 4], piano_vel=70, strings_vel=78, solo_line=line,
              bass_root=27 if i == 0 else None)                # the bass refuses for one bar
    groove(bar * 4, i)
    if i % 4 == 0:
        hit("crash_l", bar * 4, 110)
    bar += 1
STOP = t(bar * 4)
CORR = STOP + 2.6
END = CORR + 9.0
SECTIONS.append(("correction", CORR, END))

# ---------------------------------------------------------------- render
print(f"Hallucination: {END:.1f}s")
n = int(END * SR)
st = {k: s.render(END)[:, :n] for k, s in dict(piano=piano, vln=vln, vla=vla, vc=vc, solo=solo).items()}
kit = dr.render(END)
grit, sub = synth.synth_bass(bass_notes, END, cutoff=260, drive=8)

# the correction, rendered on its own: dry piano, one quiet violin note, true pitch
cp, cs = Sampler("UprightPiano.sfz"), Sampler("SViolinVib.sfz")
for k, p in enumerate([39, 51, 58, 61, 65, 66]):
    cp.note(p, CORR + k * 0.03, CORR + 7, 46 - k)
cs.note(66, CORR + 1.2, CORR + 6.5, 58)
corr = cp.render(END)[:, :n] * 1.0
corr_v = cs.render(END)[:, :n]

lofi = Pedalboard([Resample(target_sample_rate=22050), Bitcrush(bit_depth=12), LowpassFilter(7000), HighpassFilter(90),
                   Distortion(drive_db=3)])
music = np.zeros((2, n), dtype=np.float32)
LV = {"piano": -18, "vln": -24, "vla": -26, "vc": -25, "solo": -18}
POS = {"piano": 0.0, "vln": -0.55, "vla": 0.2, "vc": 0.5, "solo": 0.1}
send = np.zeros(n, dtype=np.float32)
for k, x in st.items():
    if k == "piano":
        x = rig.fx2(lofi, x)
    x = x * (10 ** (LV[k] / 20) / rig.active_rms(x.mean(0)))
    m = x.mean(0)
    side = (x[0] - x[1]) * 0.3
    l, r = pan(m, POS[k])
    music += np.stack([l + side, r - side])
    send += m * (0.5 if k != "piano" else 0.3)
music += rig.stereo_reverb(send, room=0.8, damping=0.5) * 0.5


def tape_wow(x, depth_ms):
    """Variable delay: two slow LFOs, depth (ms) given per sample. Pitch wobbles with the derivative."""
    tt = np.arange(x.shape[1]) / SR
    d = depth_ms / 1000 * (0.65 * np.sin(2 * np.pi * 0.45 * tt) + 0.35 * np.sin(2 * np.pi * 1.3 * tt + 1.0))
    idx = np.clip(np.arange(x.shape[1]) - (d + depth_ms.max() / 1000) * SR, 0, x.shape[1] - 1)
    return np.stack([np.interp(idx, np.arange(x.shape[1]), c) for c in x]).astype(np.float32)


depth = np.interp(np.arange(n) / SR, [0, STOP * 0.45, STOP * 0.6, STOP], [0.4, 2.0, 5.5, 7.0])
music = tape_wow(music, depth)

drm = rig.drum_bus(kit, room=0.3, kick_db=2, snare_db=1, hat_db=-3)
drm = rig.fx2(Pedalboard([Resample(target_sample_rate=26040), Bitcrush(bit_depth=12), LowpassFilter(9000),
                          Compressor(-22, 4, 5, 90), Distortion(drive_db=3)]), drm)
drm = drm * (10 ** (-17 / 20) / rig.active_rms(drm.mean(0)))
cl = 10 ** ((-17 + 8) / 20)
drm = cl * np.tanh(drm / cl)
bs = at_level(grit, -26) + at_level(sub, -20.5)
crk = at_level(H.crackle(END, density=4), -44)

mix = music + drm + pan(bs, 0) + pan(crk, 0)
synth.tape_stop(mix, STOP - 0.2, 1.6)
synth.silence(mix, STOP + 1.4, CORR - 0.01)
corr = corr * (10 ** (-22 / 20) / rig.active_rms(corr.mean(0)))
corr_v = corr_v * (10 ** (-26 / 20) / rig.active_rms(corr_v.mean(0)))
mix += corr + corr_v + rig.stereo_reverb((corr + corr_v).mean(0), room=0.5) * 0.25

section_report(mix, SECTIONS)
master = Pedalboard([HighpassFilter(25), LowShelfFilter(80, 1.5), PeakFilter(350, -1.5, 0.8), Compressor(-14, 2, 15, 150)])
rig.finish(mix, EP_OUT / "04_hallucination", master, fade_s=2.0, target_rms_db=-14)
