from dataclasses import dataclass
import json
from pathlib import Path
from typing import List

@dataclass
class Chord:
    time: float
    duration: float
    value: str

@dataclass
class AdjustedChord(Chord):
     was_adjusted: bool

def convert_to_chords(chord_dicts: List[dict]) -> List[Chord]:
    return [Chord(time=chord['Time'], duration=chord['Duration'], value=chord['Value']) for chord in chord_dicts]

def load_chords_from_json(json_path: Path) -> Chord:
    with open(json_path) as f:
            return convert_to_chords(json.load(f))