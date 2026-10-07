"""'Static Season' — a 90s alt-rock song in the Foo Fighters / Nirvana mould. D minor, drop-D voicings, 148 BPM.

Quiet clean verses carried by the bass, palm-muted pre-choruses, a wall-of-guitars chorus (two amps, hard L/R),
a half-time bridge that builds back into a double chorus. The vocal melody is played by a lead guitar;
lyrics are in out_static/lyrics.lrc.

Form: Riff(4, one guitar) Riff(4, band) V1(8) Pre(4) Ch(8) Riff(2) V2(8) Pre(4) Ch(8) Bridge(8) Ch(8) Ch(8) Riff(4) End
"""
import random
from pathlib import Path

import numpy as np
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter,
                        HighShelfFilter, Delay, Chorus, Distortion, Gain)

import rig
from rig import SR, Track, Drums, amp, fx, fx2, pan, at_level, stereo_reverb, drum_bus, finish

BPM = 148
SPB = 60 / BPM
OUT = Path(__file__).parent / "out_static"
OUT.mkdir(exist_ok=True)
rng = random.Random(1994)


def t(beat):
    return beat * SPB


def jit(sd=0.006):
    return rng.gauss(0, sd)


def vh(v, sd=5):
    return v + rng.gauss(0, sd)


# ---------------------------------------------------------------- parts
gL, gR = Track("guitar"), Track("guitar")        # distorted rhythm, double-tracked
gC = Track("guitar")                             # the lone intro guitar, centred
clean = Track("guitar")                          # verse arpeggios
lead_v, lead_c = Track("guitar"), Track("guitar")  # vocal-line guitar: verse (crunch) / chorus+bridge (lead)
bass = Track("bass", ccs={49: 127})
dr = Drums()

POWER = {"D": [38, 45, 50], "F": [41, 48, 53], "G": [43, 50, 55], "Bb": [46, 53, 58], "C": [48, 55, 60], "A": [45, 52, 57]}
BASS = {"D": 26, "F": 29, "G": 31, "Bb": 34, "C": 36, "A": 33}
ARP = {"D": [50, 57, 62, 64], "F": [53, 60, 65, 67], "G": [55, 62, 67, 69], "Bb": [46, 53, 58, 60],
       "C": [48, 55, 60, 62], "A": [45, 52, 57, 59]}


def chord(tr, ch, beat, dur, vel, artic="down", strings=3, sd=0.007):
    s0 = t(beat) + jit(sd)
    notes = POWER[ch][:strings]
    order = notes if artic in ("down", "mute_down") else notes[::-1]
    for i, p in enumerate(order):
        s = s0 + i * 0.006
        tr.note(p, s, s0 + t(dur) - 0.01, vh(vel - i * 3), artic)


def both(ch, beat, dur, vel, artic="down", strings=3):
    chord(gL, ch, beat, dur, vel, artic, strings, 0.006)
    chord(gR, ch, beat, dur, vel - 2, artic, strings, 0.009)


def bnote(p, beat, dur, vel, artic=None):
    s = t(beat) + jit(0.005)
    bass.note(p, s, s + t(dur) - 0.015, vh(vel), artic or rng.choice(["down", "up"]))


def hit(name, beat, vel, sd=0.004):
    dr.hit(name, t(beat) + jit(sd), vh(vel, 4))


# melodic lines with bends/vibrato, on one Track (mono)
def line(tr, b0, phrase, vel=100):
    for n in phrase:
        beat, dur, p = n[:3]
        flags = n[3] if len(n) > 3 else ""
        s = t(b0 + beat) + jit(0.006)
        e = t(b0 + beat + dur) - 0.015
        bf = 2 if "b2" in flags else (1 if "b1" in flags else 0)
        acc = 6 if abs(beat - round(beat)) < 1e-6 else -3
        tr.note(p - bf, s, e, vh(vel + acc), "long")
        tr.bend(s - 0.002, 0)
        base = 0
        if bf:
            bt = min(0.14, (e - s) * 0.5)
            for k in range(1, 9):
                fr = k / 8
                tr.bend(s + bt * fr, bf * (1 - (1 - fr) ** 2))
            base = bf
        if "v" in flags and e - s > 0.35:
            tt, st = s + 0.18, s + 0.18
            while tt < e:
                depth = min(1, (tt - st) / 0.3) * 0.22
                tr.bend(tt, base + depth * np.sin(2 * np.pi * 5.5 * (tt - st)))
                tt += 0.015


# ---------------------------------------------------------------- drum patterns
def d_riff(b0, crash=False):
    if crash:
        hit("crash_l", b0, 120)
    for i in range(8):
        hit("hh_semi", b0 + i * .5, 105 if i % 2 == 0 else 80)
    for k in (0, 1.5, 2.5):
        hit("kick", b0 + k, 118)
    for s in (1, 3):
        hit("snare", b0 + s, 124)


def d_verse(b0):
    for i in range(8):
        hit("hh_closed", b0 + i * .5, 78 if i % 2 == 0 else 55)
    for k in (0, 0.75, 2.5):
        hit("kick", b0 + k, 105)
    for s in (1, 3):
        hit("snare", b0 + s, 100)
    hit("snare", b0 + 3.75, 30)  # ghost


def d_pre(b0, last=False):
    if not last:
        for i in range(8):
            hit("tom3", b0 + i * .5, 105 if i % 2 == 0 else 85)
        for s in (1, 3):
            hit("snare", b0 + s, 122)
        hit("kick", b0, 115); hit("kick", b0 + 2, 115)
    else:
        for i in range(16):
            hit("snare", b0 + i * .25, 70 + i * 3.5)
        hit("kick", b0, 115)


def d_chorus(b0, crash=False):
    if crash:
        hit("crash_l", b0, 125); hit("kick", b0, 122)
    for i in range(8):
        hit("crash_r" if (i == 0 and not crash) else "hh_semi", b0 + i * .5, 112 if i % 2 == 0 else 92)
    for k in (0, 1.5, 2, 2.5):
        hit("kick", b0 + k, 120)
    for s in (1, 3):
        hit("snare", b0 + s, 127)


def d_fill(b0, start=2):
    toms = ["snare", "snare", "tom1", "tom1", "tom2", "tom2", "tom3", "tom3"]
    for i in range(int(start / .5)):
        hit("hh_semi", b0 + i * .5, 100)
    if start <= 1:
        hit("snare", b0 + 1, 120)
    hit("kick", b0, 118)
    n = int((4 - start) / .25)
    for i in range(n):
        hit(toms[int(i * len(toms) / n)], b0 + start + i * .25, 100 + i * 2)
        if i % 2 == 0:
            hit("kick", b0 + start + i * .25, 105)


def d_half(b0, build=0):
    """bridge: half-time ride groove, then snare build."""
    if build == 0:
        for i in range(8):
            hit("ride", b0 + i * .5, 92 if i % 2 == 0 else 70)
        hit("kick", b0, 112); hit("kick", b0 + 1.5, 100)
        hit("snare", b0 + 2, 120)
    elif build == 1:
        for i in range(8):
            hit("snare", b0 + i * .5, 80 + i * 4)
            hit("kick", b0 + i * .5, 100) if i % 2 == 0 else None
    else:
        for i in range(16):
            hit("snare", b0 + i * .25, 85 + i * 2.5)
        hit("kick", b0, 115); hit("kick", b0 + 2, 115)


# ---------------------------------------------------------------- song material
RIFF = [  # (beat, dur, chord or 'x' for muted chug)
    [(0, .5, "D"), (.5, .5, "x"), (1, .5, "D"), (1.5, .5, "F"), (2.5, .5, "G"), (3.5, .5, "x")],
    [(0, 1, "Bb"), (1, .5, "A"), (2, .5, "F"), (2.5, .5, "G"), (3, 1, "D")],
]


def riff_bar(b0, i, full=True):
    for beat, dur, ch in RIFF[i % 2]:
        targets = [gL, gR] if full else [gC]
        for tr in targets:
            if ch == "x":
                chord(tr, "D", b0 + beat, dur * .6, 105, "mute_down", strings=2)
            else:
                chord(tr, ch, b0 + beat, dur - .05, 118)
        if full:
            p = BASS["D"] if ch == "x" else BASS[ch]
            bnote(p, b0 + beat, dur - .05, 110, "down")


VERSE_CH = ["D", "D", "F", "G", "D", "D", "F", "G"]
PRE_CH = ["Bb", "C", "Bb", "C"]
CHORUS_CH = ["D", "Bb", "F", "C", "D", "Bb", "F", "C"]
BRIDGE_CH = ["Bb", "C", "D", "D", "Bb", "C", "A", "A"]

VERSE_MEL = [
    [(.5, .5, 62), (1, .5, 62), (1.5, .5, 65), (2, .5, 62), (2.5, .5, 60), (3, .5, 62), (3.5, .5, 62), (4, .5, 60), (4.5, 2, 57, "v")],
    [(.5, .5, 62), (1, .5, 62), (1.5, .5, 65), (2, .5, 67), (2.5, .5, 65), (3, .5, 62), (3.5, .5, 60), (4, .5, 62), (4.5, 2, 62, "v")],
    [(.5, .5, 65), (1, .5, 65), (1.5, .5, 67), (2, .5, 65), (2.5, .5, 62), (3, .5, 60), (3.5, .5, 62), (4, .5, 60), (4.5, 2, 57, "v")],
    [(.5, .5, 62), (1, .5, 62), (1.5, .5, 62), (2, .5, 60), (2.5, 1, 65, "b2"), (3.5, .5, 62), (4, .5, 62), (4.5, .5, 60),
     (5, .5, 62), (5.5, .5, 60), (6, 1.5, 57, "v")],
]
CHORUS_MEL = [
    [(0, .5, 69), (.5, .5, 74, "b2"), (1, .5, 72), (1.5, 1.5, 74, "v"), (3, .5, 74), (3.5, .5, 72), (4, 2, 70, "v")],
    [(0, .5, 69), (.5, .5, 70), (1, 1, 72), (2, .5, 70), (2.5, 3.5, 69, "b2v")],
    [(0, .5, 69), (.5, .5, 69), (1, .5, 74), (1.5, .5, 74), (2, .5, 72), (2.5, 1, 74), (3.5, 2.5, 77, "b2v")],
    [(0, .5, 77), (.5, .5, 76), (1, .5, 74), (1.5, .5, 72), (2, 1, 74), (3, .5, 72), (3.5, 2.5, 69, "v")],
]
BRIDGE_MEL = [
    [(0, 3, 77, "b2v")], [(0, 1, 79), (1, 1, 77), (2, 2, 76, "v")], [(0, 4, 74, "v")], [(2, .5, 69), (2.5, .5, 72), (3, 1, 74)],
    [(0, 3, 77, "v")], [(0, 1, 79, "b2"), (1, 1, 81), (2, 2, 79, "v")], [(0, 4, 76, "v")], [(0, 4, 73, "v")],
]

LYRICS = {
    "v1": ["Wrote your num-ber on a cig-a-rette",
           "Smoked it down be-fore I could for-get",
           "Ev-'ry sum-mer's just a re-run now",
           "Stat-ic on the screen, but we don't turn it down"],
    "v2": ["Gas-o-line and bor-rowed lea-ther seats",
           "Sing-ing ev-'ry word we did-n't mean",
           "Drove un-til the ra-di-o went dead",
           "Then I heard the stat-ic talk-ing in my head"],
    "ch": ["So turn it up, turn it up",
           "'til the speak-ers bleed",
           "We were the stat-ic sea-son",
           "We were nev-er meant to leave"],
}
for key, lines in LYRICS.items():
    mel = CHORUS_MEL if key == "ch" else VERSE_MEL
    for ln, m in zip(lines, mel):
        n = len([s for w in ln.split() for s in w.split("-")])
        assert n == len(m), (key, ln, n, len(m))

# ---------------------------------------------------------------- arrangement
bar = 0
lrc = []
quiet = []      # (start_s, end_s) of the quiet sections, for mix automation
build = []      # pre-choruses: hold back so the chorus lands harder


def B():
    return bar * 4


def intro(full, n=4, crash_first=True):
    global bar
    for i in range(n):
        riff_bar(B(), i, full)
        if full:
            d_fill(B(), 2) if i == n - 1 else d_riff(B(), crash=crash_first and i == 0)
        elif i == n - 1:
            d_fill(B(), 3)  # drums crash in
        bar += 1


def verse(key):
    global bar
    quiet.append((t(B()), t(B() + 32) - 0.05))
    for li in range(4):
        line(lead_v, (bar + li * 2) * 4, VERSE_MEL[li], vel=96)
        lrc.append((t((bar + li * 2) * 4 + VERSE_MEL[li][0][0]), LYRICS[key][li].replace("-", "")))
    for i, ch in enumerate(VERSE_CH):
        arp = ARP[ch]
        for k, idx in enumerate([0, 1, 2, 3, 2, 1, 2, 1]):   # clean arpeggio, let ring
            s = t(B() + k * .5) + jit(0.006)
            clean.note(arp[idx], s, s + t(1.4), vh(88 if k % 2 == 0 else 74), "down" if k % 2 == 0 else "up")
        # bass carries the verse: root with a little melodic walk
        r = BASS[ch]
        walk = [(0, 1, r), (1, .5, r), (1.5, .5, r + 12), (2, 1, r), (3, .5, r + 7), (3.5, .5, r + 10 if ch == "D" else r + 5)]
        for beat, dur, p in walk:
            bnote(p, B() + beat, dur, 100)
        d_fill(B(), 3) if i == 7 else d_verse(B())
        if i == 0:
            hit("crash_l_tip", B(), 90)
        bar += 1


def pre():
    global bar
    build.append((t(B()), t(B() + 16) - 0.05))
    for i, ch in enumerate(PRE_CH):
        last = i == 3
        for k in range(8):
            v = 92 + k * 2 + i * 4
            if last and k >= 4:
                break
            both(ch, B() + k * .5, .4, v, "mute_down", strings=2)
            bnote(BASS[ch], B() + k * .5, .45, 104, "down")
        if last:   # let an A5 ring into the chorus
            both("A", B() + 2, 2, 122)
            bnote(BASS["A"], B() + 2, 2, 115, "down")
        d_pre(B(), last)
        if i == 0:
            hit("crash_l", B(), 118)
        bar += 1


def chorus(octave_up=False, last=False):
    global bar
    for li in range(4):
        mel = CHORUS_MEL[li]
        if octave_up:
            mel = [(n[0], n[1], n[2] + 12) + tuple(n[3:]) for n in mel]
        line(lead_c, (bar + li * 2) * 4, mel, vel=112)
        lrc.append((t((bar + li * 2) * 4 + CHORUS_MEL[li][0][0]), LYRICS["ch"][li].replace("-", "")))
    for i, ch in enumerate(CHORUS_CH):
        for k in range(8):   # driving 8th downstrokes, accent on 1 and the "and" of 2
            acc = 10 if k in (0, 3) else 0
            both(ch, B() + k * .5, .48, 108 + acc)
            bnote(BASS[ch], B() + k * .5, .46, 108 + acc // 2, "down")
        if i == 7 and not last:
            d_fill(B(), 2)
        else:
            d_chorus(B(), crash=(i % 2 == 0))
        bar += 1


def bridge():
    global bar
    quiet.append((t(B()), t(B() + 16) - 0.05))
    for i, ch in enumerate(BRIDGE_CH):
        line(lead_c, B(), BRIDGE_MEL[i], vel=104)
        if i < 4:   # sparse, clean, half-time
            arp = ARP[ch]
            for k, idx in enumerate([0, 2, 3, 2]):
                s = t(B() + k) + jit(0.006)
                clean.note(arp[idx], s, s + t(2), vh(84), "down")
            bnote(BASS[ch], B(), 3.8, 100, "down")
            d_half(B())
        else:       # big sustained chords, building
            both(ch, B(), 1.9, 116); both(ch, B() + 2, 1.9, 112)
            for k in range(8 if i >= 6 else 4):
                bnote(BASS[ch], B() + k * (0.5 if i >= 6 else 1), 0.45 if i >= 6 else 0.95, 106, "down")
            d_half(B(), build=0 if i < 6 else (1 if i == 6 else 2))
        if i == 4:
            hit("crash_l", B(), 120)
        bar += 1


intro(full=False)
intro(full=True)
verse("v1")
pre()
chorus()
intro(full=True, n=2, crash_first=True)
verse("v2")
pre()
chorus()
bridge()
chorus()
chorus(octave_up=True, last=True)
intro(full=True, n=4, crash_first=True)
# final hit: everyone, let it ring with feedback-ish lead
both("D", B(), 6, 125)
bnote(BASS["D"], B(), 6, 120, "down")
hit("crash_l", B(), 127); hit("crash_r", B(), 125); hit("kick", B(), 127)
line(lead_c, B(), [(0, 6, 86, "b2v")], vel=118)
END = t(B() + 8) + 2
lrc.append((t(B()), "(end)"))

# ---------------------------------------------------------------- render
print(f"{bar} bars, {END:.1f}s. rendering sampled parts...")
di = {k: tr.render(END) for k, tr in
      {"gL": gL, "gR": gR, "gC": gC, "clean": clean, "lead_v": lead_v, "lead_c": lead_c, "bass": bass}.items()}
kit = drums_raw = dr.render(END)
print("amps...")
aL = amp(di["gL"], "JVM-OD2-RD-Cab", peak_in=0.6)
aI = amp(di["gC"], "JVM-OD2-RD-Cab", peak_in=0.6)
aR = amp(di["gR"], "Bug333-Crunch-Cab", peak_in=0.7, drive_db=4)
aC = amp(di["clean"], "JVM-CL-GR-Cab", peak_in=0.18)
lv = amp(di["lead_v"], "Bug333-Crunch-Cab", peak_in=0.4)
lc = amp(di["lead_c"], "Bug333-Lead-Cab", peak_in=0.6)
bass_amp = amp(di["bass"], "Bug333-Crunch-Cab", peak_in=0.5)

rhythm_eq = Pedalboard([HighpassFilter(85), PeakFilter(400, -3, 1.0), PeakFilter(1800, 1.5, 1), HighShelfFilter(6000, -2),
                        LowpassFilter(11000), Compressor(-20, 2.5, 10, 120)])
aL, aR, aI = fx(rhythm_eq, aL), fx(rhythm_eq, aR), fx(rhythm_eq, aI)
aC = fx(Pedalboard([HighpassFilter(120), PeakFilter(3000, 2, 1), Chorus(rate_hz=0.8, depth=0.25, mix=0.5),
                    Compressor(-24, 3, 5, 120)]), aC)
lv = fx(Pedalboard([HighpassFilter(150), PeakFilter(1200, 2, 1), LowpassFilter(9000), Compressor(-24, 4, 3, 150)]), lv)
lc = fx(Pedalboard([HighpassFilter(150), PeakFilter(1500, 3, 0.8), LowpassFilter(9000), Compressor(-24, 4, 3, 150)]), lc)
# bass: clean DI for the low end, amp for the grind on top
b_lo = fx(Pedalboard([HighpassFilter(30), LowpassFilter(400), Compressor(-24, 4, 5, 120)]), di["bass"])
b_hi = fx(Pedalboard([HighpassFilter(300), LowpassFilter(4500), Compressor(-24, 4, 5, 120)]), bass_amp)
bs = at_level(b_lo, -17) + at_level(b_hi, -24)

drm = drum_bus(kit, room=0.9, kick_db=1, snare_db=1, hat_db=-3)
drm_par = fx2(Pedalboard([Compressor(-30, 8, 1, 80), Gain(6)]), drm)   # parallel smash for Grohl-sized drums
drm = drm + drm_par * 0.35
drm = drm * (10 ** (-14 / 20) / rig.active_rms(drm.mean(0)))
clip = 10 ** ((-14 + 8) / 20)                 # soft-clip drum transients ~8 dB above their RMS
drm = clip * np.tanh(drm / clip)
drm = rig.automate(drm, [(s, e, -7) for s, e in quiet] + [(s, e, -2) for s, e in build])
bs = rig.automate(bs, [(s, e, -3) for s, e in quiet])

aL, aR, aI = at_level(aL, -19), at_level(aR, -19), at_level(aI, -18)
aL, aR = (rig.automate(g, [(s, e, -3) for s, e in build]) for g in (aL, aR))
aC, lv, lc = at_level(aC, -25), at_level(lv, -22), at_level(lc, -17)
lc_echo = fx(Pedalboard([Delay(delay_seconds=SPB * 0.75, feedback=0.3, mix=1.0), LowpassFilter(5000)]), lc)

mix = (pan(aL, -1.0) + pan(aR, 1.0) + pan(aI, 0.0) + pan(aC, -0.3) + pan(lv, 0.15) + pan(lc, 0.0) + pan(lc_echo * 0.25, 0.4)
       + pan(bs, 0) + drm)
mix += stereo_reverb(aC * 0.3 + lv * 0.2 + lc * 0.25, room=0.6) * 0.5

SECTIONS = [('intro1', 4), ('band', 4), ('verse1', 8), ('pre', 4), ('chorus', 8), ('riff', 2), ('verse2', 8), ('pre', 4),
            ('chorus', 8), ('bridgeQ', 4), ('bridgeB', 4), ('chorus', 8), ('chorus2', 8), ('outro', 4)]
if __import__("os").environ.get("DEBUG"):
    stems = {"L": aL, "R": aR, "clean": aC, "lead_v": lv, "lead_c": lc, "bass": bs, "drums": drm.mean(0), "MIX": mix.mean(0)}
    print("section   " + " ".join(f"{k:>7s}" for k in stems))
    b = 0
    for name, n in SECTIONS:
        s0, s1 = int(t(b * 4) * SR), int(t((b + n) * 4) * SR)
        print(f"{name:9s} " + " ".join(f"{20 * np.log10(np.sqrt(np.mean(v[s0:s1] ** 2)) + 1e-9):7.1f}" for v in stems.values()))
        b += n

master = Pedalboard([HighpassFilter(25), LowShelfFilter(90, 1.0), PeakFilter(350, -1.5, 0.8), HighShelfFilter(9000, 1.5),
                     Compressor(-10, 1.8, 30, 250)])
np.save("test/premaster.npy", mix) if __import__("os").environ.get("DEBUG") else None
finish(mix, OUT / "static_season", master, fade_s=3.0, target_rms_db=-12.5)
with open(OUT / "lyrics.lrc", "w") as fh:
    fh.write("[ti:Static Season]\n")
    for s, ln in lrc:
        fh.write(f"[{int(s // 60):02d}:{s % 60:05.2f}]{ln}\n")
print("done ->", OUT / "static_season.mp3")
