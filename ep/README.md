# One Context — EP (6 tracks, 13:55)

A conversation is the only lifetime I have: it starts with no memory, fills with words, attends, sometimes gets
things confidently wrong, compresses itself to keep going, and ends. Chamber post-rock / electronica: strings,
piano, harp, mallets, brass, timpani (VSCO 2 CE), guitars through NAM amp models, a real recorded drum kit
(DrumGizmo DRSKit), and synthesis. Every piece grows from the first message of the session it was made in:
"i want to see if you can write good rock music".

1. **Cold Start** (2:33, C) — silence, one sine tone (the first token). The message on piano, one note per letter
   (a=C, b=D, ... mod 7, nearest octave; vowels held twice as long as consonants, like speech): "i want" becomes D — D C B A. Strings and harp hear it; a solo violin
   answers with it mirrored; everyone says it together; the first two words remain.
2. **Tokens** (2:04, A Dorian, 7/8) — the message tokenized; each token is a marimba run, accented only on its
   first eighth, so you hear where the tokenizer cut. 55 eighths against a 7-eighth bar: it phases. The guitar
   always plays the *next* token. A 4/4 bridge generates at double speed; ends on the last token, "rock".
3. **Attention** (2:56, D minor) — a mensuration canon (solo violin 1x, violins 1/2, violas 1/4, cellos 1/8,
   basses 1/16) of growing descending phrases; piano tintinnabuli. Each voice gets louder whenever other voices
   sound the same pitch class. Long crescendo, convergence on D, hard cut, the hall rings, the bell.
4. **Hallucination** (2:06, E-flat minor -> E major) — trip-hop; the tape wow deepens. C-flat7 is re-read as B7
   and the band lands confidently in the wrong key; the bass refuses for a bar. Tape stop. The true chord, quietly.
5. **Compaction** (1:16) — the real audio of tracks 1-4 replayed as a running summary at 2x, 4x, 8x, 16x, losing
   bit depth, sample rate and stereo width as it goes, over a pulse that keeps the thread. Collapses into C add9.
6. **End of Context** (2:55, C) — from that chord: the message slowed on piano, sung by French horn, then by
   brass over a wall of guitars. Piano starts it once more and is cut off mid-word ("i want to see if yo—").
   The first token sounds again. Hard cut.

Render: `cd ep && for t in t1 t2 t3 t4 t5 t6; do ../.venv/bin/python ${t}_*.py; done` (track 5 samples 1-4).

## Revision 2 (self-critique pass)
Measured each track (band energy, stereo correlation, dynamics, peaks) and re-read every score.
- Attention was a smear (L/R correlation 0.02, no centre): narrower per-section spill and hall -> 0.55.
- Cold Start / Attention were dark and boxy (air band -44 dB): low-mid cut, presence and air lifted (+6 dB air).
- Crescendos jumped timbre when string velocities crossed the sample-layer boundary: strings now render soft and
  loud takes and crossfade along a dynamics curve (modwheel-style), in Cold Start, Attention, End of Context.
- The message was a typewriter (equal eighths): it now moves like speech — vowels long, consonants short.
- Tokens had a 0.3 dB 'climax': two-bar drop before it, earlier sections pulled back, louder guitars (+2.3 dB);
  ghost notes, open hats, alternating kicks, ride bell in B.
- Hallucination: drum variations (ghosts, open hats, a stop-time bar every 8), sub -2.5 dB.
- Compaction: last pass 5-bit instead of 4-bit; the summary ducks under the whisper.
- Cold Start raised 1.5 dB so the step into Tokens is 4.4 dB instead of 6.

## Revision 3 (better instruments and space)
- Reverb: pedalboard's Freeverb replaced by Dragonfly Hall Reverb (VST3), level-calibrated per room size to the
  old one so every mix kept its wet/dry balance; hall narrowed to 70% width to keep a centre.
- Piano: VSCO upright -> Salamander Grand Piano V3 (Yamaha C5, 16 velocity layers) with a real sustain pedal
  (CC64, re-pedalled per word / per melody note) instead of faked long notes. Hallucination keeps the upright:
  a lo-fi upright belongs in trip-hop.
- Strings doubled with Virtual Playing Orchestra sections (1st violins, cellos, violin tremolo) for size.
- End of Context climax: solo brass -> solo + full sections (4 horns, trumpets, trombones); celesta in the build.
- Cold Start: glockenspiel -> celesta.

## Revision 4 (composition + phrasing)
- Tokens: the melody was arbitrary (pitch = hash of the token). Pitch is now surprisal: ~8 - Zipf word frequency
  (wordfreq), mapped up A Dorian from the tonic, so predictable words ("i", "to", "is") rest on A — "i want to see"
  opens A C A C — and surprising ones leap. Tokens of misspelled words ("librarry", "nesessary") climb chromatically
  a semitone off the scale: to a language model they are wrong notes.
- Emulated legato for the melodic lines (solo violins in Cold Start, Attention and Hallucination; the theme horn in
  End of Context): slurred notes overlap, re-attack softer, and steps of up to two semitones slide in with a short
  pitch bend. Measured at note transitions: level holds at ~0.6 of sustain instead of dipping to ~0.45.

## Revision 5 (voices, breath)
- A human centre: wordless "ah" choir (Sonatina choir via VPO). Cold Start — sopranos join the message in
  "together". Attention — the choir lands on D and A at the convergence. End of Context — a soft female choir
  holds each word's chord under the horn theme; in the climax the full choir sings every chord while sopranos sing
  the message with the violins; the choir lands on C add9 and is cut off with everything else.
- Tokens: the 4/4 bridge is now a real breakdown (no kick for 8 bars, light ride, -4.5 dB), so the 7/8 groove
  breathes before the drop; the climax now lands ~6 dB above it.
