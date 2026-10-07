"""One Context — 2. Tokens. A Dorian, 7/8 (2+2+3), eighth = 0.2 s.

The first message, tokenized. The marimba plays the token stream: one run of eighths per token, accented only on
the token's first eighth, so you can hear where the tokenizer cut; full stops are rests. The stream's length
never matches the 7/8 bar, so it phases against the groove. The guitar plays the NEXT token's pitch at every
boundary — it is always one prediction ahead. A 4/4 bridge re-flows the tokens at double speed; the climax
adds crunch guitars and xylophone; the stream ends on its last token, 'rock', and the sequence stops.
"""
import random
import sys
from pathlib import Path

import numpy as np
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, Compressor, PeakFilter, LowShelfFilter, Delay,
                        Chorus, HighShelfFilter)

from orch import Sampler, envelope, section_report, EP_OUT, SR
import rig
from rig import Track, Drums, amp, fx, pan, at_level

rng = random.Random(2)
E8 = 0.2

TOKENS = ["i", " want", " to", " see", " if", " you", " can", " write", " good", " rock", " music", ".", " download",
          " whatever", " lib", "r", "arry", " is", " n", "es", "essary", ".", " lets", " start", " with", " simple",
          " 4", ".", "4", " classic", " rock"]
DORIAN = [57, 59, 60, 62, 64, 66, 67]          # A B C D E F# G


def words_of(tokens):
    """Group tokens into words (a token starting with a space, or the first one, starts a new word)."""
    out, cur = [], []
    for tk in tokens:
        if (tk.startswith(" ") or not cur) and cur:
            out.append(cur)
            cur = []
        cur.append(tk)
    out.append(cur)
    return out


SCALE = sorted(p + 12 * o for p in DORIAN for o in range(0, 3))      # A3 .. G5


def token_cells(tokens):
    """Pitch = surprisal. Common, predictable tokens sit near the tonic; surprising ones leap up the scale
    (surprisal ~ 8 - Zipf word frequency). Tokens of words no dictionary knows — the typos — climb chromatically,
    a semitone off the scale: to a language model they are wrong notes."""
    from wordfreq import zipf_frequency
    cells = []
    for word_tokens in words_of(tokens):
        word = "".join(t.strip() for t in word_tokens)
        if word == ".":
            cells.append((None, 1))
            continue
        z = zipf_frequency(word, "en")
        for k, tk in enumerate(word_tokens):
            st = tk.strip()
            dur = 1 if len(st) <= 2 else 2 if len(st) <= 5 else 3
            if st == ".":
                cells.append((None, 1))
            elif z == 0:                                       # unknown word: the wrong notes
                cells.append((SCALE[9 + k] + 1, dur))
            else:
                surprisal = 8 - z
                cells.append((SCALE[min(len(SCALE) - 1, max(0, round((surprisal - 0.6) * 1.4)))], dur))   # most predictable = tonic
    return cells


STREAM = token_cells(TOKENS)
STREAM_LEN = sum(d for _, d in STREAM)          # in eighths

marimba, xylo = Sampler("Marimba.sfz"), Sampler("Xylophone.sfz")
pz_vln, pz_vla, pz_vc = Sampler("ViolinEnsPizz.sfz"), Sampler("ViolaEnsPizz.sfz"), Sampler("CelloEnsPizz.sfz")
s_vln, s_vc = Sampler("ViolinEnsSusVib.sfz"), Sampler("CelloEnsSusVib.sfz")
predict = Track("guitar")
crunchL, crunchR = Track("guitar"), Track("guitar")
bass = Track("bass", ccs={49: 127})
dr = Drums()

# ---------------------------------------------------------------- bar grid
SECTIONS = []
bars = []          # (start_eighth, n_eighths, chord, section)
CYCLE = ["Am", "D", "Am", "G"]


def add_bars(name, count, meter):
    start = bars[-1][0] + bars[-1][1] if bars else 0
    for i in range(count):
        s = bars[-1][0] + bars[-1][1] if bars else 0
        bars.append((s, meter, CYCLE[(len(bars)) % 4], name))
    SECTIONS.append((name, start * E8, (bars[-1][0] + bars[-1][1]) * E8))


add_bars("intro", 8, 7)
add_bars("A groove", 16, 7)
add_bars("B predict", 24, 7)
add_bars("C bridge 4/4", 12, 8)
add_bars("D climax", 24, 7)
TOTAL8 = bars[-1][0] + bars[-1][1]


def sec(e8_pos):
    for s, n, ch, name in bars:
        if s <= e8_pos < s + n:
            return name
    return None


# ---------------------------------------------------------------- the token stream (marimba) + prediction (guitar)
# play passes of the stream so that the final pass ends exactly at the end of the climax
cursor = TOTAL8 - STREAM_LEN * (TOTAL8 // STREAM_LEN + 1)   # starts before 0: enters mid-sequence, like a context
events = []                       # (eighth_pos, pitch, dur, token_index)
while cursor < TOTAL8:
    for ti, (p, d) in enumerate(STREAM):
        if cursor >= 0:
            events.append((cursor, p, d, ti))
        cursor += d

for i, (pos8, p, d, ti) in enumerate(events):
    name = sec(pos8)
    if p is None or name is None:
        continue
    bridge = name.startswith("C")
    step = E8 / 2 if bridge else E8                           # the bridge generates twice as fast
    reps = d * (2 if bridge else 1)
    for k in range(reps):
        tt = pos8 * E8 + k * step + rng.gauss(0, 0.004)
        if bridge and tt >= (pos8 + d) * E8:
            break
        v = 104 if k == 0 else 58 + rng.gauss(0, 4)
        marimba.note(p, tt, tt + 0.5, v)
        if name.startswith("D"):
            xylo.note(p + 12, tt, tt + 0.3, v - 10)
    # the guitar predicts: at this boundary it already plays the next token's pitch
    if name not in ("intro", "A groove"):
        nxt = next((q for _, q, _, _ in events[i + 1:i + 3] if q is not None), None)
        if nxt is not None:
            s = pos8 * E8 + rng.gauss(0, 0.004)
            predict.note(nxt - 12, s, s + d * E8 * 0.95, 96, "long" if d >= 2 else "down")

# ---------------------------------------------------------------- groove
ROOTS = {"Am": 33, "D": 38, "G": 31}
PIZZ = {"Am": [57, 60, 64, 69], "D": [57, 62, 66, 69], "G": [55, 59, 62, 67]}
SUS = {"Am": [64, 69, 72], "D": [66, 69, 74], "G": [62, 67, 71]}
CRUNCH = {"Am": [45, 52, 57, 60], "D": [50, 57, 62, 66], "G": [43, 50, 55, 59]}


def hit(name, e8, vel, sd=0.004):
    dr.hit(name, e8 * E8 + rng.gauss(0, sd), vel + rng.gauss(0, 4))


sec_index = {}
for bi, (s, n, ch, name) in enumerate(bars):
    r = ROOTS[ch]
    j = sec_index[name] = sec_index.get(name, -1) + 1        # bar number within its section
    if name == "intro" or (name == "D climax" and j < 2):  # the drop: tokens alone before the climax lands
        continue
    if n == 7:                                     # 2 + 2 + 3
        groups = [0, 2, 4]
        for k in range(7):
            hit("hh_closed" if name != "D climax" else "ride", s + k, 92 if k in groups else 60)
        hit("kick", s, 112); hit("kick", s + 4, 106)
        if bi % 2:
            hit("kick", s + 6, 92)                                 # alternate bars push into the next downbeat
        hit("snare", s + 2, 118); hit("snare", s + 5, 112)
        hit("snare", s + 1, 38); hit("snare", s + 3.5, 34)         # ghosts
        if j % 4 == 3 and name != "D climax":
            hit("hh_open", s + 6, 96)
        if name == "B predict":
            for g in groups:
                hit("ride_bell", s + g, 84)
        if name == "D climax" and j == 2:
            hit("crash_l", s, 127); hit("crash_r", s, 124)
        if bi % 4 == 3:
            hit("tom1", s + 5.5, 100); hit("tom2", s + 6, 104); hit("tom3", s + 6.5, 108)
        if name == "D climax" and j % 4 == 2 and j > 2:
            hit("crash_l", s, 118)
        line = [(0, r, 1.6), (2, r, 0.9), (3, r + 7, 0.9), (4, r + 12, 0.9), (5, r + 10, 0.9), (6, r + 7, 0.9)]
    else:                                          # 4/4 bridge: half time, open
        for k in range(8):
            hit("ride", s + k, (84 if k % 2 == 0 else 60) - (20 if j < 8 else 0))
        if j >= 8:                                          # the breakdown breathes, then the kick returns
            hit("kick", s, 100); hit("snare", s + 4, 108)
        else:
            hit("snare", s + 4, 70)
        line = [(0, r, 3.8), (4, r + 7, 1.8), (6, r + 12, 1.8)]
        for p in SUS[ch]:
            s_vln.note(p, s * E8, (s + n) * E8 + 0.2, 56)
        s_vc.note(r + 12, s * E8, (s + n) * E8 + 0.2, 58)
    for off, p, d in line:
        t0 = (s + off) * E8 + rng.gauss(0, 0.004)
        bass.note(p, t0, t0 + d * E8, 108, "down" if off % 2 == 0 else "up")
    if name in ("B predict", "D climax") and n == 7:
        for off in (0, 4):
            for p in PIZZ[ch]:
                (pz_vln if p >= 60 else pz_vla).note(p + 12 if p >= 64 else p, (s + off) * E8, (s + off) * E8 + 0.3, 92)
            pz_vc.note(r + 12, (s + off) * E8, (s + off) * E8 + 0.3, 96)
    if name == "D climax" and j >= 2:
        for off, d in ((0, 2), (2, 2), (4, 3)):
            for tr, sd in ((crunchL, 0.003), (crunchR, 0.006)):
                t0 = (s + off) * E8 + rng.gauss(0, sd)
                for k, p in enumerate(CRUNCH[ch]):
                    tr.note(p, t0 + k * 0.005, t0 + d * E8 * 0.9, 112, "down")

# end of sequence: one last hit together, then nothing
EOS = TOTAL8 * E8
for p in CRUNCH["Am"]:
    crunchL.note(p, EOS, EOS + 1.6, 120, "down"); crunchR.note(p, EOS, EOS + 1.6, 118, "down")
bass.note(33, EOS, EOS + 1.6, 115, "down")
marimba.note(57, EOS, EOS + 1.0, 110); marimba.note(69, EOS, EOS + 1.0, 100)
hit("crash_l", TOTAL8, 124); hit("kick", TOTAL8, 124)
END = EOS + 3.5
SECTIONS.append(("EOS", EOS, END))

# ---------------------------------------------------------------- render & mix
print(f"Tokens: {END:.1f}s, stream = {STREAM_LEN} eighths against a 7-eighth bar")
n = int(END * SR)
orch = {k: s.render(END)[:, :n] for k, s in dict(marimba=marimba, xylo=xylo, pz_vln=pz_vln, pz_vla=pz_vla,
                                                 pz_vc=pz_vc, s_vln=s_vln, s_vc=s_vc).items()}
gp = amp(predict.render(END), "JVM-CL-GR-Cab", peak_in=0.25)
cL = amp(crunchL.render(END), "Bug333-Crunch-Cab", peak_in=0.6)
cR = amp(crunchR.render(END), "JVM-OD2-RD-Cab", peak_in=0.35)
bs = bass.render(END)
kit = dr.render(END)

gp = fx(Pedalboard([HighpassFilter(120), PeakFilter(2500, 2, 1), Chorus(rate_hz=0.6, depth=0.2, mix=0.3),
                    Compressor(-24, 3, 5, 100)]), gp)
gp_echo = fx(Pedalboard([Delay(E8 * 3, 0.35, 1.0), LowpassFilter(4000)]), gp)
crunch_fx = Pedalboard([HighpassFilter(90), PeakFilter(450, -3, 1), LowpassFilter(9500), Compressor(-20, 2.5, 8, 120)])
cL, cR = fx(crunch_fx, cL), fx(crunch_fx, cR)
bs = fx(Pedalboard([HighpassFilter(30), LowShelfFilter(100, 2), LowpassFilter(4000), Compressor(-22, 4, 5, 100)]), bs)
drm = rig.drum_bus(kit, room=0.55, hat_db=-1)
drm = drm * (10 ** (-16 / 20) / rig.active_rms(drm.mean(0)))
cl = 10 ** ((-16 + 8) / 20)
drm = cl * np.tanh(drm / cl)


def place(x, p, db):
    x = x * (10 ** (db / 20) / rig.active_rms(x.mean(0)))
    m = x.mean(0)
    side = (x[0] - x[1]) * 0.3
    l, r = pan(m, p)
    return np.stack([l + side, r - side])


mix = (place(orch["marimba"], 0.0, -15) + place(orch["xylo"], 0.25, -24) + place(orch["pz_vln"], -0.5, -22)
       + place(orch["pz_vla"], 0.1, -24) + place(orch["pz_vc"], 0.45, -22) + place(orch["s_vln"], -0.4, -23)
       + place(orch["s_vc"], 0.4, -25)
       + pan(at_level(gp, -19), 0.45) + pan(at_level(gp_echo, -27), -0.45)
       + pan(at_level(cL, -17.5), -0.9) + pan(at_level(cR, -17.5), 0.9) + pan(at_level(bs, -17), 0) + drm)
send = orch["marimba"].mean(0) * 0.2 + (orch["s_vln"].mean(0) + orch["s_vc"].mean(0)) * 0.6 + at_level(gp, -19) * 0.25
mix += rig.stereo_reverb(send, room=0.6) * 0.4

master = Pedalboard([HighpassFilter(25), LowShelfFilter(90, 1.0), HighShelfFilter(9000, 1.0), Compressor(-14, 2, 15, 150)])
sec_t = {nm: (a, b) for nm, a, b in SECTIONS}
mix = rig.automate(mix, [(*sec_t["A groove"], -1.5), (*sec_t["B predict"], -2.5), (*sec_t["C bridge 4/4"], -4.5)], ramp=0.4)
section_report(mix, SECTIONS)
rig.finish(mix, EP_OUT / "02_tokens", master, fade_s=1.5, target_rms_db=-13)
