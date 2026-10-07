"""Shared tools for the 'One Context' EP: a generic SFZ sampler (VSCO 2 CE orchestra, stereo), the seed motif,
gain envelopes, a tubular-bell / sine helper, and loudness/section diagnostics."""
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pretty_midi as pm
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import rig  # noqa: E402
from rig import SR, SFIZZ, PRE  # noqa: E402

VSCO = rig.LIBS / "vsco"
VSCO_LINUX = rig.LIBS / "vsco_linux"
GRAND = rig.LIBS / "salamander/Salamander Grand Piano V3.sfz"
VPO = rig.LIBS / "vpo"
EP_OUT = Path(__file__).resolve().parent / "out"
EP_OUT.mkdir(exist_ok=True)


def _linux_sfz(name):
    """VSCO's SFZ files use Windows paths; keep a converted copy next to the samples."""
    VSCO_LINUX.mkdir(exist_ok=True)
    dst = VSCO_LINUX / name
    if not dst.exists():
        txt = (VSCO / name).read_text(errors="replace").replace("\r", "")
        txt = txt.replace("\\", "/")
        txt = txt.replace("default_path=", f"default_path={VSCO}/")
        dst.write_text(txt)
    return dst


def _legato(notes, slur_gap=0.15, overlap=0.06, slide=0.07, soften=14):
    """Emulate a legato player on a sample library without legato transitions. Notes closer than `slur_gap` are
    slurred: the previous note is held `overlap` into the next, the new note re-attacks softer, and for steps of
    up to 2 semitones it slides in from the previous pitch with a short pitch bend (default +-2 st bend range)."""
    notes = sorted(notes, key=lambda n: n.start)
    out, bends = [], []
    for i, n in enumerate(notes):
        prev = notes[i - 1] if i else None
        slurred = prev is not None and 0 <= n.start - prev.end < slur_gap
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        end = n.end + overlap if nxt is not None and 0 <= nxt.start - n.end < slur_gap else n.end
        vel = max(1, n.velocity - soften) if slurred else n.velocity
        out.append(pm.Note(vel, n.pitch, n.start, max(end, n.start + 0.03)))
        if slurred and 0 < abs(n.pitch - prev.pitch) <= 2:
            d = prev.pitch - n.pitch
            for k in range(8):
                fr = k / 7
                bends.append((n.start + slide * fr, int(np.clip(d * (1 - fr) ** 2 / 2 * 8191, -8192, 8191))))
        else:
            bends.append((n.start, 0))
    return out, bends


class Sampler:
    """Any SFZ instrument. Notes in seconds; renders stereo (2, N)."""

    def __init__(self, sfz, transpose=0, ccs=None, legato=False):
        self.sfz = sfz
        self.legato = legato          # monophonic line: overlap, softer slurred re-attacks, small-interval slides
        self.transpose = transpose
        self.notes = []
        self.ccs = ccs or {}
        self.cc_events = []           # (time_s, cc, value): e.g. sustain pedal (64), dynamics (1)

    def cc(self, time, number, value):
        self.cc_events.append((max(0.0, time), number, int(max(0, min(127, value)))))

    def pedal(self, down, up):
        """Sustain pedal down/up (CC64), with a tiny overlap like a real foot."""
        self.cc(down, 64, 127)
        self.cc(up, 64, 0)

    def note(self, pitch, start, end, vel):
        self.notes.append(pm.Note(int(max(1, min(127, vel))), int(pitch + self.transpose), max(0.0, start),
                                  max(start + 0.02, end)))

    def render_dynamic(self, length, dyn, lo=46, hi=108):
        """Modwheel-style dynamics for velocity-layered samples: render every note at a soft and a loud velocity
        and crossfade the two takes with dyn(t_seconds) in 0..1, so a crescendo changes timbre gradually instead of
        jumping when the velocity crosses a layer boundary."""
        saved = self.notes
        takes = []
        for v in (lo, hi):
            self.notes = [pm.Note(v, nt.pitch, nt.start, nt.end) for nt in saved]
            takes.append(self.render(length))
        self.notes = saved
        n = takes[0].shape[1]
        w = np.clip(np.asarray(dyn(np.arange(n) / SR), dtype=np.float32), 0, 1)
        gain_lo = np.cos(w * np.pi / 2)
        gain_hi = np.sin(w * np.pi / 2)
        return takes[0] * gain_lo + takes[1] * gain_hi

    def render(self, length):
        n = int(length * SR)
        out = np.zeros((2, n), dtype=np.float32)
        if not self.notes:
            return out
        path = _linux_sfz(self.sfz) if not Path(self.sfz).is_absolute() else Path(self.sfz)
        m = pm.PrettyMIDI(initial_tempo=120)
        inst = pm.Instrument(0)
        for cc, val in self.ccs.items():
            inst.control_changes.append(pm.ControlChange(cc, val, 0.0))
        for tm, cc, val in sorted(self.cc_events):
            inst.control_changes.append(pm.ControlChange(cc, val, tm + PRE))
        if self.legato:
            notes, bends = _legato(self.notes)
            inst.notes = [pm.Note(nt.velocity, nt.pitch, nt.start + PRE, nt.end + PRE) for nt in notes]
            inst.pitch_bends = [pm.PitchBend(v, tm + PRE) for tm, v in bends]
        if not self.legato:
            for nt in self.notes:
                inst.notes.append(pm.Note(nt.velocity, nt.pitch, nt.start + PRE, nt.end + PRE))
        m.instruments.append(inst)
        with tempfile.TemporaryDirectory() as td:
            mid, wav = Path(td) / "x.mid", Path(td) / "x.wav"
            m.write(str(mid))
            subprocess.run([str(SFIZZ), "--sfz", str(path), "--midi", str(mid), "--wav", str(wav), "-s", str(SR),
                            "-q", "3", "-p", "256"], check=True, capture_output=True)
            a, _ = sf.read(wav, dtype="float32")
        a = a.T[:, int(PRE * SR):]
        k = min(a.shape[1], n)
        out[:, :k] = a[:, :k]
        return out


# ---------------------------------------------------------------- the seed motif
FIRST_MESSAGE = "i want to see if you can write good rock music"
C_MAJOR = [60, 62, 64, 65, 67, 69, 71]


def motif_words(msg=FIRST_MESSAGE, start=64):
    """Each letter -> a C-major scale degree ((a=0) mod 7), placed in the octave nearest the previous note."""
    out, prev = [], start
    for w in msg.split():
        word = []
        for ch in w:
            deg = (ord(ch) - 97) % 7
            p = min((C_MAJOR[deg] + 12 * o for o in (-1, 0, 1)), key=lambda c: abs(c - prev))
            word.append(p)
            prev = p
        out.append((w, word))
    return out


VOWELS = set("aeiouy")


def speech_durs(word, unit):
    """Durations that move like the word is spoken: vowels sing (2 units), consonants are short (1 unit),
    the last letter of the word stretches (x1.5) like a word-final syllable."""
    d = [unit * (2 if ch in VOWELS else 1) for ch in word]
    d[-1] *= 1.5
    return d


# ---------------------------------------------------------------- envelopes & synthesis
def envelope(points, n):
    """Piecewise-linear gain in dB from [(time_s, db), ...]; returns linear gain array of length n."""
    ts = np.array([p[0] for p in points]) * SR
    db = np.array([p[1] for p in points], dtype=np.float64)
    g = np.interp(np.arange(n), ts, db)
    return (10 ** (g / 20)).astype(np.float32)


def sine(freq, start, end, length, amp=0.2, att=0.5, rel=0.5):
    n = int(length * SR)
    out = np.zeros(n, dtype=np.float32)
    i0 = int(start * SR)
    m = min(int((end - start + rel) * SR), n - i0)
    if m <= 0:
        return out
    tt = np.arange(m) / SR
    env = np.minimum(1, tt / max(att, 1e-3)) * np.clip((end - start + rel - tt) / max(rel, 1e-3), 0, 1)
    out[i0:i0 + m] = amp * env * np.sin(2 * np.pi * freq * tt)
    return out


def hz(p):
    return 440.0 * 2 ** ((p - 69) / 12)


def section_report(mix, sections):
    for name, s, e in sections:
        x = mix.mean(0)[int(s * SR):int(e * SR)]
        print(f"  {name:14s} {20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9):6.1f} dB")


class Layer:
    """Several samplers playing the same part (e.g. VSCO violins doubled by VPO 1st violins), mixed by gain (dB)."""

    def __init__(self, *parts):
        self.parts = parts              # (Sampler, gain_db) pairs

    def note(self, pitch, start, end, vel):
        for s, _ in self.parts:
            s.note(pitch, start, end, vel)

    def pedal(self, down, up):
        for s, _ in self.parts:
            s.pedal(down, up)

    def render(self, length):
        return sum(s.render(length) * 10 ** (g / 20) for s, g in self.parts)

    def render_dynamic(self, length, dyn, lo=46, hi=108):
        return sum(s.render_dynamic(length, dyn, lo, hi) * 10 ** (g / 20) for s, g in self.parts)


def vpo(rel):
    return str(VPO / rel)
