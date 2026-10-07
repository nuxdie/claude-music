# Volume Gamma — a C418-style suite (original material)

Render any track: `cd album && PYTHONPATH=. ../.venv/bin/python NN_name.py` → `out/NN_name.{wav,mp3}`.
Whole album: `../.venv/bin/python assemble.py` → `out/Volume_Gamma.{wav,mp3}` + `out/tracklist.txt`.
Album art + tags: `../.venv/bin/python art.py` → pixel art in `art/` (cover + one scene per track), `out/cover.jpg`,
ID3 tags with embedded art in every mp3/wav. Re-run it after re-rendering any track (rendering rewrites the file untagged).
YouTube videos: `../.venv/bin/python video.py` → `video/NN_*.mp4` (1080p24, animated pixel scenes, partly music-driven),
`video/Volume_Gamma_full_album.mp4` and `video/youtube_description.txt` (chapters). `video.py --still N` previews a scene.
Shared toolkit: `kit.py` (instruments, tempo/rubato, synth voices, textures, tape + master, album motifs).

| # | Track | Mood / Minecraft role | Key, tempo | Instruments |
|---|---|---|---|---|
| 01 | Spawn Point | title screen | D maj, 64 | Surge pads (filter opens/closes), grand, pluck arp + echoes, analog lead, FM bells |
| 02 | Birch | overworld, Sweden-like | E aeolian, 72 | Salamander grand, string section, celli, violins, pad |
| 03 | Pebble Song | creative mode | G Lydian, 96 | Rhodes, Surge 16th arp, sine lead, synthesized shaker/tick |
| 04 | Lantern Waltz | lullaby, 3/4 | Ab maj, 88 | celesta, harp, music box, upright, sine sub |
| 05 | Dripstone | cave | D Phrygian | drones, cave drips, distant grand, reversed swells, wind |
| 06 | Disc: amber | music disc ("stal"-ish) | Ab Dorian, ~100 swing | tenor sax, Rhodes, pizz bass, brushes |
| 07 | Disc: piston | music disc ("blocks"-ish) | D Dorian, 112 | Pianet, Wurlitzer, chip lead, Surge bass, funk kit |
| 08 | Kelp Forest | underwater | Gb Lydian, 64 | chorused pads, harp, wobbly Rhodes, whale glides, bubbles |
| 09 | Basalt Deltas | Nether | C / F# tritone, 52 | distorted drone, male choir, FM clangs, timpani, bowed basses |
| 10 | Hearth | village | D Mixolydian, 6/8 | acoustic guitar, lyre, flute, cello |
| 11 | Void Gate | The End / boss | E min, 110 | saw arp ostinato, strings trem, horns, trombones, timpani, choir |
| 12 | Long Way Home | credits epic (Alpha-like) | D maj, 66–86 | everything: brings back the motifs of 01, 02 and 04 |
| 13 | Lichen (bonus) | overworld, Wet Hands-like | F maj, 70 | KW upright, pad, sine lead (from c418/) |

Libraries added for this album (libs/extra): jRhodes3c, Greg Sullivan E-Pianos (Wurlitzer/CP80/Pianet),
Ovation acoustic guitar, Karoryfer Emily (electric), MTG Solo Sax, Cithara Barbarica lyre.
