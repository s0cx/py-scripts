import pretty_midi
import random

# --- SETTINGS ---
BPM = 85
CHORD_DURATION = 1.0
SWING = 0.05  # delay every 2nd beat slightly
OUTPUT_FILE = 'groove_progression.mid'
KEYS = {'C': 60, 'F': 65, 'G': 67, 'A': 69}

# --- PROGRESSIONS ---
progressions = [
    ['I', 'V', 'vi', 'IV'],
    ['ii', 'V', 'I'],
    ['Imaj7', 'vi7', 'IVmaj7', 'V7'],
    ['I', 'IV', 'I', 'V'],
    ['Imaj7', 'ii7', 'V7', 'Imaj7']
]

# --- CHORD FORMULAS ---
CHORDS = {
    'I':      [0, 4, 7],
    'ii':     [2, 5, 9],
    'iii':    [4, 7, 11],
    'IV':     [5, 9, 0],
    'V':      [7, 11, 2],
    'vi':     [9, 0, 4],
    'Imaj7':  [0, 4, 7, 11],
    'ii7':    [2, 5, 9, 0],
    'vi7':    [9, 0, 4, 7],
    'IVmaj7': [5, 9, 0, 4],
    'V7':     [7, 11, 2, 5]
}

def get_chord_notes(root_note, intervals):
    chord = [root_note + i for i in intervals]
    
    # Randomly invert some chords
    if len(chord) >= 3 and random.random() < 0.6:
        inversion = random.randint(0, 2)
        chord = chord[inversion:] + [n + 12 for n in chord[:inversion]]
    
    # Add octave doubling randomly
    if random.random() < 0.3:
        chord.append(chord[0] - 12)  # bass
    return chord

def progression_to_chords(prog, key='C'):
    root = KEYS[key]
    return [get_chord_notes(root, CHORDS[d]) for d in prog]

def create_midi_chords(chords, bpm):
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    piano = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Electric Piano 1'))
    
    time = 0
    for i, chord in enumerate(chords):
        delay = SWING if i % 2 == 1 else 0
        start_time = time + delay
        for note_pitch in chord:
            velocity = random.randint(70, 95)
            note = pretty_midi.Note(velocity=velocity, pitch=note_pitch, start=start_time, end=start_time + CHORD_DURATION)
            piano.notes.append(note)
        time += CHORD_DURATION

    midi.instruments.append(piano)
    return midi

def main():
    key = random.choice(list(KEYS.keys()))
    progression = random.choice(progressions)
    chords = progression_to_chords(progression, key=key)
    midi = create_midi_chords(chords, BPM)
    midi.write(OUTPUT_FILE)
    print(f"✅ MIDI saved as '{OUTPUT_FILE}' — key={key}, progression={progression}")

if __name__ == "__main__":
    main()
