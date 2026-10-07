import json, time, numpy as np, soundfile as sf, torch
from nam.models.wavenet import WaveNet
a, sr = sf.read('p5.wav', dtype='float32'); a = a.mean(1) if a.ndim > 1 else a
cfg = json.load(open('/home/n/claude-music/libs/nam/JVM-OD2-RD-Cab.nam'))
c = cfg['config']
model = WaveNet(layers_configs=c['layers'], head_config=c['head'], head_scale=c['head_scale'])
model.import_weights(cfg['weights']); model.eval()
x = torch.from_numpy(a / np.abs(a).max() * 0.5)
t0 = time.time()
with torch.no_grad():
    y = model(x).numpy()
print('nam time %.1fs for %.1fs audio; in peak %.2f out peak %.2f' % (time.time() - t0, len(a) / sr, 0.5, np.abs(y).max()))
sf.write('amp.wav', y / np.abs(y).max() * 0.9, sr)
