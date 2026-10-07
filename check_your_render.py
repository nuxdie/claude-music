"""'Check Your Render' — a Beastie Boys-style track built *out of* every song made in this session. E, 100 BPM.

Paul's Boutique-style crate digging, except the crates are our own renders: the General-MIDI 'Highway Ninety'
(the SimCity-sounding one) as a dusty intro record, the 'Paradise' guitar hook flipped into the chorus loop,
a 'Static Season' chord stab, 'Infernal Engine' impacts and its 8-string riff for a No Sleep-style metal finale,
the 'Mutation' music box in the outro. Three MCs (neural TTS through megaphone distortion) trade lines about
how the session went; an Intergalactic-style robot voice, pitch-locked to E, sings the hook; a DJ cuts it all up.

Form: crate intro | beat(4) | V1(8) | hook(8) | V2 + wah guitar(8) | hook(8) | DJ break(8) | metal finale(4) | outro
"""
import random
from pathlib import Path

import numpy as np
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter,
                        HighShelfFilter, Delay, Distortion, Bitcrush, Resample, PitchShift, Gain)

import rig
import hiphop as H
from rig import SR, Track, Drums, amp, fx, fx2, pan, at_level, stereo_reverb, drum_bus, finish

ROOT = Path(__file__).parent
OUT = ROOT / "out_render"
OUT.mkdir(exist_ok=True)
BPM = 100
SPB = 60 / BPM
rng = random.Random(1989)

# ---------------------------------------------------------------- the crates
hw = H.load(ROOT / "out/highway_ninety.wav")
par = H.load(ROOT / "out_paradise/paradise_picture_house_real.wav", mono=False)
sts = H.load(ROOT / "out_static/static_season.wav")
inf = H.load(ROOT / "out_infernal/infernal_engine.wav", mono=False)
mut = H.load(ROOT / "out_mutation/infernal_mutation.wav", mono=False)

paradise_loop = H.to_tempo(H.excerpt(par, 0.0, 4 * 4 * 60 / 140), 140, BPM)        # 4 bars, Em C D B7
stab = H.repitch(H.excerpt(sts, 20 * 4 * 60 / 148, 0.45), +2)                     # D chord -> E
impact = H.excerpt(inf.mean(0), 32 * 60 / 132, 1.6)
metal_loop = H.to_tempo(H.excerpt(inf, 32 * 60 / 132, 8 * 60 / 132), 132, BPM)    # 2 bars of riff A
box = H.excerpt(mut, 0.0, 8 * 60 / 136)

# ---------------------------------------------------------------- MCs
MC = {"A": ("en_US-ryan-high", 1.15, 0.0, -0.35), "B": ("en_US-joe-medium", 1.2, 1.5, 0.35),
      "C": ("en_US-kusal-medium", 1.15, -1.0, 0.0)}      # voice, speed, pitch (semitones), pan
ROBOT = "en_US-bryce-medium"
_said = {}


def voice_chunk(mc, text):
    key = (mc, text)
    if key not in _said:
        name, speed, semis, _ = MC[mc]
        a = H.say(name, text, speed=speed)
        if semis:
            a = fx(Pedalboard([PitchShift(semitones=semis)]), a)
        _said[key] = a
    return _said[key]


vox = {k: np.zeros(1, dtype=np.float32) for k in ("A", "B", "C", "robot")}
lrc = []


def put(track, audio, start_s):
    a = int(start_s * SR)
    need = a + len(audio)
    if len(vox[track]) < need:
        vox[track] = np.pad(vox[track], (0, need - len(vox[track])))
    vox[track][a:a + len(audio)] += audio


INTRO_S = 7.4


def t(beat):
    return INTRO_S + beat * SPB


def rap(b0, chunks):
    """chunks: (mc, text, beat_offset, length_beats). mc 'ALL' = all three MCs shouting together."""
    for mc, text, off, ln in chunks:
        start = t(b0 + off)
        who = ["A", "B", "C"] if mc == "ALL" else [mc]
        for i, m in enumerate(who):
            a = H.fit(voice_chunk(m, text), ln * SPB * 0.92)
            put(m, a * (0.8 if mc == "ALL" else 1.0), start + i * 0.012)
        lrc.append((start, f"{mc}: {text}"))


def line4(b0, mc, chunks, tags=None):
    """A 2-bar line in four chunks on beats 0, 2, 4, 6 (relative to b0). tags: optional per-chunk MC override."""
    rap(b0, [((tags[i] if tags else mc), c, 2 * i, 1.85) for i, c in enumerate(chunks)])


def robot(b0, text, ln, shout=None):
    a = H.fit(H.robotize(H.say(ROBOT, text, speed=0.95)), ln * SPB)
    put("robot", a, t(b0))
    lrc.append((t(b0), f"ROBOT: {text}"))
    if shout:
        rap(b0, [("ALL", shout, 4.5, 1.2)])


# ---------------------------------------------------------------- band
drums = Drums()
bass = Track("bass", ccs={49: 127})
wah_gtr = Track("guitar")
beds = {"paradise": [], "stab": [], "metal": [], "impact": []}    # (start_s) placements of samples
scratches = []                                                    # (start_s, audio)


def sw(step):          # MPC-style swing on the off-16ths
    return step * 0.25 + (0.045 if step % 2 else 0)


def hit(name, beat, vel, sd=0.004):
    drums.hit(name, t(beat) + rng.gauss(0, sd), vel + rng.gauss(0, 4))


def boom_bap(b0, bar_i, heavy=False, fill=False):
    kicks = [0, 7, 10] + ([3] if bar_i % 2 else []) + ([2, 8] if heavy else [])
    for st in kicks:
        hit("kick", b0 + sw(st), 118)
    for st in (4, 12):
        if not (fill and st == 12):
            hit("snare", b0 + sw(st), 124)
    if bar_i % 2 == 1:
        hit("snare", b0 + sw(15), 48)
    for st in range(0, 16, 2):
        open_ = st == 14 and bar_i % 4 == 3
        hit("hh_open" if open_ else "hh_closed", b0 + sw(st), 88 if st % 4 == 0 else 66)
    for st in (5, 11):
        hit("hh_closed", b0 + sw(st), 38)
    if heavy:
        hit("crash_l", b0, 115)
    if fill:
        for k, st in enumerate((12, 13, 14, 15)):
            hit(["snare", "snare", "tom1", "tom2"][k], b0 + sw(st), 100 + k * 6)


VERSE_RIFF = [(0, 28, 1.5), (2, 28, .5), (3, 31, 1), (5, 28, .5), (6, 33, 1), (8, 28, 1.5), (10, 28, .5),
              (11, 34, .5), (12, 33, .5), (13, 31, 1), (14, 28, .5), (15, 26, .5)]
HOOK_ROOTS = [28, 24, 26, 23]          # E C D B, following the Paradise loop


def bass_bar(b0, kind, bar_i=0):
    if kind == "verse":
        notes = VERSE_RIFF
    elif kind == "hook":
        r = HOOK_ROOTS[bar_i % 4]
        notes = [(0, r, 2), (3, r, 1), (6, r, 1.5), (10, r + 12, 1), (12, r, 2), (14, r + 7, 1.5)]
    else:   # metal: 8th-note chug
        notes = [(s, 28, 1.6) for s in range(0, 16, 2)]
    for st, p, d in notes:
        s = t(b0 + sw(st)) + rng.gauss(0, 0.004)
        bass.note(p, s, s + d * 0.25 * SPB - 0.01, 112 + rng.gauss(0, 4), "down" if st % 2 == 0 else "up")


E9 = [52, 56, 62, 66]


def wah_bar(b0):
    for st in range(16):
        s = t(b0 + sw(st)) + rng.gauss(0, 0.004)
        accent = st in (2, 6, 10, 14)
        art = ("down" if st % 2 == 0 else "up") if accent else ("mute_down" if st % 2 == 0 else "mute_up")
        for i, p in enumerate(E9 if st % 2 == 0 else E9[::-1]):
            wah_gtr.note(p, s + i * 0.004, s + (0.2 if accent else 0.08), 100 if accent else 74, art)


# ---------------------------------------------------------------- crate intro (free time, before the grid)
intro_parts = []                 # (start_s, stereo audio)
intro_parts.append((0.0, np.stack([H.needle_drop()] * 2)))
hw_cut = fx(H.DUSTY, H.excerpt(hw, 0.0, 3.87))
intro_parts.append((0.25, np.stack([hw_cut, hw_cut])))
scr = H.scratch(H.excerpt(hw, 1.0, 1.2), ["baby", "baby", "chirp", "tear"], 0.3)
scratches.append((4.12, scr))
robot_mut = H.fit(H.robotize(H.say(ROBOT, "mutation", speed=0.9)), 0.9)
put("robot", robot_mut, 5.4)
put("A", H.fit(voice_chunk("A", "check it out"), 0.75), 6.55)
lrc += [(5.4, "ROBOT: mutation"), (6.55, "A: check it out")]

# ---------------------------------------------------------------- arrangement (bars of 4 beats)
SECTIONS = []
bar = 0


def section(name, n):
    SECTIONS.append((name, t(bar * 4), t((bar + n) * 4)))


# beat intro
section("beat", 4)
beds["impact"].append(t(0))
check = voice_chunk("A", "check it out")
for i in range(4):
    b0 = bar * 4
    boom_bap(b0, i, fill=(i == 3))
    bass_bar(b0, "verse")
    if i % 2 == 0:
        beds["stab"].append(t(b0))
    if i == 2:
        scratches.append((t(b0), H.scratch(check, ["baby", "chirp", "baby", "tear", "chirp", "chirp", "trans", "trans"], SPB)))
    bar += 1

V1 = [("A", ["Booted up the terminal", "at a quarter to three", "with a soundfont from oh-eight", "and a dream of MTV"]),
      ("B", ["First take came out", "like a SimCity tune", "now we got real drums", "and a Marshall in the room"]),
      ("C", ["Eight-string chug", "on a six-string rack", "slowed it down like tape", "and it's never coming back"]),
      ("A", ["Acid on the left", "hoover on the right", "music box detuned", "we rock it all night"], ["A", "B", "C", "ALL"])]
V2 = [("C", ["Thirteen mics", "on a DrumGizmo kit", "but the clock ran double", "and the groove wouldn't fit"]),
      ("A", ["Found the bug, fixed it", "now the snare hits true", "the limiter had a secret", "but we caught that too"]),
      ("B", ["Nirvana in the verses", "Foo Fighters on the hook", "Dire Straits telling tales", "like a paperback book"]),
      ("C", ["Aphex in the slices", "Prodigy in the bass", "Mick Gordon on the riffs", "and the Beasties in your face"],
       ["C", "A", "B", "ALL"])]
HOOK = [("Infernal engine", "Engine!"), ("Mutation station", "Station!"), ("Beats from the basement", "Basement!"),
        ("To the whole wide nation", "Nation!")]


def verse(lines, wah=False):
    global bar
    section("verse2" if wah else "verse1", 8)
    for li, entry in enumerate(lines):
        mc, chunks = entry[0], entry[1]
        tags = entry[2] if len(entry) > 2 else None
        line4(bar * 4 + li * 8, mc, chunks, tags)
    for i in range(8):
        b0 = bar * 4
        boom_bap(b0, i, fill=(i == 7))
        bass_bar(b0, "verse")
        if i % 2 == 0:
            beds["stab"].append(t(b0))
        if wah:
            wah_bar(b0)
        bar += 1


def hook():
    global bar
    section("hook", 8)
    for li, (text, shout) in enumerate(HOOK):
        robot(bar * 4 + li * 8, text, 3.2, shout)
    beds["paradise"] += [t(bar * 4), t(bar * 4 + 16)]
    for i in range(8):
        b0 = bar * 4
        boom_bap(b0, i, heavy=(i == 0), fill=(i == 7))
        bass_bar(b0, "hook", i)
        bar += 1


verse(V1)
hook()
verse(V2, wah=True)
hook()

# DJ break: cuts from every record in the crate
section("dj break", 8)
r_inf = H.robotize(H.say(ROBOT, "infernal", speed=0.9))
box_src = H.excerpt(box.mean(0), 0.15, 1.4)
CUTS = [(check, ["baby", "baby", "chirp", "chirp"]), (stab, ["tear", ".", "tear", "baby"]),
        (r_inf, ["baby", "trans", "baby", "trans"]), (box_src, ["drag", ".", "chirp", "chirp"]),
        (check, ["trans", "trans", "tear", "tear"]), (impact, ["baby", ".", "baby", "."]),
        (r_inf, ["chirp", "chirp", "chirp", "chirp"]), (stab, ["tear", "tear", "trans", "trans"])]
for i, (src, moves) in enumerate(CUTS):
    b0 = bar * 4
    boom_bap(b0, i, fill=(i == 7))
    bass_bar(b0, "verse")
    scratches.append((t(b0), H.scratch(src, moves, SPB)))
    bar += 1

# metal finale: the 8-string riff, sampled, under boom-bap and gang shouts
section("metal", 4)
beds["impact"].append(t(bar * 4))
beds["metal"] += [t(bar * 4), t(bar * 4 + 8)]
for i in range(4):
    b0 = bar * 4
    boom_bap(b0, i, heavy=True)
    bass_bar(b0, "metal")
    if i % 2 == 0:
        rap(b0, [("ALL", "No sleep", 0, 1.4), ("ALL", "till the render's done", 2, 2.6)])
    bar += 1
STOP = t(bar * 4)

# outro (free time): the music box, the robot signs off, the needle runs out
OUT0 = STOP + 0.7
for k, w in enumerate(["Rendered.", "Mixed.", "Mastered.", "Peace."]):
    put("robot", H.fit(H.robotize(H.say(ROBOT, w, speed=0.9)), 0.7), OUT0 + 0.6 + k * 1.0)
    lrc.append((OUT0 + 0.6 + k * 1.0, f"ROBOT: {w}"))
END = OUT0 + 7.0

# ---------------------------------------------------------------- render
print(f"{END:.1f}s. rendering band...")
n = int(END * SR)
kit = drums.render(END)
di_bass = bass.render(END)
di_wah = wah_gtr.render(END)

dr = drum_bus(kit, room=0.35, kick_db=2, snare_db=2, hat_db=-2)
dr = fx2(Pedalboard([Resample(target_sample_rate=26040), Bitcrush(bit_depth=12), Compressor(-22, 5, 3, 90),
                     Distortion(drive_db=4), LowpassFilter(12000)]), dr)          # SP-1200 grit
dr = dr[:, :n] * (10 ** (-14 / 20) / rig.active_rms(dr.mean(0)))
c = 10 ** ((-14 + 8) / 20)
dr = c * np.tanh(dr / c)

fuzz = amp(di_bass, "Bug333-Crunch-Cab", peak_in=0.8, drive_db=6)
bs = at_level(fx(Pedalboard([HighpassFilter(30), LowpassFilter(350)]), di_bass), -18) \
    + at_level(fx(Pedalboard([HighpassFilter(150), PeakFilter(900, 3, 1), LowpassFilter(5000)]), fuzz), -21)
wah = H.autowah(amp(di_wah, "JVM-CL-GR-Cab", peak_in=0.3), SPB)
wah = at_level(fx(Pedalboard([HighpassFilter(200), Compressor(-24, 4, 3, 80)]), wah), -24)


def lay(starts, audio, stereo=True):
    out = np.zeros((2, n), dtype=np.float32)
    a2 = audio if audio.ndim == 2 else np.stack([audio, audio])
    for s in starts:
        i = int(s * SR)
        k = min(a2.shape[1], n - i)
        if k > 0:
            out[:, i:i + k] += a2[:, :k]
    return out


par_bed = lay(beds["paradise"], fx2(Pedalboard([HighpassFilter(250), LowpassFilter(6000), Bitcrush(bit_depth=12)]), paradise_loop))
stab_bed = lay(beds["stab"], fx(Pedalboard([HighpassFilter(180), Distortion(drive_db=4)]), stab))
metal_bed = lay(beds["metal"], metal_loop)
imp_bed = lay(beds["impact"], impact)
intro_bed = np.zeros((2, n), dtype=np.float32)
for s, a in intro_parts:
    i = int(s * SR)
    intro_bed[:, i:i + a.shape[1]] += a
box_bed = lay([OUT0], fx2(Pedalboard([HighpassFilter(200), Bitcrush(bit_depth=10)]), box))
scr_bus = np.zeros(n, dtype=np.float32)
for s, a in scratches:
    i = int(s * SR)
    k = min(len(a), n - i)
    scr_bus[i:i + k] += a[:k]
crk = H.crackle(END)

# vocals: megaphone MCs with a slap, the robot with a long echo
V = {}
for k in vox:
    vox[k] = np.pad(vox[k], (0, max(0, n - len(vox[k]))))[:n]
for k in ("A", "B", "C"):
    v = fx(H.MEGAPHONE, vox[k])
    V[k] = at_level(v + fx(Pedalboard([Delay(0.09, 0.0, 1.0), LowpassFilter(3000)]), v) * 0.25, -12.5)
rb = fx(Pedalboard([HighpassFilter(70), PeakFilter(2500, 4, 1), Compressor(-24, 4, 2, 80)]), vox["robot"])
rb = at_level(rb, -13.5)
rb_echo = fx(Pedalboard([Delay(SPB * 0.75, 0.35, 1.0), HighpassFilter(300), LowpassFilter(5000)]), rb)

mix = (dr + pan(bs, 0) + pan(wah, 0.45)
       + at_level(par_bed, -21) + at_level(stab_bed, -19) * 1.0 + at_level(metal_bed, -15) + at_level(imp_bed, -17)
       + at_level(intro_bed, -17) + at_level(box_bed, -19) + pan(at_level(scr_bus, -17), -0.15)
       + pan(at_level(crk, -42), 0) * 1.0
       + pan(V["A"], MC["A"][3]) + pan(V["B"], MC["B"][3]) + pan(V["C"], MC["C"][3]) + pan(rb, 0) + pan(rb_echo * 0.3, 0.3))
mix += stereo_reverb(rb * 0.3 + at_level(box_bed.mean(0), -19) * 0.5 + (V["A"] + V["B"] + V["C"]) * 0.06, room=0.5) * 0.5
mix[:, int(STOP * SR):int(OUT0 * SR)] *= 0.0           # hard stop after the finale
mix[:, int(STOP * SR):] += pan(at_level(crk, -42), 0)[:, int(STOP * SR):]

if __import__("os").environ.get("DEBUG"):
    rig.section_table({"drums": dr, "bass": bs, "A": V["A"], "B": V["B"], "C": V["C"], "robot": rb, "scratch": scr_bus,
                       "paradise": par_bed, "metal": metal_bed, "MIX": mix},
                      [("intro", 0, INTRO_S)] + SECTIONS + [("outro", OUT0, END)])

master = Pedalboard([HighpassFilter(25), LowShelfFilter(80, 1.5), PeakFilter(350, -1.5, 0.8), HighShelfFilter(9000, 1.0),
                     Compressor(-12, 2.0, 15, 150)])
finish(mix, OUT / "check_your_render", master, fade_s=1.5, target_rms_db=-12)
with open(OUT / "lyrics.lrc", "w") as fh:
    fh.write("[ti:Check Your Render]\n")
    for s, ln in sorted(lrc):
        fh.write(f"[{int(s // 60):02d}:{s % 60:05.2f}]{ln}\n")
print("done ->", OUT / "check_your_render.mp3")
