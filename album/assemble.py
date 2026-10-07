"""Concatenate out/NN_*.wav into one album file with gaps, print a timestamped track list."""
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

OUT = Path(__file__).resolve().parent / "out"
GAP = 2.5
files = sorted(p for p in OUT.glob("[0-9][0-9]_*.wav"))
parts, t, lines = [], 0.0, []
for f in files:
    a, sr = sf.read(f, dtype="float32")
    lines.append(f"{int(t // 60):02d}:{int(t % 60):02d}  {f.stem}  ({int(len(a) / sr // 60)}:{int(len(a) / sr % 60):02d})")
    parts += [a, np.zeros((int(GAP * sr), 2), dtype="float32")]
    t += len(a) / sr + GAP
album = np.concatenate(parts[:-1])
sf.write(OUT / "Volume_Gamma.wav", album, sr)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT / "Volume_Gamma.wav"), "-b:a", "256k",
                str(OUT / "Volume_Gamma.mp3")], check=True)
(OUT / "tracklist.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
print(f"total {t / 60:.1f} min")
