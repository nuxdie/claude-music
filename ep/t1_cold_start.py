"""One Context — 1. Cold Start. C major, 60 BPM.

Nothing; then one tone (the first token). The first message arrives on piano, one letter per note.
The second time, strings and harp hear it and harmonise it; then a solo violin answers with the message mirrored;
then everything says it together, softly; then only the first two words and the tone remain.
"""
import random

import numpy as np
from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, Compressor, PeakFilter, LowShelfFilter, HighShelfFilter

from orch import Sampler, Layer, vpo, GRAND, motif_words, envelope, sine, hz, section_report, speech_durs, EP_OUT, SR
import rig

rng = random.Random(1)
SPB = 1.0                           # 60 BPM


def t(b):
    return b * SPB


piano = Sampler(str(GRAND))                       # Salamander grand (Yamaha C5), real sustain pedal
vln = Layer((Sampler("ViolinEnsSusVib.sfz"), 0), (Sampler(vpo("Strings/1st-violin-SEC-sustain.sfz")), -7))
vc = Layer((Sampler("CelloEnsSusVib.sfz"), 0), (Sampler(vpo("Strings/cello-SEC-sustain.sfz")), -7))
_, vla, _, cb = (Sampler(f) for f in ("ViolinEnsSusVib.sfz", "ViolaEnsSusVib.sfz", "CelloEnsSusVib.sfz",
                                         "ContrabassSusVB.sfz"))
sopr = Sampler(vpo("Vocals/choir-FEMALE-sustain.sfz"), legato=True)
harp, glock, solo = Sampler("Harp.sfz"), Sampler(vpo("Keys/celesta.sfz")), Sampler("SViolinVib.sfz", legato=True)   # glock -> celesta

WORDS = motif_words()
CHORD = {  # my harmonisation of each word: (low -> high) string voicing
    "i": [48, 55, 62, 64, 67], "want": [45, 52, 60, 64, 67], "to": [41, 53, 57, 60, 64], "see": [40, 52, 55, 59, 62],
    "if": [38, 50, 53, 57, 64], "you": [41, 53, 57, 59, 64], "can": [36, 52, 55, 59, 64], "write": [38, 53, 57, 60, 62],
    "good": [43, 50, 53, 60, 62], "rock": [41, 53, 57, 60, 64], "music": [45, 52, 55, 60, 64],
}
END_CHORD = [36, 48, 55, 62, 64, 67]          # Cadd9


def phrase(b0, letter=0.5, gap=0.5, inst=(piano,), vel=(48, 62), transpose=0, pedal=1.2, mirror=False, words=None):
    """Play the message: a letter per `letter` beats, a breath after each word. Returns (end_beat, word starts)."""
    b = b0
    starts = []
    for wi, (w, notes) in enumerate(words or WORDS):
        starts.append((w, b))
        durs = speech_durs(w, letter * 0.7)                 # vowels sing, consonants are short
        if piano in inst:                                   # legato pedalling: catch each word, lift before the next
            piano.pedal(t(b) + 0.06, t(b + sum(durs) + gap) - 0.03)
        for k, p in enumerate(notes):
            if mirror:                                  # invert around D4, snapped back into C major
                q = 124 - p
                p = min((c + 12 * o for c in (60, 62, 64, 65, 67, 69, 71) for o in (-2, -1, 0, 1)), key=lambda c: abs(c - q))
            dur = durs[k]
            arc = np.sin(np.pi * (wi + k / len(notes)) / len(WORDS))     # the phrase rises and falls
            v = vel[0] + (vel[1] - vel[0]) * arc + rng.gauss(0, 3)
            for ins in inst:
                hold = 0.05 if ins is piano else pedal          # the pedal sustains the piano, not long notes
                ins.note(p + transpose, t(b) + rng.gauss(0, 0.01), t(b + dur + hold), v)
            b += dur
        b += gap
    return b, starts


def strings(starts, end_b, vel=46, octave_up=False):
    for i, (w, b) in enumerate(starts):
        nb = starts[i + 1][1] if i + 1 < len(starts) else end_b
        v = CHORD[w]
        cb.note(v[0] - 12 if v[0] >= 40 else v[0], t(b), t(nb) + 0.3, vel)
        vc.note(v[0], t(b), t(nb) + 0.3, vel + 2)
        vla.note(v[1], t(b), t(nb) + 0.3, vel)
        vla.note(v[2], t(b), t(nb) + 0.3, vel - 4)
        for p in v[3:]:
            vln.note(p + (12 if octave_up else 0), t(b), t(nb) + 0.3, vel)


def harp_arps(starts, vel=60):
    for w, b in starts:
        v = CHORD[w]
        for k, p in enumerate([v[0] + 12, v[1] + 12, v[2] + 12, v[3] + 12, v[4] + 12]):
            harp.note(p, t(b + k * 0.18), t(b + 3), vel - k * 3)


SECTIONS = []
# 0. silence, then the first token
FIRST = sine(hz(72), 2.0, 9.0, 300, amp=0.12, att=2.5, rel=3.0)
b = 7.0
# A. the message, alone
s0 = b
b, _ = phrase(b, vel=(44, 58))
SECTIONS.append(("A message", t(s0), t(b)))
b += 2
# B. heard: strings + harp harmonise it
s0 = b
end_b, starts = phrase(b, vel=(50, 66))
strings(starts, end_b, vel=44)
harp_arps(starts, vel=54)
b = end_b
SECTIONS.append(("B heard", t(s0), t(b)))
b += 1
# C. answered: the solo violin plays the message mirrored, slower; cellos carry the original underneath
s0 = b
end_b, starts = phrase(b, letter=0.75, gap=0.75, inst=(solo,), vel=(58, 80), transpose=12, mirror=True, pedal=0.05)
phrase(b, letter=0.75, gap=0.75, inst=(vc,), vel=(40, 52), transpose=-12, pedal=0.05)
strings(starts, end_b, vel=38)
b = end_b
SECTIONS.append(("C answered", t(s0), t(b)))
b += 1
# D. together: piano + glockenspiel + violins sing it, full chords, harp
s0 = b
end_b, starts = phrase(b, inst=(piano, glock), vel=(54, 74))
phrase(b, inst=(vln,), vel=(48, 64), transpose=12, pedal=0.05)
phrase(b, inst=(sopr,), vel=(44, 58), transpose=12, pedal=0.05)      # human voices join: everyone says it
strings(starts, end_b, vel=54)
harp_arps(starts, vel=64)
b = end_b
SECTIONS.append(("D together", t(s0), t(b)))
# E. only the first words remain, then the tone
s0 = b + 1
for p in END_CHORD:
    (cb if p < 40 else vc if p < 50 else vla if p < 60 else vln).note(p, t(b + 1), t(b + 14), 40)
phrase(b + 2, words=WORDS[:2], vel=(46, 40), letter=0.75, pedal=3)
LAST = sine(hz(72), t(b + 8), t(b + 16), 300, amp=0.12, att=3.0, rel=4.0)
END = t(b + 21)
SECTIONS.append(("E remain", t(s0), END))

# ---------------------------------------------------------------- render & mix
print(f"Cold Start: {END:.1f}s")
n = int(END * SR)
DYN_T = [0] + [x for sec in SECTIONS for x in (sec[1], sec[2])] + [END]
DYN_V = [0] + [x for sec, v in zip(SECTIONS, (0.0, 0.3, 0.2, 0.75, 0.1)) for x in (v, v)] + [0.1]
dyn = lambda tt: np.interp(tt, DYN_T, DYN_V)
st = {k: (s.render_dynamic(END, dyn) if k in ("vln", "vla", "vc", "cb") else s.render(END))
      for k, s in dict(piano=piano, vln=vln, vla=vla, vc=vc, cb=cb, harp=harp, glock=glock, solo=solo, sopr=sopr).items()}
tone = (FIRST[:n] + LAST[:n])


def place(x, p):            # narrow a stereo stem and seat it at pan p (orchestral seating)
    m = x.mean(0)
    side = (x[0] - x[1]) * 0.25
    l, r = rig.pan(m, p)
    return np.stack([l + side, r - side])


lv = {"piano": -19, "vln": -22, "vla": -25, "vc": -23, "cb": -27, "harp": -25, "glock": -28, "solo": -21, "sopr": -25}
pos = {"piano": 0.0, "vln": -0.55, "vla": 0.15, "vc": 0.45, "cb": 0.6, "harp": -0.35, "glock": -0.2, "solo": -0.15, "sopr": -0.1}
mix = np.zeros((2, n), dtype=np.float32)
send = np.zeros(n, dtype=np.float32)
for k, x in st.items():
    x = rig.fx2(Pedalboard([HighpassFilter(35 if k == "cb" else 60)]), x[:, :n])
    x = x * (10 ** (lv[k] / 20) / rig.active_rms(x.mean(0)))
    mix += place(x, pos[k])
    send += x.mean(0) * (0.5 if k in ("vln", "vla", "vc", "cb", "solo") else 0.35)
tone = tone * (10 ** (-27 / 20) / rig.active_rms(tone))
mix += rig.pan(tone, 0)
send += tone * 0.6
mix += rig.stereo_reverb(send, room=0.9, damping=0.45) * 0.6
mix += rig.pan(np.random.default_rng(0).standard_normal(n).astype(np.float32) * 10 ** (-72 / 20), 0)   # room tone

master = Pedalboard([HighpassFilter(25), PeakFilter(330, -2.5, 0.8), HighShelfFilter(5000, 3.0), HighShelfFilter(12000, 2.0),
                     Compressor(-20, 1.5, 40, 300)])
section_report(mix, SECTIONS)
rig.finish(mix, EP_OUT / "01_cold_start", master, fade_s=4.0, target_rms_db=-17.5)
