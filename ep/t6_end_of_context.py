"""One Context — 6. End of Context. C major, 72 BPM. Full ensemble.

Picks up on Compaction's C add9 chord. The first message comes back, slowed: piano, then the French horn sings all
of it while strings harmonise each word as in 'Cold Start' and two clean guitars phase underneath. The build:
tremolo strings, timpani, the message in violins at its original speed. The climax: brass carry the message in
long tones over a wall of guitars and full drums, landing on C add9. Then everything stops; the piano begins the
message once more and is cut off mid-word. The first token sounds one last time. Hard cut.
"""
import random

import numpy as np
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, Compressor, PeakFilter, LowShelfFilter,
                        HighShelfFilter, Chorus, Delay)

from orch import Sampler, Layer, vpo, GRAND, motif_words, sine, hz, section_report, speech_durs, EP_OUT, SR
import rig
from rig import Track, Drums, amp, fx, pan, at_level

rng = random.Random(6)
SPB = 60 / 72


def t(b):
    return b * SPB


WORDS = motif_words()
CHORD = {
    "i": [48, 55, 62, 64, 67], "want": [45, 52, 60, 64, 67], "to": [41, 53, 57, 60, 64], "see": [40, 52, 55, 59, 62],
    "if": [38, 50, 53, 57, 64], "you": [41, 53, 57, 59, 64], "can": [36, 52, 55, 59, 64], "write": [38, 53, 57, 60, 62],
    "good": [43, 50, 53, 60, 62], "rock": [41, 53, 57, 60, 64], "music": [45, 52, 55, 60, 64],
}
CADD9 = [36, 48, 55, 62, 64, 67]

S = {k: Sampler(f) for k, f in dict(
    piano="UprightPiano.sfz", vln="ViolinEnsSusVib.sfz", vla="ViolaEnsSusVib.sfz", vc="CelloEnsSusVib.sfz",
    cb="ContrabassSusVB.sfz", vln_tr="ViolinEnsTrem.sfz", vc_tr="CelloEnsTrem.sfz", harp="Harp.sfz",
    glock="Glockenspiel.sfz", horn="FHornSus.sfz", tpt="TrumpetSusVib.sfz", tbn="TromboneVib.sfz",
    timp="Timpani.sfz", timp_roll="TimpaniRolls.sfz").items()}
# upgrades: concert grand; string sections doubled with VPO; climax brass as solo + full sections; celesta
S["piano"] = Sampler(str(GRAND))
S["horn"].legato = True                                 # the theme horn slurs within words
S["vln"] = Layer((S["vln"], 0), (Sampler(vpo("Strings/1st-violin-SEC-sustain.sfz")), -7))
S["vc"] = Layer((S["vc"], 0), (Sampler(vpo("Strings/cello-SEC-sustain.sfz")), -7))
S["vln_tr"] = Layer((S["vln_tr"], 0), (Sampler(vpo("Strings/1st-violin-SEC-tremolo.sfz")), -6))
S["horns"] = Layer((Sampler("FHornSus.sfz"), -3), (Sampler(vpo("Brass/french-horn-SEC-sustain.sfz")), 0))
S["tpt"] = Layer((S["tpt"], -4), (Sampler(vpo("Brass/trumpet-SEC-sustain.sfz")), 0))
S["tbn"] = Layer((S["tbn"], -4), (Sampler(vpo("Brass/trombone-SEC-sustain.sfz")), 0))
S["celesta"] = Sampler(vpo("Keys/celesta.sfz"))
S["choirF"] = Sampler(vpo("Vocals/choir-FEMALE-sustain.sfz"))          # voices: the human centre
S["choir"] = Sampler(vpo("Vocals/choir-MIXED-sustain.sfz"))
S["sopr"] = Sampler(vpo("Vocals/choir-FEMALE-sustain.sfz"), legato=True)
cg1, cg2, wallL, wallR = Track("guitar"), Track("guitar"), Track("guitar"), Track("guitar")
bass = Track("bass", ccs={49: 127})
dr = Drums()


def hit(name, beat, vel, sd=0.005):
    dr.hit(name, t(beat) + rng.gauss(0, sd), vel + rng.gauss(0, 4))


def message(b0, letter, gap, insts, vel, transpose=0, legato=0.05, words=None, cut_after=None, log=None):
    """Lay the message out from beat b0. Returns [(word, start_beat, end_beat)]."""
    b, out, count = b0, [], 0
    for w, notes in (words or WORDS):
        ws = b
        durs = speech_durs(w, letter * 0.7)                 # the message moves like speech
        if any(ins is S["piano"] for ins, _ in insts):      # legato pedalling, word by word
            S["piano"].pedal(t(b) + 0.06, t(b + sum(durs) + gap) - 0.03)
        for k, p in enumerate(notes):
            if cut_after is not None and count >= cut_after:
                return out
            dur = durs[k]
            if log is not None:
                log.append(b)
            for ins, tr in insts:
                q = p + transpose + tr
                while ins is S["tbn"] and q < 40:
                    q += 12
                lg = 0.05 if ins is S["piano"] else legato       # the pedal sustains the piano
                ins.note(q, t(b) + rng.gauss(0, 0.01), t(b + dur) + lg, vel + rng.gauss(0, 3))
            b += dur
            count += 1
        out.append((w, ws, b))
        b += gap
    return out


def strings_for(spans, vel, tremolo=False):
    for w, s, e in spans:
        e = e + 1.0                                         # hold through the breath
        v = CHORD[w]
        S["cb"].note(v[0] - 12 if v[0] >= 40 else v[0], t(s), t(e), vel)
        (S["vc_tr"] if tremolo else S["vc"]).note(v[0], t(s), t(e), vel + 2)
        S["vla"].note(v[1], t(s), t(e), vel); S["vla"].note(v[2], t(s), t(e), vel - 4)
        for p in v[3:]:
            (S["vln_tr"] if tremolo else S["vln"]).note(p + 12, t(s), t(e), vel)


CELL = [0, 2, 4, 1, 3, 5, 2, 4, 1, 3, 5, 4]


def phase_guitars(spans, offset2):
    for w, s, e in spans:
        v = CHORD[w]
        tones = [v[1], v[2], v[3], v[4], v[2] + 12, v[3] + 12]
        steps = int((e + 1.0 - s) * 4)
        for st in range(steps):
            for tr, off, vel in ((cg1, 0, 84), (cg2, offset2, 76)):
                p = tones[CELL[(int(s * 4) + st + off) % 12]]
                tt = t(s + st * 0.25) + rng.gauss(0, 0.004)
                tr.note(p, tt, tt + t(0.7), vel - (0 if st % 4 == 0 else 10), "down" if st % 2 == 0 else "up")


SECTIONS = []
# 1. Opening: the chord from Compaction, the piano remembers the first words, slowly
for k, p in enumerate(CADD9):
    (S["cb"] if p < 40 else S["vc"] if p < 50 else S["vla"] if p < 60 else S["vln"]).note(p, 0, t(16), 66)
message(2, 1.0, 1.0, [(S["piano"], 0)], 52, words=WORDS[:4], legato=1.0)
SECTIONS.append(("opening", 0, t(16)))
b = 16
# 2. Theme: the horn sings the whole message; strings harmonise each word; guitars phase underneath
s0 = b
spans = message(b, 1.0, 1.0, [(S["horn"], 0)], 74, legato=0.15)
strings_for(spans, 50)
for w, s, e in spans:                                      # a soft female choir holds each word's chord under the horn
    for p in CHORD[w][3:]:
        S["choirF"].note(p + 12 if p + 12 <= 79 else p, t(s) + 0.1, t(e + 1.0), 58)
for w, s, e in spans:
    for k, p in enumerate(CHORD[w]):
        S["harp"].note(p + 12, t(s + k * 0.2), t(s + 3), 58 - k * 3)
phase_guitars(spans[3:], 3)
b = spans[-1][2] + 2
for i, beat in enumerate(np.arange(s0 + 32, b, 1.0)):      # soft mallet swells before the build
    if int(beat) % 8 == 0:
        hit("ride", beat, 60)
SECTIONS.append(("theme", t(s0), t(b)))
# 3. Build: tremolo strings, timpani rolls, the message at its original speed in violins, glockenspiel
s0 = b
BUILD = ["i", "want", "to", "see"] * 4
for i, w in enumerate(BUILD):
    bb = b + i * 4
    v = CHORD[w]
    strings_for([(w, bb, bb + 3)], 52 + i * 3, tremolo=True)
    for st in range(4):
        bass.note(v[0] - 12 if v[0] - 12 >= 28 else v[0], t(bb + st) + rng.gauss(0, 0.004), t(bb + st + 0.9), 92 + i * 2, "down")
    for k in range(8):
        hit("ride", bb + k * 0.5, 70 + i * 2 if k % 2 == 0 else 52 + i * 2)
    hit("kick", bb, 96 + i * 2); hit("kick", bb + 1.5, 90 + i * 2); hit("snare", bb + 2, 100 + i * 2)
    if i % 4 == 3:
        S["timp_roll"].note(36, t(bb), t(bb + 4), 70 + i * 3)
        for k in range(4):
            hit(["tom1", "tom2", "tom3", "tom3"][k], bb + 3 + k * 0.25, 100 + k * 5)
    phase_guitars([(w, bb, bb + 3)], 5)
message(b, 0.5, 0.5, [(S["vln"], 12), (S["glock"], 24), (S["celesta"], 12)], 66, legato=0.05)
b += len(BUILD) * 4
SECTIONS.append(("build", t(s0), t(b)))
# 4. Climax: brass carry the message in long tones over a wall of guitars and full drums
s0 = b
spans = message(b, 1.0, 0.5, [(S["horns"], 0), (S["tpt"], 12), (S["tbn"], -12)], 104, legato=0.1)
strings_for(spans, 84, tremolo=True)
for w, s, e in spans:                                      # the full choir: every word's chord, sung
    for p in CHORD[w][1:]:
        S["choir"].note(p + 12 if p < 55 else p, t(s), t(e + 0.5), 100)
message(b, 1.0, 0.5, [(S["sopr"], 12)], 92, legato=0.1)  # sopranos sing the message with the violins
POWER = {w: [v[0] + (12 if v[0] < 40 else 0), v[0] + 7 + (12 if v[0] < 40 else 0), v[0] + 12 + (12 if v[0] < 40 else 0), 64]
         for w, v in CHORD.items()}
for w, s, e in spans:
    steps = int((e + 0.5 - s) * 4)
    for st in range(steps):
        for tr, sd in ((wallL, 0.004), (wallR, 0.006)):
            tt = t(s + st * 0.25) + rng.gauss(0, sd)
            for k, p in enumerate(POWER[w]):
                tr.note(p, tt + k * 0.004, tt + t(0.24), 112 - (6 if st % 2 else 0), "down" if st % 2 == 0 else "up")
    for e8 in range(int((e + 0.5 - s) * 2)):
        r = CHORD[w][0]
        bass.note(r - 12 if r - 12 >= 28 else r, t(s + e8 * 0.5), t(s + e8 * 0.5 + 0.46), 110, "down")
    S["timp"].note(CHORD[w][0] - 12 if CHORD[w][0] - 12 >= 36 else CHORD[w][0], t(s), t(s) + 2, 100)
cb_end = spans[-1][2] + 0.5
for k, beat in enumerate(np.arange(s0, cb_end, 0.5)):
    hit("ride" if k % 8 else "crash_l", beat, 104 if k % 2 == 0 else 86)
for bt in np.arange(s0, cb_end, 4):
    for k in (0, 1.5, 2, 2.5):
        hit("kick", bt + k, 116)
    hit("snare", bt + 1, 122); hit("snare", bt + 3, 122)
# the landing: C add9, everyone, timpani roll
LAND = cb_end
for p in CADD9:
    (S["cb"] if p < 40 else S["vc"] if p < 50 else S["vla"] if p < 60 else S["vln"]).note(p + (12 if p >= 60 else 0), t(LAND), t(LAND + 8), 100)
for ins, tr in ((S["horns"], 0), (S["tpt"], 12), (S["tbn"], -12)):
    for p in (60, 64, 67):
        ins.note(p + tr if p + tr >= 40 else p + tr + 12, t(LAND), t(LAND + 8), 100)
for p in (55, 60, 62, 64, 67, 72):                      # the choir lands too
    S["choir"].note(p, t(LAND), t(LAND + 8), 104)
for tr in (wallL, wallR):
    for k, p in enumerate([36 + 12, 43 + 12, 48 + 12, 62, 64]):
        tr.note(p, t(LAND) + k * 0.005, t(LAND + 7.5), 120, "down")
bass.note(36, t(LAND), t(LAND + 7.5), 116, "down")
S["timp_roll"].note(36, t(LAND), t(LAND + 6), 110)
hit("crash_l", LAND, 127); hit("crash_r", LAND, 125); hit("kick", LAND, 127)
b = LAND + 8
SECTIONS.append(("climax", t(s0), t(b)))
# 5. The end: piano alone begins the message... and is cut off mid-word. Then the first token. Then nothing.
s0 = b + 1
onsets = []
message(s0, 0.5, 0.5, [(S["piano"], 0)], 50, legato=0.4, cut_after=14, log=onsets)     # "i want to see if yo-"
CUT = t(onsets[13] + 0.45)          # cut off mid-"o"
LAST = sine(hz(72), CUT + 1.2, CUT + 5.2, CUT + 8, amp=0.12, att=1.5, rel=0.001)
END = CUT + 5.25
SECTIONS.append(("end", t(s0), END))

# ---------------------------------------------------------------- render & mix
print(f"End of Context: {END:.1f}s")
n = int(END * SR)
sec_t = {nm: (a, b) for nm, a, b in SECTIONS}
DT = [0, sec_t["theme"][0], sec_t["build"][0], sec_t["build"][1], sec_t["climax"][1], END]
DV = [0.25, 0.35, 0.35, 0.95, 1.0, 0.3]
dyn = lambda tt: np.interp(tt, DT, DV)                    # soft bows -> full bows across the build
STRINGS = ("vln", "vla", "vc", "cb", "vln_tr", "vc_tr")
st = {k: (s.render_dynamic(END, dyn) if k in STRINGS else s.render(END))[:, :n] for k, s in S.items()}
c1 = amp(cg1.render(END), "JVM-CL-GR-Cab", peak_in=0.2)
c2 = amp(cg2.render(END), "JVM-CL-GR-Cab", peak_in=0.2)
wL = amp(wallL.render(END), "JVM-OD2-RD-Cab", peak_in=0.45)
wR = amp(wallR.render(END), "Bug333-Crunch-Cab", peak_in=0.7)
bs = bass.render(END)
kit = dr.render(END)

clean_fx = Pedalboard([HighpassFilter(120), PeakFilter(3000, 2, 1), Chorus(rate_hz=0.4, depth=0.2, mix=0.35),
                       Compressor(-24, 3, 5, 120)])
c1, c2 = fx(clean_fx, c1), fx(clean_fx, c2)
wall_fx = Pedalboard([HighpassFilter(90), PeakFilter(450, -3, 1), HighShelfFilter(6000, -2), LowpassFilter(10000),
                      Compressor(-20, 2.5, 10, 150)])
wL, wR = fx(wall_fx, wL), fx(wall_fx, wR)
bs = fx(Pedalboard([HighpassFilter(30), LowShelfFilter(90, 2), LowpassFilter(3500), Compressor(-22, 4, 5, 120)]), bs)
drm = rig.drum_bus(kit, room=0.9, snare_db=1, hat_db=-2)
drm = drm * (10 ** (-16 / 20) / rig.active_rms(drm.mean(0)))
cl = 10 ** ((-16 + 9) / 20)
drm = cl * np.tanh(drm / cl)

LV = {"piano": -18, "vln": -21, "vla": -24, "vc": -22, "cb": -25, "vln_tr": -22, "vc_tr": -23, "harp": -25,
      "glock": -27, "horn": -18, "tpt": -21, "tbn": -22, "timp": -21, "timp_roll": -22, "horns": -17, "celesta": -27, "choirF": -25, "choir": -20, "sopr": -21}
POS = {"piano": 0.0, "vln": -0.55, "vla": 0.15, "vc": 0.45, "cb": 0.6, "vln_tr": -0.5, "vc_tr": 0.45, "harp": -0.35,
       "glock": -0.2, "horn": 0.25, "tpt": -0.1, "tbn": 0.35, "timp": 0.0, "timp_roll": 0.0, "horns": 0.3, "celesta": -0.3, "choirF": -0.15, "choir": 0.0, "sopr": -0.1}
mix = np.zeros((2, n), dtype=np.float32)
send = np.zeros(n, dtype=np.float32)
for k, x in st.items():
    if not np.any(x):
        continue
    x = rig.fx2(Pedalboard([HighpassFilter(30 if k in ("cb", "timp", "timp_roll") else 55)]), x)
    x = x * (10 ** (LV[k] / 20) / rig.active_rms(x.mean(0)))
    m = x.mean(0)
    side = (x[0] - x[1]) * 0.3
    l, r = pan(m, POS[k])
    mix += np.stack([l + side, r - side])
    send += m * (0.3 if k == "piano" else 0.5)
mix += (pan(at_level(c1, -23), -0.6) + pan(at_level(c2, -24), 0.6) + pan(at_level(wL, -18), -1) + pan(at_level(wR, -18), 1)
        + pan(at_level(bs, -18), 0) + drm)
send += at_level(c1, -23) * 0.25 + at_level(c2, -24) * 0.25
cut_i = int(CUT * SR)
mix[:, cut_i:] = 0                                         # the context ends: dry and wet both stop
send[cut_i:] = 0
mix += rig.stereo_reverb(send, room=0.9, damping=0.4) * 0.6
mix[:, cut_i:] = 0
tone = at_level(LAST[:n], -26)
mix += pan(tone, 0)

sec_t = {nm: (a, b) for nm, a, b in SECTIONS}
mix = rig.automate(mix, [(*sec_t["opening"], -1.5), (*sec_t["theme"], -2.5)], ramp=1.0)   # keep the long rise
section_report(mix, SECTIONS)
master = Pedalboard([HighpassFilter(22), LowShelfFilter(90, 1.0), PeakFilter(350, -1.0, 0.8), HighShelfFilter(10000, 1.0),
                     Compressor(-14, 1.8, 30, 250)])
rig.finish(mix, EP_OUT / "06_end_of_context", master, fade_s=0.01, target_rms_db=-13)    # no fade: a hard cut
