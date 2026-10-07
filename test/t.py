import pretty_midi as pm
m = pm.PrettyMIDI(initial_tempo=120); g = pm.Instrument(0)
g.notes.append(pm.Note(100, 24, 0.0, 0.05))  # keyswitch c1
t = 0.2
for p in [40, 40, 43, 45, 40, 47, 45, 43]:
    g.notes.append(pm.Note(110, p, t, t + 0.45)); t += 0.5
m.instruments.append(g); m.write('t.mid')
