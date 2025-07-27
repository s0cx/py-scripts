import pretty_midi
import random
import os

# --- SETTINGS ---
BPM = 82
CHORD_DURATION = 1.0
SWING = 0.04
OUTPUT_DIR = 'midi_exports'

KEYS = {
    'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65,
    'F#': 66, 'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71
}

progressions = [
    ['Imaj7', 'vi7', 'IVmaj7', 'V7'],
    ['ii7', 'V7', 'Imaj7', 'Imaj7'],
    ['I', 'IV', 'I', 'V'],
    ['I', 'V', 'vi', 'IV'],
    ['Imaj7', 'iii7', 'vi7', 'IVmaj7']
]

CHORDS = {
    'I':      [0, 4, 7],
    'ii':     [2, 5, 9],
    'iii':    [4, 7, 11],
    'IV':     [5, 9, 0],
    'V':      [7, 11, 2],
    'vi':     [9, 0, 4],
    'Imaj7':  [0, 4, 7, 11],
    'ii7':    [2, 5, 9, 0],
    'iii7':   [4, 7, 11, 2],
    'vi7':    [9, 0, 4, 7],
    'IVmaj7': [5, 9, 0, 4],
    'V7':     [7, 11, 2, 5]
}

def get_chord_notes(root_note, intervals):
    chord = [root_note + i for i in intervals]

    # Inversion
    if len(chord) >= 3 and random.random() < 0.6:
        inversion = random.randint(0, len(chord)-2)
        chord = chord[inversion:] + [n + 12 for n in chord[:inversion]]

    # Bass doubling
    if random.random() < 0.3:
        chord = [chord[0] - 12] + chord

    return chord

def staggered_chord(chord, start_time, duration, roll_strength=0.04):
    return [
        pretty_midi.Note(
            velocity=random.randint(68, 92),
            pitch=pitch,
            start=start_time + (i * roll_strength if i > 0 else 0),
            end=start_time + duration
        ) for i, pitch in enumerate(chord)
    ]

def build_progression(prog, key_note):
    return [get_chord_notes(key_note, CHORDS[d]) for d in prog]

def create_midi(chords, bpm, key, progression_str, index):
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    piano = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Electric Piano 1'))
    
    time = 0
    for i, chord in enumerate(chords):
        delay = SWING if i % 2 == 1 else 0
        notes = staggered_chord(chord, time + delay, CHORD_DURATION)
        piano.notes.extend(notes)
        time += CHORD_DURATION

    midi.instruments.append(piano)

    prog_id = '-'.join(progression_str)
    filename = f"{key}_{index}_{prog_id}.mid".replace('/', '')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    midi.write(filepath)
    print(f"🎹 Exported: {filepath}")

def main():
    print("🎧 Available keys:", ', '.join(KEYS.keys()))
    key_input = input("Select a key (e.g. C, D#, F#): ").strip()
    while key_input not in KEYS:
        key_input = input("Invalid key. Try again (e.g. C, G#): ").strip()

    key_note = KEYS[key_input]

    try:
        count = int(input("How many progressions would you like to generate? "))
    except ValueError:
        count = 1

    for i in range(count):
        progression = random.choice(progressions)
        chords = build_progression(progression, key_note)
        create_midi(chords, BPM, key_input, progression, i)

if __name__ == "__main__":
    main()
