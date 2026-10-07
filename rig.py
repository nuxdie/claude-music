"""Shared rendering rig: sampled guitar/bass (sfizz + Unreal Instruments SFZ), real drums (DrumGizmo DRSKit),
neural amp models (NAM), a small tonewheel-organ synth, and mixing helpers. Everything runs at 48 kHz."""
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pretty_midi as pm
import soundfile as sf
import torch
from pedalboard import Pedalboard, Reverb

SR = 48000
ROOT = Path(__file__).parent
LIBS = ROOT / "libs"
SFIZZ = LIBS / "sfizz-src/build/library/bin/sfizz_render"
GUITAR_SFZ = LIBS / "standard_guitar/UI_Standard_Guitar/Linux"
BASS_SFZ = LIBS / "standard_bass/Ui_Standard_Bass_V2/Linux"
DRSKIT = LIBS / "drskit/DRSKit"
NAM_DIR = LIBS / "nam"
PRE = 0.1          # seconds of lead-in for keyswitches / CCs, trimmed after rendering

# articulation -> (sfz file, keyswitch note, extra CCs)
ARTIC = {
    "down":      ("Sus_Down.sfz", 24, {}),
    "up":        ("Sus_Up.sfz", 25, {}),
    "mute_down": ("Mute_Down.sfz", 27, {}),
    "mute_up":   ("Mute_Up.sfz", 28, {}),
    "long":      ("Sus_Long.sfz", 24, {23: 127}),
}


GUITAR_TOP = 86       # D6: highest sampled guitar note


class Track:
    """A sampled-instrument part. Times in seconds; bends in semitones (±2 max)."""
    folded = 0           # count of guitar notes folded down an octave (they were out of range)

    def __init__(self, lib="guitar", ccs=None):
        self.lib = lib
        self.notes = {}           # artic -> list of pm.Note
        self.bends = []           # (time, semitones)
        self.ccs = ccs or {}

    def note(self, pitch, start, end, vel, artic="down"):
        if lib_offset := (12 if self.lib == "bass" else 0):
            pitch += lib_offset
        if self.lib == "guitar" and pitch > GUITAR_TOP:   # above the sampled range the note would be silent
            Track.folded += 1
            while pitch > GUITAR_TOP:
                pitch -= 12
        vel = int(max(1, min(127, vel)))
        self.notes.setdefault(artic, []).append(pm.Note(vel, int(pitch), max(0.0, start), max(start + 0.02, end)))

    def bend(self, time, semis):
        self.bends.append((max(0.0, time), semis))

    def render(self, length, down=0):
        """down > 0: tape-varispeed. Render `down` semitones higher and faster, then slow the audio back down,
        reaching below the sampled range (e.g. 8-string tunings) with a darker, longer attack."""
        if down:
            r = 2 ** (down / 12)
            fast = Track(self.lib, self.ccs)
            for artic, notes in self.notes.items():
                fast.notes[artic] = [pm.Note(n.velocity, n.pitch + down, n.start / r, n.end / r) for n in notes]
            fast.bends = [(tm / r, s) for tm, s in self.bends]
            y = fast.render(length / r + 0.5)
            n_out = int(length * SR)
            return np.interp(np.arange(n_out) / r, np.arange(len(y)), y).astype(np.float32)
        sfz_dir = GUITAR_SFZ if self.lib == "guitar" else BASS_SFZ
        out = np.zeros(int(length * SR), dtype=np.float32)
        with tempfile.TemporaryDirectory() as td:
            for artic, notes in self.notes.items():
                sfz, ks, ccs = ARTIC[artic]
                m = pm.PrettyMIDI(initial_tempo=120)
                inst = pm.Instrument(0)
                inst.notes.append(pm.Note(100, ks, 0.0, 0.03))
                for cc, val in {**self.ccs, **ccs}.items():
                    inst.control_changes.append(pm.ControlChange(cc, val, 0.0))
                for n in notes:
                    inst.notes.append(pm.Note(n.velocity, n.pitch, n.start + PRE, n.end + PRE))
                for tm, semis in sorted(self.bends):
                    inst.pitch_bends.append(pm.PitchBend(int(max(-8192, min(8191, semis / 2 * 8191))), tm + PRE))
                m.instruments.append(inst)
                mid, wav = Path(td) / f"{artic}.mid", Path(td) / f"{artic}.wav"
                m.write(str(mid))
                subprocess.run([str(SFIZZ), "--sfz", str(sfz_dir / sfz), "--midi", str(mid), "--wav", str(wav),
                                "-s", str(SR), "-q", "3", "-p", "256"], check=True, capture_output=True)
                a, _ = sf.read(wav, dtype="float32")
                a = a.mean(axis=1)[int(PRE * SR):]
                k = min(len(a), len(out))
                out[:k] += a[:k]
        return out


# ---------------------------------------------------------------- drums
DRUM = {  # DRSKit midimap (no whiskers)
    "kick": 36, "snare": 38, "rim": 37, "hh_closed": 56, "hh_tight": 42, "hh_semi": 46, "hh_open": 58,
    "hh_foot": 44, "crash_l": 49, "crash_r": 57, "crash_l_tip": 54, "ride": 51, "ride_bell": 53,
    "tom1": 47, "tom2": 43, "tom3": 41,
}


class Drums:
    def __init__(self):
        self.hits = []

    def hit(self, name, time, vel):
        self.hits.append((DRUM[name], max(0.0, time), int(max(1, min(127, vel)))))

    def render(self, length):
        """Returns dict of mic channel -> mono array."""
        m = pm.PrettyMIDI(initial_tempo=120)
        inst = pm.Instrument(0, is_drum=True)
        for p, tm, v in self.hits:
            inst.notes.append(pm.Note(v, p, tm + PRE, tm + PRE + 0.05))
        m.instruments.append(inst)
        n = int(length * SR)
        with tempfile.TemporaryDirectory() as td:
            mid = Path(td) / "d.mid"
            m.write(str(mid))
            subprocess.run(["drumgizmo", "-i", "midifile", "-I", f"file={mid},midimap={DRSKIT}/Midimap_no_whiskers.xml,speed=2",  # its MIDI reader runs 2x slow for 120-BPM files
                            "-o", "wavfile", "-O", f"file={td}/d,srate={SR}", str(DRSKIT / "DRSKit_no_whiskers.xml")],
                           check=True, capture_output=True)
            out = {}
            for f in Path(td).glob("d*-*.wav"):
                ch = f.stem[1:].rsplit("-", 1)[0]
                a, _ = sf.read(f, dtype="float32")
                a = a[int(PRE * SR):]
                out[ch] = np.pad(a, (0, max(0, n - len(a))))[:n]
        return out


# ---------------------------------------------------------------- amps
_models = {}


def _load_nam(name):
    if name not in _models:
        from nam.models.wavenet import WaveNet
        cfg = json.load(open(NAM_DIR / f"{name}.nam"))
        c = cfg["config"]
        model = WaveNet(layers_configs=c["layers"], head_config=c["head"], head_scale=c["head_scale"])
        model.import_weights(cfg["weights"])
        model.eval()
        _models[name] = model
    return _models[name]


def amp(x, model, drive_db=0.0, peak_in=0.5):
    """Run a DI signal through a NAM capture. The DI is peak-normalised to `peak_in` (+drive_db) first."""
    net = _load_nam(model)
    pk = np.abs(x).max()
    if pk < 1e-6:
        return np.zeros_like(x)
    x = (x / pk * peak_in * 10 ** (drive_db / 20)).astype(np.float32)
    ctx, chunk = 8192, SR * 10
    y = np.zeros_like(x)
    with torch.no_grad():
        for s in range(0, len(x), chunk):
            a = max(0, s - ctx)
            seg = torch.from_numpy(x[a:s + chunk])
            out = net(seg).numpy()
            y[s:s + chunk] = out[s - a:]
    return y


# ---------------------------------------------------------------- organ
def organ(notes, length, drawbars=(8, 8, 6, 0, 0, 0, 0, 0, 0)):
    """Tonewheel-style additive organ with a slow rotary-ish wobble. notes: (pitch, start_s, end_s, vel)."""
    ratios = [0.5, 1.5, 1, 2, 3, 4, 5, 6, 8]
    out = np.zeros(int(length * SR) + SR, dtype=np.float32)
    for p, s, e, v in notes:
        f0 = 440 * 2 ** ((p - 69) / 12)
        n = int((e - s) * SR)
        if n <= 0:
            continue
        tt = np.arange(n) / SR
        sig = np.zeros(n, dtype=np.float32)
        for r, d in zip(ratios, drawbars):
            if d and f0 * r < SR / 2.2:
                sig += (d / 8) * np.sin(2 * np.pi * f0 * r * tt + 0.004 * np.sin(2 * np.pi * 0.8 * tt))
        env = np.minimum(1, tt / 0.008) * np.minimum(1, (tt[::-1]) / 0.03)
        i0 = int(s * SR)
        out[i0:i0 + n] += sig * env * (v / 127) * 0.1
    return out[:int(length * SR)]


# ---------------------------------------------------------------- mix helpers
def fx(board, x):
    return board(np.asarray(x, dtype=np.float32)[np.newaxis, :], SR)[0]


def fx2(board, x2):
    return board(np.asarray(x2, dtype=np.float32), SR)


def pan(x, p):
    ang = (p + 1) * math.pi / 4
    return np.stack([x * math.cos(ang), x * math.sin(ang)]).astype(np.float32)


def active_rms(x):
    a = x[np.abs(x) > 1e-4]
    return float(np.sqrt(np.mean(a ** 2))) if len(a) else 1e-9


def at_level(x, db):
    """Scale so the signal's RMS (while playing) sits at `db` dBFS."""
    return x * (10 ** (db / 20) / max(active_rms(x), 1e-9))


DRAGONFLY = LIBS / "plugins/dragonfly-reverb-3.2.10/DragonflyHallReverb.vst3"
_hall = None


def hall(x, decay=2.2, size=30.0, predelay=18.0, width=100.0, high_cut=7600.0, low_cut=50.0, early=12.0, late=100.0):
    """Dragonfly Hall Reverb (VST3) — wet signal only. x: mono or (2, N). Returns (2, N)."""
    global _hall
    from pedalboard import load_plugin
    if _hall is None:
        _hall = load_plugin(str(DRAGONFLY))
    h = _hall
    h.sample_rate_frames = SR
    h.dry_level, h.early_level, h.late_level = 0.0, early, late
    h.size_m, h.decay_s, h.predelay_ms, h.width = size, decay, predelay, width
    h.high_cut_hz, h.low_cut_hz, h.early_send, h.diffuse, h.modulation = high_cut, low_cut, 30.0, 90.0, 20.0
    x2 = np.stack([x, x]) if x.ndim == 1 else x
    return h(np.ascontiguousarray(x2, dtype=np.float32), SR, reset=True)


def stereo_reverb(send, room=0.5, damping=0.5):
    """Hall send. room 0..1 -> decay 0.8-4.0 s and size 12-50 m; damping 0..1 -> high cut 16k-4k."""
    # calibrated (per channel) to the Freeverb levels the mixes were balanced with, so swapping engines keeps them
    gain_db = np.interp(room, [0.25, 0.5, 0.7, 0.9, 0.95], [-5.5, -3.8, -2.2, 1.4, 2.1])
    return hall(send, decay=0.8 + 3.2 * room, size=12 + 38 * room, high_cut=16000 - 12000 * damping, width=70.0,
                predelay=10 + 20 * room) * 10 ** (gain_db / 20)


def _polarity_match(ref, x):
    return x if np.dot(ref, x) >= 0 else -x


def drum_bus(ch, close=1.0, room=0.5, kick_db=0.0, snare_db=0.0, hat_db=0.0, tom_db=0.0, oh_db=0.0):
    """Mix DrumGizmo mic channels (drummer's perspective panning) into a stereo bus, before bus processing."""
    from pedalboard import Compressor, HighpassFilter, LowpassFilter, PeakFilter, LowShelfFilter, Gain
    g = lambda db: 10 ** (db / 20)
    kick = ch["Kdrum_front"] + _polarity_match(ch["Kdrum_front"], ch["Kdrum_back"]) * 0.6
    kick = fx(Pedalboard([HighpassFilter(30), PeakFilter(60, 4, 1.0), PeakFilter(350, -6, 1.2), PeakFilter(4000, 5, 1.0),
                          Compressor(-18, 4, 5, 80)]), kick)
    snare = ch["Snare_top"] + _polarity_match(ch["Snare_top"], ch["Snare_bottom"]) * 0.45
    snare = fx(Pedalboard([HighpassFilter(80), PeakFilter(200, 3, 1.0), PeakFilter(900, -3, 1.0), PeakFilter(5000, 3, 0.8),
                           Compressor(-18, 4, 3, 100)]), snare)
    hat = fx(Pedalboard([HighpassFilter(300), LowShelfFilter(600, -3)]), ch["Hihat"])
    toms = [fx(Pedalboard([HighpassFilter(60), PeakFilter(500, -4, 1), PeakFilter(4000, 3, 1), Compressor(-20, 3, 5, 120)]),
               ch[t]) for t in ("Tom1", "Tom2", "Tom3")]
    ohs = [fx(Pedalboard([HighpassFilter(180), PeakFilter(10000, 2, 0.7)]), ch[o]) for o in ("OHL", "OHR")]
    ride = fx(Pedalboard([HighpassFilter(250)]), ch["Ride"])
    amb = [ch["AmbL"], ch["AmbR"]]
    bus = (pan(at_level(kick, -16) * g(kick_db) * close, 0) + pan(at_level(snare, -17) * g(snare_db) * close, 0)
           + pan(at_level(hat, -30) * g(hat_db) * close, -0.45)
           + pan(toms[0] * g(tom_db) * 2.0, -0.15) + pan(toms[1] * g(tom_db) * 2.0, 0.3) + pan(toms[2] * g(tom_db) * 2.0, 0.55)
           + pan(ride * 0.6, 0.5)
           + pan(ohs[0] * g(oh_db) * 1.0, -0.8) + pan(ohs[1] * g(oh_db) * 1.0, 0.8)
           + pan(amb[0] * room * 1.5, -1) + pan(amb[1] * room * 1.5, 1))
    return bus


def loud_db(mix, block=0.4, pct=70):
    """Loudness of the loud parts: mean RMS of the blocks above the given percentile (quiet sections stay quiet)."""
    m = mix.mean(0) if mix.ndim == 2 else mix
    n = int(block * SR)
    r = np.array([np.sqrt(np.mean(m[i:i + n] ** 2)) for i in range(0, len(m) - n, n)]) + 1e-12
    return float(20 * np.log10(np.sqrt(np.mean(r[r >= np.percentile(r, pct)] ** 2))))


def automate(x, windows, ramp=0.08):
    """Gain automation: windows = [(start_s, end_s, db)], with short linear ramps. Works on mono or stereo."""
    g = np.ones(x.shape[-1], dtype=np.float32)
    rn = int(ramp * SR)
    for s, e, db in windows:
        a, b = int(s * SR), min(int(e * SR), len(g))
        if b <= a:
            continue
        seg = np.full(b - a, 10 ** (db / 20), dtype=np.float32)
        r = min(rn, (b - a) // 2)
        if r > 0:
            seg[:r] = np.linspace(1, seg[r], r)
            seg[-r:] = np.linspace(seg[r], 1, r)
        g[a:b] *= seg
    return x * g


def brickwall(x, ceiling_db=-1.0, window=0.012):
    """Look-ahead peak limiter: only reduces gain around peaks (no hidden pre-compression).
    Gain = moving average of a min-filtered target gain, so every peak is guaranteed under the ceiling."""
    from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
    ceil = 10 ** (ceiling_db / 20)
    w = 2 * int(window * SR) + 1
    env = maximum_filter1d(np.abs(x).max(axis=0), size=w)
    target = np.minimum(1.0, ceil / np.maximum(env, 1e-9))
    g = uniform_filter1d(minimum_filter1d(target, size=w), size=w)
    return (x * g).astype(np.float32)


def finish(mix, path, master, fade_s=2.0, target_rms_db=-14.0):
    """Master bus, gain into a peak limiter until the loud sections hit the target, fade tail, write wav + mp3."""
    mix = master(mix / (np.abs(mix).max() + 1e-9) * 0.7, SR)
    gain_db = 0.0
    for _ in range(6):  # limiting lowers loudness a little, so iterate the input gain
        out = brickwall(mix * 10 ** (gain_db / 20))
        err = target_rms_db - loud_db(out)
        if abs(err) < 0.1:
            break
        gain_db += err
    mix = np.clip(out, -0.98, 0.98)
    print(f"master: +{gain_db:.1f} dB into limiter, loud-section RMS {loud_db(mix):.1f} dBFS")
    f = int(fade_s * SR)
    mix[:, -f:] *= np.linspace(1, 0, f) ** 2
    path = Path(path)
    sf.write(path.with_suffix(".wav"), mix.T, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path.with_suffix(".wav")),
                    "-b:a", "256k", str(path.with_suffix(".mp3"))], check=True)
    return mix


def section_table(stems, sections):
    """Print RMS (dBFS) of each stem in each section. stems: {name: mono or stereo array}; sections: [(name, s, e)]."""
    print("section     " + " ".join(f"{k[:7]:>7s}" for k in stems))
    for name, s, e in sections:
        a, b = int(s * SR), int(e * SR)
        row = []
        for v in stems.values():
            x = v.mean(0) if v.ndim == 2 else v
            row.append(20 * np.log10(np.sqrt(np.mean(x[a:b] ** 2)) + 1e-9))
        print(f"{name:11s} " + " ".join(f"{r:7.1f}" for r in row))
