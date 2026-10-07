import pretty_midi as pm
m = pm.PrettyMIDI(initial_tempo=120); d = pm.Instrument(0, is_drum=True)
for bar in range(2):
    for i in range(8):
        b = bar * 2 + i * 0.25
        d.notes.append(pm.Note(100 if i % 2 == 0 else 70, 56, b, b + .1))
    for k in (0, 0.75): d.notes.append(pm.Note(115, 36, bar*2 + k, bar*2 + k + .1))
    for s in (0.5, 1.5): d.notes.append(pm.Note(120, 38, bar*2 + s, bar*2 + s + .1))
d.notes.append(pm.Note(120, 54, 4, 4.1)); d.notes.append(pm.Note(120, 36, 4, 4.1))
m.instruments.append(d); m.write('d.mid')
