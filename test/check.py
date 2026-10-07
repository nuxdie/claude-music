import sys, numpy as np, soundfile as sf
sys.argv = sys.argv  # usage: check.py file.wav
a, sr = sf.read(sys.argv[1]); m = a.mean(1)
print('len %.1fs peak %.3f rms %.1f dBFS' % (len(m) / sr, np.abs(a).max(), 20 * np.log10(np.sqrt((m ** 2).mean()))))
seg = 10 * sr
print('rms per 10s:', ' '.join('%.0f' % (20 * np.log10(np.sqrt((m[i:i + seg] ** 2).mean()) + 1e-9)) for i in range(0, len(m), seg)))
corr = np.corrcoef(a[:, 0], a[:, 1])[0, 1]; print('L/R correlation %.2f' % corr)
