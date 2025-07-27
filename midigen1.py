import pretty_midi
import random
import os
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Config:
    chord_duration: float = 1.0
    swing: float = 0.04
    output_dir: str = 'midi_exports'
    default_bpm: int = 85
    keys: Dict[str, int] = None
    progressions: List[List[str]] = None
    chords: Dict[str, List[int]] = None

def default_config() -> Config:
    return Config(
        keys={
            'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65,
            'F#': 66, 'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71
        },
        progressions=[
            ['Imaj7', 'vi7', 'IVmaj7', 'V7'],
            ['ii7', 'V7', 'Imaj7', 'Imaj7'],
            ['I', 'IV', 'I', 'V'],
            ['I', 'V', 'vi', 'IV'],
            ['Imaj7', 'iii7', 'vi7', 'IVmaj7']
        ],
        chords={
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
    )

def get_chord_notes(root_note: int, intervals: List[int]) -> List[int]:
    """
    Build chord notes with possible random inversion and bass doubling.
    """
    chord = [root_note + i for i in intervals]

    if len(chord) >= 3 and random.random() < 0.6:
        inversion = random.randint(0, len(chord) - 2)
        chord = chord[inversion:] + [n + 12 for n in chord[:inversion]]

    if random.random() < 0.3:
        chord = [chord[0] - 12] + chord

    return chord

def staggered_chord(chord: List[int], start_time: float, duration: float, roll_strength: float = 0.04) -> List[pretty_midi.Note]:
    """
    Create notes for a chord with slight timing offsets for realism.
    """
    notes = []
    for i, pitch in enumerate(chord):
        velocity = random.randint(68, 92)
        note_start = start_time + (i * roll_strength if i > 0 else 0)
        note_end = start_time + duration
        note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=note_start, end=note_end)
        notes.append(note)
    return notes

def generate_melody(chords: List[List[int]], start_time: float, chord_duration: float, note_length: float = 0.5, swing_amount: float = 0.02) -> List[pretty_midi.Note]:
    """
    Generate a simple melodic line based on chord tones with timing variations.
    """
    melody_notes = []
    t = start_time
    for chord in chords:
        if len(chord) > 1:
            melody_note = random.choice(chord[1:]) + 12  # melody an octave higher, avoid root
        else:
            melody_note = chord[0] + 12

        velocity = random.randint(75, 100)
        delay = random.uniform(-swing_amount, swing_amount)
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=melody_note,
            start=t + delay,
            end=t + delay + note_length
        )
        melody_notes.append(note)
        t += chord_duration

    return melody_notes

def build_progression(prog: List[str], key_note: int, chords_dict: Dict[str, List[int]]) -> List[List[int]]:
    """
    Convert chord progression degrees to MIDI note lists.
    """
    return [get_chord_notes(key_note, chords_dict[d]) for d in prog]

def create_midi_file(
    chords: List[List[int]],
    bpm: int,
    key: str,
    progression: List[str],
    index: int,
    add_melody: bool,
    config: Config
) -> str:
    """
    Create and save a MIDI file with optional melody.
    Returns the file path.
    """
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)

    piano_program = pretty_midi.instrument_name_to_program('Electric Piano 1')
    piano = pretty_midi.Instrument(program=piano_program)

    time_cursor = 0.0
    for i, chord in enumerate(chords):
        delay = config.swing if i % 2 == 1 else 0.0
        notes = staggered_chord(chord, time_cursor + delay, config.chord_duration)
        piano.notes.extend(notes)
        time_cursor += config.chord_duration
    midi.instruments.append(piano)

    if add_melody:
        melody_program = pretty_midi.instrument_name_to_program('Synth Lead 1')
        lead = pretty_midi.Instrument(program=melody_program)
        lead.notes = generate_melody(chords, start_time=0.1, chord_duration=config.chord_duration)
        midi.instruments.append(lead)

    prog_str = '-'.join(progression)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"{key}_{index}_{prog_str}_{timestamp}.mid".replace('/', '')

    os.makedirs(config.output_dir, exist_ok=True)
    file_path = os.path.join(config.output_dir, filename)
    midi.write(file_path)
    logger.info(f"✅ Exported MIDI: {file_path}")
    return file_path

def select_key(keys: Dict[str, int]) -> str:
    """
    Prompt user to select a valid key.
    """
    logger.info("🎧 Available keys: " + ', '.join(keys.keys()))
    while True:
        key = input("Select a key (e.g. C, D#, F#): ").strip()
        if key in keys:
            return key
        logger.warning(f"Invalid key '{key}'. Please try again.")

def select_int(prompt: str, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """
    Prompt user to input an integer, with validation and default fallback.
    """
    while True:
        raw = input(f"{prompt} (default {default}): ").strip()
        if not raw:
            return default
        if raw.isdigit():
            val = int(raw)
            if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                logger.warning(f"Value out of range [{min_val}-{max_val}]. Try again.")
                continue
            return val
        logger.warning("Invalid number. Please enter an integer.")

def select_yes_no(prompt: str, default: bool = False) -> bool:
    """
    Prompt user for a Y/N answer.
    """
    yn_map = {'Y': True, 'N': False}
    default_char = 'Y' if default else 'N'
    while True:
        resp = input(f"{prompt} (Y/N, default {default_char}): ").strip().upper()
        if not resp:
            return default
        if resp in yn_map:
            return yn_map[resp]
        logger.warning("Invalid input. Please enter Y or N.")

def run():
    config = default_config()
    random.seed()  # or set a fixed seed for reproducibility here

    key = select_key(config.keys)
    count = select_int("How many progressions to generate?", default=1, min_val=1)
    bpm = select_int("Set BPM", default=config.default_bpm, min_val=20, max_val=300)
    add_melody = select_yes_no("Add melody on top?", default=False)

    for i in range(count):
        progression = random.choice(config.progressions)
        chords = build_progression(progression, config.keys[key], config.chords)
        create_midi_file(chords, bpm, key, progression, i, add_melody, config)

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user, exiting.")
        sys.exit(0)
