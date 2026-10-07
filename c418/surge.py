"""Surge XT (VST3, libs/surge) as a scriptable synth. Patches are built from parameters; string-valued parameters
(times, cents, voice counts) are set to the nearest valid value, so callers can write numbers in s / cents."""
import re
import sys
from pathlib import Path

import mido
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import rig  # noqa: E402
from rig import SR  # noqa: E402

SURGE = rig.LIBS / "surge/lib/vst3/Surge XT.vst3"
_UNIT = {"ms": 1e-3, "s": 1.0, "cents": 1.0, "semitones": 1.0, "voice": 1.0, "voices": 1.0, "Hz": 1.0}


def _num(text):
    m = re.match(r"\s*(-?[\d.]+)\s*([A-Za-z]*)", text)
    if not m:
        return None
    return float(m.group(1)) * _UNIT.get(m.group(2), 1.0)


class Surge:
    def __init__(self, **params):
        from pedalboard import load_plugin
        self.p = load_plugin(str(SURGE))
        self.set(global_volume=-12.0)
        self.set(**params)
        self.notes = []

    def set(self, **params):
        for k, v in params.items():
            par = self.p.parameters[k]
            vv = par.valid_values
            if isinstance(v, (int, float)) and not isinstance(v, bool) and vv and isinstance(vv[0], str):
                nums = [(_num(s), s) for s in vv]
                nums = [(x, s) for x, s in nums if x is not None]
                v = min(nums, key=lambda xs: abs(xs[0] - v))[1]
            setattr(self.p, k, v)

    def note(self, pitch, start, end, vel=90):
        self.notes.append((int(pitch), max(0.0, start), max(start + 0.02, end), int(max(1, min(127, vel)))))

    def render(self, length):
        ev = []
        for p, s, e, v in self.notes:
            ev.append((s, 1, mido.Message("note_on", note=p, velocity=v)))
            ev.append((e, 0, mido.Message("note_off", note=p)))
        ev.sort(key=lambda x: (x[0], x[1]))
        msgs = [(m.bytes(), t) for t, _, m in ev]
        self.p.reset()
        out = self.p(msgs, duration=length, sample_rate=SR, num_channels=2, buffer_size=512, reset=True)
        n = int(length * SR)
        a = np.zeros((2, n), dtype=np.float32)
        k = min(n, out.shape[1])
        a[:, :k] = out[:, :k]
        return a
