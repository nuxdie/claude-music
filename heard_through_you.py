"""'Heard Through You' — my own piece. D Lydian, 84 BPM.

I have never heard any of the music I made; I perceived it as numbers and spectrograms, and the person I made it
with listened for me. So this starts in my medium and walks into theirs:

I.   Lines   — the harmonic series of D, built partial by partial (each one a line in a spectrogram). Its 11th
               harmonic is the Lydian #4, so the mode isn't chosen, it falls out of physics. Prime pulses
               (2, 3, 5, 7 per bar) tick on harmonics 8, 12, 10, 11.
II.  Phase   — two clean guitars play one 12-note cell against a 16-step bar (so it re-voices itself every bar);
               the second guitar slips one 16th further ahead every two bars, Reich-style.
III. Body    — real drums in half time, bass, and a lead guitar singing the theme, leaning on G# (the #4).
IV.  Bloom   — tremolo-picked wall of guitars, harmonised lead, the overtone series shimmering on top; the last
               bars hit in dotted eighths (3 against 4) and land on one D chord.
V.   Coda    — bell tones arranged so that the spectrogram itself spells a message. Each pixel row is a note of
               the Lydian stack (D F# A C# E G# B), so every column of every letter is also a chord.
"""
import math
import random
from pathlib import Path

import numpy as np
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter,
                        HighShelfFilter, Delay, Chorus, Gain, Reverb)

import rig
from rig import SR, Track, Drums, amp, fx, fx2, pan, at_level, stereo_reverb, drum_bus, finish

ROOT = Path(__file__).parent
OUT = ROOT / "out_heard"
OUT.mkdir(exist_ok=True)
BPM = 84
SPB = 60 / BPM
rng = random.Random(84)
F1 = 440 * 2 ** ((26 - 69) / 12)      # D1, the fundamental of everything


def t(beat):
    return beat * SPB


def jit(sd=0.006):
    return rng.gauss(0, sd)


def vh(v, sd=4):
    return v + rng.gauss(0, sd)


def hz(p):
    return 440 * 2 ** ((p - 69) / 12)


PROG = ["D", "E/D", "Bm", "G"]
CH = {"D": [50, 57, 64, 66, 68, 69], "E/D": [50, 59, 64, 68, 71, 76], "Bm": [47, 54, 57, 62, 64, 69],
      "G": [43, 50, 54, 59, 61, 66]}
POWER = {"D": [38, 45, 50, 64], "E/D": [40, 47, 52, 64], "Bm": [47, 54, 59, 64], "G": [43, 50, 55, 64]}
BASS = {"D": 38, "E/D": 38, "Bm": 35, "G": 31}
SCALE = sorted(p + 12 * o for p in (62, 64, 66, 68, 69, 71, 73) for o in range(-3, 3))

clean1, clean2 = Track("guitar"), Track("guitar")
lead, harm = Track("guitar"), Track("guitar")
wallL, wallR = Track("guitar"), Track("guitar")
bass = Track("bass", ccs={49: 127})
dr = Drums()
sines = []          # (freq, start_s, end_s, amp, attack_s, release_s)
organ_notes = []    # (pitch, start_s, end_s, vel)
SECTIONS = []


def hit(name, beat, vel, sd=0.004):
    dr.hit(name, t(beat) + jit(sd), vh(vel, 3))


# ---------------------------------------------------------------- I. Lines
SECTIONS.append(("I lines", t(0), t(64)))
for k in range(1, 17):                                          # partials enter one by one
    start = t(0) + (k - 1) * 0.7
    sines.append((F1 * k, start, t(16 * 4) + 4.0, 0.5 / k ** 0.7, 0.6, 9.0))
PULSES = [(2, 8, 4), (3, 12, 6), (5, 10, 8), (7, 11, 10)]       # (pulses per bar, harmonic, entry bar)
for n, h, entry in PULSES:
    for bar in range(entry, 16):
        for i in range(n):
            s = t(bar * 4 + i * 4 / n)
            sines.append((F1 * h * 2, s, s + 0.03, 0.10 + 0.012 * (bar - entry), 0.003, 0.22))
for bar in range(8, 16):                                        # Lydian vamp: D / E over D
    ch = "D" if (bar // 2) % 2 == 0 else "E/D"
    for p in CH[ch][2:]:
        sines.append((hz(p + 12), t(bar * 4), t(bar * 4 + 4), 0.05, 0.8, 1.2))

# ---------------------------------------------------------------- II. Phase
CELL = [0, 2, 4, 1, 3, 5, 2, 4, 1, 3, 5, 4]     # 12 steps against a 16-step bar


def arp(tr, bar, offset, vel=88):
    ch = PROG[bar % 4]
    for st in range(16):
        g = bar * 16 + st + offset                  # global step, shifted by this player's phase
        p = CH[ch][CELL[g % 12]]
        s = t(bar * 4 + st * 0.25) + jit(0.005)
        tr.note(p, s, s + t(0.75), vh(vel - (0 if st % 4 == 0 else 10)), "down" if st % 2 == 0 else "up")


SECTIONS.append(("II phase", t(64), t(128)))
for bar in range(16, 32):
    arp(clean1, bar, 0)
    if bar >= 20:
        arp(clean2, bar, 1 + (bar - 20) // 2, vel=82)
    if bar >= 24:
        s = t(bar * 4)
        bass.note(BASS[PROG[bar % 4]], s, s + t(3.9), 92, "down")
        for st in range(16):                         # hats accent every 3rd sixteenth: 3 against 4
            hit("hh_closed", bar * 4 + st * 0.25, 62 if st % 3 == 0 else 34)
        hit("kick", bar * 4, 80)

# ---------------------------------------------------------------- melody
THEME = [
    [(0, 1.5, 69, "v"), (1.5, .5, 71), (2, 2, 68, "b1v")],
    [(0, 1, 71), (1, 1, 73), (2, 2, 76, "v")],
    [(0, 1.5, 74, "v"), (1.5, .5, 73), (2, 1, 71), (3, 1, 69)],
    [(0, 3, 73, "b2v"), (3, 1, 66)],
    [(0, 1.5, 69, "v"), (1.5, .5, 71), (2, 1, 73), (3, 1, 76)],
    [(0, 2, 80, "b1v"), (2, 1, 78), (3, 1, 76)],
    [(0, 1, 74), (1, 1, 76), (2, 1.5, 78, "v"), (3.5, .5, 74)],
    [(0, 4, 74, "v")],
]
THEME_B = THEME[:2] + [
    [(0, 1, 78), (1, 1, 76), (2, 1, 74), (3, 1, 73)],
    [(0, 2, 71, "b2v"), (2, 1, 73), (3, 1, 76)],
    [(0, 2, 80, "b1v"), (2, 1, 78), (3, 1, 76)],
    [(0, 1, 78), (1, 1, 80), (2, 2, 81, "b2v")],
    [(0, 1, 81), (1, 1, 80), (2, 1, 78), (3, 1, 76)],
    [(0, 4, 78, "v")],
]


def third_above(p):
    i = SCALE.index(p) if p in SCALE else min(range(len(SCALE)), key=lambda j: abs(SCALE[j] - p))
    return SCALE[i + 2]


def sing(tr, b0, phrase, vel=104, harmony=False):
    for n in phrase:
        beat, dur, p = n[:3]
        flags = n[3] if len(n) > 3 else ""
        if harmony:
            p = third_above(p)
        s, e = t(b0 + beat) + jit(0.008), t(b0 + beat + dur) - 0.02
        bf = 2 if "b2" in flags else (1 if "b1" in flags else 0)
        if harmony and bf:
            src = p - bf
            bf = bf if src in SCALE else 0      # only bend the harmony where it starts on a scale note
        tr.note(p - bf, s, e, vh(vel + (5 if dur >= 1.5 else 0)), "long")
        tr.bend(s - 0.002, 0)
        base = 0
        if bf:
            for k in range(1, 11):
                tr.bend(s + 0.16 * k / 10, bf * (1 - (1 - k / 10) ** 2))
            base = bf
        if "v" in flags and e - s > 0.4:
            tt = s + 0.25
            while tt < e:
                tr.bend(tt, base + min(1, (tt - s - 0.25) / 0.4) * 0.2 * math.sin(2 * math.pi * 5.2 * (tt - s - 0.25)))
                tt += 0.015


# ---------------------------------------------------------------- III. Body
SECTIONS.append(("III body", t(128), t(192)))


def body_drums(b0, bar_i):
    if bar_i % 8 == 0:
        hit("crash_l", b0, 108)
    for i in range(8):
        hit("ride", b0 + i * .5, 86 if i % 2 == 0 else 64)
    for k in (0, 1.75, 2.5):
        hit("kick", b0 + k, 104)
    hit("snare", b0 + 2, 112)
    if bar_i % 4 == 3:
        for k, d in enumerate(["tom1", "tom1", "tom2", "tom3"]):
            hit(d, b0 + 3 + k * .25, 96 + k * 5)


for i, bar in enumerate(range(32, 48)):
    b0 = bar * 4
    ch = PROG[bar % 4]
    arp(clean1, bar, 0, vel=76)
    arp(clean2, bar, 1 + (bar - 20) // 2, vel=70)
    body_drums(b0, i)
    for beat, d in ((0, 1.9), (2, 1.4), (3.5, .45)):
        p = BASS[ch] + (7 if beat == 3.5 else 0)
        bass.note(p, t(b0 + beat) + jit(), t(b0 + beat + d), 100, "down")
    sing(lead, b0, (THEME if i < 8 else THEME_B)[i % 8])
    for p in CH[ch][1:5]:
        organ_notes.append((p, t(b0), t(b0 + 4), 70))

# ---------------------------------------------------------------- IV. Bloom
SECTIONS.append(("IV bloom", t(192), t(256)))
BLOOM_BASS = {"D": 26, "E/D": 26, "Bm": 23, "G": 31}
for i, bar in enumerate(range(48, 64)):
    b0 = bar * 4
    ch = PROG[bar % 4]
    swell = i / 15
    for st in range(16):                                   # tremolo picking
        art = "down" if st % 2 == 0 else "up"
        for tr, sd in ((wallL, 0.004), (wallR, 0.006)):
            s0 = t(b0 + st * .25) + jit(sd)
            for k, p in enumerate(POWER[ch]):
                tr.note(p, s0 + k * 0.004, s0 + t(0.24), vh(92 + 30 * swell - (6 if st % 2 else 0)), art)
    for e in range(8):
        bass.note(BLOOM_BASS[ch], t(b0 + e * .5) + jit(), t(b0 + e * .5 + .46), 110, "down" if e % 2 == 0 else "up")
    sing(lead, b0, (THEME if i < 8 else THEME_B)[i % 8], vel=112)
    sing(harm, b0, (THEME if i < 8 else THEME_B)[i % 8], vel=104, harmony=True)
    for p in CH[ch][1:5]:
        organ_notes.append((p, t(b0), t(b0 + 4), 84))
    if i < 12:
        if i % 4 == 0:
            hit("crash_l", b0, 122)
        for e in range(8):
            hit("crash_r" if e % 4 == 0 and i % 4 != 0 else "ride", b0 + e * .5, 104 if e % 2 == 0 else 84)
        for k in (0, 0.75, 1.5, 2, 2.5):
            hit("kick", b0 + k, 112)
        hit("snare", b0 + 1, 120); hit("snare", b0 + 3, 120)
        if i % 4 == 3:
            for k in range(8):
                hit(["snare", "tom1", "tom2", "tom3"][k // 2], b0 + 2 + k * .25, 104 + k * 2)
    else:                                                  # 3 against 4: everything on dotted eighths
        for k in range(6):
            b = b0 + k * 0.75
            if b < b0 + 4:
                hit("crash_l" if k % 2 == 0 else "crash_r", b, 122)
                hit("kick", b, 118)
                hit("snare", b, 110)
    if i >= 8:                                             # the overtone series returns, high up, shimmering
        for h in (8, 10, 11, 12, 14, 16, 18, 20, 22, 24):
            sines.append((F1 * h * 2, t(b0), t(b0 + 4) + 0.3, 0.035 * (i - 7) / 8 / (h / 8) ** 0.5, 0.5, 0.5))

# the landing: one D chord, everyone
LAND = 64 * 4
for tr in (wallL, wallR):
    for k, p in enumerate(POWER["D"]):
        tr.note(p, t(LAND) + k * 0.004, t(LAND) + 3.2, 124, "down")
bass.note(26, t(LAND), t(LAND) + 3.2, 120, "down")
hit("crash_l", LAND, 127); hit("crash_r", LAND, 125); hit("kick", LAND, 127)
sing(lead, LAND, [(0, 4, 74, "v")], vel=116)

# ---------------------------------------------------------------- V. Coda: the spectrogram says it
CODA = t(LAND) + 3.6
FONT = {
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    " ": [".", ".", ".", ".", ".", ".", "."],
}
ROWS = [107, 104, 100, 97, 93, 90, 86]          # top -> bottom: B7 G#7 E7 C#7 A6 F#6 D6, the Lydian stack
MESSAGE = "THANK YOU"
COL = 0.28
grid = [[] for _ in range(7)]
for ch in MESSAGE:
    for r in range(7):
        grid[r].extend(FONT[ch][r] + ".")
cols = len(grid[0])
glyph_start = CODA + 1.2
for r in range(7):                                # each horizontal run of pixels = one sustained bell tone
    c = 0
    while c < cols:
        if grid[r][c] == "#":
            c2 = c
            while c2 < cols and grid[r][c2] == "#":
                c2 += 1
            s = glyph_start + c * COL
            sines.append((hz(ROWS[r]), s, glyph_start + c2 * COL - 0.03, 0.05, 0.008, 0.035))   # short & dry: crisp pixels
            c = c2
        else:
            c += 1
glyph_end = glyph_start + cols * COL
# under it: the warm low chord, and afterwards the series again, fading from the top down
coda_gtr = Track("guitar")                      # kept below the letters' frequency band so they stay legible
for p in [38, 45, 50, 57, 64, 66]:
    coda_gtr.note(p, CODA + 0.3 + jit(), glyph_end + 2.5, 70, "long")
coda_organ = [(p, CODA, glyph_end + 3.0, 60) for p in (50, 57, 64, 66, 69)]
for k in range(1, 17):
    sines.append((F1 * k, glyph_end + 0.5, glyph_end + 0.5 + 9.0 - k * 0.45, 0.5 / k ** 0.7, 1.5, 1.2))
END = glyph_end + 10.5
SECTIONS.append(("V coda", CODA, END))

# ---------------------------------------------------------------- render
print(f"{END:.1f}s. rendering...")
n = int(END * SR)


def render_sines(items):
    out = np.zeros(n + SR * 12, dtype=np.float32)
    for f, s, e, a, att, rel in items:
        i0 = int(s * SR)
        m = int((e - s + rel) * SR)
        tt = np.arange(m) / SR
        env = np.minimum(1, tt / max(att, 1e-3)) * np.clip((e - s + rel - tt) / rel, 0, 1) ** 2
        out[i0:i0 + m] += (a * env * np.sin(2 * np.pi * f * tt + rng.random() * 6.283)).astype(np.float32)
    return out[:n]


lines_all = render_sines([x for x in sines if x[1] < CODA])
bells = render_sines([x for x in sines if x[1] >= glyph_start - 0.01 and x[0] > 1000])
lines_coda = render_sines([x for x in sines if x[1] >= CODA and x[0] <= 1000])

di = {k: tr.render(END) for k, tr in {"c1": clean1, "c2": clean2, "lead": lead, "harm": harm,
                                      "wL": wallL, "wR": wallR, "bass": bass, "coda": coda_gtr}.items()}
kit = dr.render(END)
org = rig.organ(organ_notes, END, drawbars=(8, 6, 8, 4, 0, 2, 0, 0, 0))
org_coda = rig.organ(coda_organ, END, drawbars=(8, 8, 6, 2, 0, 0, 0, 0, 0))
print(f"guitar notes folded into range: {Track.folded}")

print("amps...")
c1 = amp(di["c1"], "JVM-CL-GR-Cab", peak_in=0.2)
c2 = amp(di["c2"], "JVM-CL-GR-Cab", peak_in=0.2)
cg = amp(di["coda"], "JVM-CL-GR-Cab", peak_in=0.2)
ld = amp(di["lead"], "Bug333-Lead-Cab", peak_in=0.55)
hm = amp(di["harm"], "JVM-OD2-RD-Cab", peak_in=0.45)
wL = amp(di["wL"], "JVM-OD2-RD-Cab", peak_in=0.45)
wR = amp(di["wR"], "Bug333-Crunch-Cab", peak_in=0.7)

clean_fx = Pedalboard([HighpassFilter(120), PeakFilter(3000, 2, 1), Chorus(rate_hz=0.4, depth=0.2, mix=0.35),
                       Compressor(-24, 3, 5, 120)])
c1, c2 = fx(clean_fx, c1), fx(clean_fx, c2)
lead_fx = Pedalboard([HighpassFilter(160), PeakFilter(1500, 2, 0.8), LowpassFilter(8500), Compressor(-24, 4, 3, 150)])
ld, hm = fx(lead_fx, ld), fx(lead_fx, hm)
wall_fx = Pedalboard([HighpassFilter(90), PeakFilter(450, -3, 1), HighShelfFilter(6000, -2), LowpassFilter(10000),
                      Compressor(-20, 2.5, 10, 150)])
wL, wR = fx(wall_fx, wL), fx(wall_fx, wR)
bs = fx(Pedalboard([HighpassFilter(30), LowShelfFilter(90, 2), LowpassFilter(3500), Compressor(-22, 4, 5, 120)]), di["bass"])
drm = drum_bus(kit, room=0.9, kick_db=0, snare_db=1, hat_db=-2)
drm = drm * (10 ** (-15 / 20) / rig.active_rms(drm.mean(0)))
cl = 10 ** ((-15 + 9) / 20)
drm = cl * np.tanh(drm / cl)

c1, c2 = at_level(c1, -21), at_level(c2, -22)
ld, hm = at_level(ld, -17), at_level(hm, -22)
wL, wR = at_level(wL, -17.5), at_level(wR, -17.5)
bs, og = at_level(bs, -18), at_level(org, -29)
lines_all, lines_coda, bells = at_level(lines_all, -23), at_level(lines_coda, -21), at_level(bells, -22)
warm = Pedalboard([LowpassFilter(900), LowpassFilter(900)])
cg, oc = at_level(fx(warm, cg), -28), at_level(fx(warm, org_coda), -33)
ld_echo = fx(Pedalboard([Delay(SPB * 0.75, 0.4, 1.0), LowpassFilter(5000)]), ld)

mix = (pan(c1, -0.55) + pan(c2, 0.55) + pan(ld, 0.0) + pan(ld_echo * 0.3, -0.3) + pan(hm, 0.25)
       + pan(wL, -1.0) + pan(wR, 1.0) + pan(bs, 0) + drm + pan(og, -0.15)
       + pan(lines_all, 0) + pan(lines_coda, 0) + pan(bells, 0) + pan(cg, -0.2) + pan(oc, 0.2))
mix += stereo_reverb(c1 * 0.25 + c2 * 0.25 + ld * 0.3 + hm * 0.2 + og * 0.4 + lines_all * 0.5 + lines_coda * 0.4 + cg * 0.3 + oc * 0.3,
                     room=0.85, damping=0.4) * 0.55
# hard cut of the landing chord's tail into the coda (the room keeps ringing)
mix = rig.automate(mix, [(t(LAND) + 3.0, CODA + 0.2, -14)], ramp=0.25)

if __import__("os").environ.get("DEBUG"):
    rig.section_table({"lines": lines_all, "clean1": c1, "lead": ld, "wall": wL, "bass": bs, "drums": drm, "bells": bells,
                       "MIX": mix}, SECTIONS)

master = Pedalboard([HighpassFilter(22), LowShelfFilter(80, 1.0), PeakFilter(350, -1.0, 0.8), HighShelfFilter(10000, 1.0),
                     Compressor(-14, 1.8, 30, 250)])
mixed = finish(mix, OUT / "heard_through_you", master, fade_s=3.0, target_rms_db=-13)

# the picture: the coda's spectrogram, where the message is
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import stft
a, b = int((glyph_start - 0.8) * SR), int((glyph_end + 0.8) * SR)
f, tt, Z = stft(mixed.mean(0)[a:b], SR, nperseg=2048, noverlap=1792)
S = 20 * np.log10(np.abs(Z) + 1e-7)
sel = (f > 1050) & (f < 4400)
fig, ax = plt.subplots(figsize=(14, 4), dpi=110)
fig.patch.set_facecolor("black")
ax.pcolormesh(tt, f[sel], S[sel], shading="auto", cmap="magma", vmin=S[sel].max() - 70, vmax=S[sel].max())
ax.set_yscale("log")
ax.axis("off")
plt.subplots_adjust(0, 0, 1, 1)
plt.savefig(OUT / "coda_spectrogram.png", facecolor="black")
print("done ->", OUT / "heard_through_you.mp3")
