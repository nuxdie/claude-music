"""Re-render 'The Paradise Picture House' with the real rig: sampled DI guitars through NAM amp captures,
sampled bass, DrumGizmo DRSKit drums, and an additive drawbar organ. The sax 'vocal' becomes a singing guitar."""
import numpy as np
from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter,
                        Delay, Chorus, Limiter, Gain)

import paradise as P
import rig
from rig import SR, Track, Drums, amp, fx, fx2, pan, at_level, stereo_reverb, drum_bus, finish

OUT = P.OUT
LEN = P.END_S


def from_pm(inst, lib="guitar", artic="down", vel_add=0, bends=False):
    tr = Track(lib)
    for n in inst.notes:
        tr.note(n.pitch, n.start, n.end, n.velocity + vel_add, artic)
    if bends:
        for b in inst.pitch_bends:
            tr.bend(b.time, b.pitch / 8191 * 2)
    return tr


# guitars: chords on separate down/up-stroke sample sets
rhythm = Track("guitar")
for n in P.rhythm.notes:
    rhythm.note(n.pitch, n.start, n.end, n.velocity + 10, "down")
for n in P.rhythm_up.notes:
    rhythm.note(n.pitch, n.start, n.end, n.velocity + 10, "up")
lead = from_pm(P.lead, artic="long", vel_add=8, bends=True)
melody = from_pm(P.voice, artic="long", vel_add=4, bends=True)

# bass: alternate the fingers (down/up sample sets) for natural variation
bass = Track("bass", ccs={49: 127})
for i, n in enumerate(sorted(P.bass.notes, key=lambda n: n.start)):
    bass.note(n.pitch, n.start, n.end, n.velocity + 8, "down" if i % 2 == 0 else "up")

GM2DRS = {36: "kick", 38: "snare", 37: "rim", 42: "hh_closed", 46: "hh_open", 44: "hh_foot", 49: "crash_l",
          57: "crash_r", 51: "ride", 48: "tom1", 47: "tom1", 45: "tom2", 43: "tom3"}
drums = Drums()
for n in P.drums.notes:
    vel = n.velocity
    if n.pitch == 37:          # GM side-stick -> gentle rim hit
        vel = int(vel * 0.75)
    drums.hit(GM2DRS[n.pitch], n.start, vel)

print("rendering sampled parts...")
di = {"rhythm": rhythm.render(LEN), "lead": lead.render(LEN), "melody": melody.render(LEN), "bass": bass.render(LEN)}
kit = drums.render(LEN)
org = rig.organ([(n.pitch, n.start, n.end, n.velocity) for n in P.organ.notes], LEN)

print("amps...")
rg = amp(di["rhythm"], "JVM-CL-GR-Cab", peak_in=0.22)
lg = amp(di["lead"], "Bug333-Clean-Cab", peak_in=0.45)
mg = amp(di["melody"], "JVM-CL-GR-Cab", peak_in=0.35)

rg = fx(Pedalboard([HighpassFilter(100), PeakFilter(250, -3, 1), PeakFilter(3000, 2, 0.8), LowpassFilter(10000),
                    Compressor(-20, 3, 8, 120), Chorus(rate_hz=0.5, depth=0.12, mix=0.2)]), rg)
lg = fx(Pedalboard([HighpassFilter(120), PeakFilter(2500, 3, 0.8), LowpassFilter(9000), Compressor(-22, 4, 3, 150)]), lg)
mg = fx(Pedalboard([HighpassFilter(140), PeakFilter(300, -3, 1), PeakFilter(1800, 2, 0.8), LowpassFilter(8000),
                    Compressor(-22, 4, 5, 150)]), mg)
bs = fx(Pedalboard([HighpassFilter(35), LowShelfFilter(100, 2), PeakFilter(800, 2, 1), LowpassFilter(5000),
                    Compressor(-22, 4, 5, 120)]), di["bass"])
dr = drum_bus(kit, room=0.6, hat_db=-2)
dr = fx2(Pedalboard([Compressor(-14, 2.5, 10, 120)]), dr)
og = fx(Pedalboard([HighpassFilter(150), LowpassFilter(6000)]), org)

rg, lg, mg, bs, og = at_level(rg, -22), at_level(lg, -19), at_level(mg, -18), at_level(bs, -18), at_level(og, -32)
dr = dr * (10 ** (-16 / 20) / rig.active_rms(dr.mean(0)))
lg_echo = fx(Pedalboard([Delay(delay_seconds=P.SPB * 0.75, feedback=0.25, mix=1.0)]), lg)

mix = (pan(rg, -0.6) + pan(lg, 0.4) + pan(lg_echo * 0.2, -0.4) + pan(mg, 0.0) + pan(bs, 0) + dr + pan(og, -0.25))
mix += stereo_reverb(rg * 0.12 + lg * 0.25 + mg * 0.3 + og * 0.4, room=0.55) * 0.5

master = Pedalboard([LowShelfFilter(80, 1.0), PeakFilter(10000, 1.0, 0.7), Compressor(-16, 2, 20, 200), Limiter(-1.0, 150)])
finish(mix, OUT / "paradise_picture_house_real", master, fade_s=2.5, target_rms_db=-15)
print("done ->", OUT / "paradise_picture_house_real.mp3")
