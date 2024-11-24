import json
import os
from pathlib import Path
from typing import Dict, List
import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack, second2tick
from pychord import Chord as pychord
from app.models import Chord
from midi2audio import FluidSynth
import subprocess


TICKS_PER_BEAT = 480

GUITAR_CHORD_DB_JSON_PATH = Path(os.path.dirname(__file__), '..', 'assets', 'guitar.json')

SHORTHAND_TO_SUFFIX_MAP = {
    "maj": "major",
    "min": "minor",
    "dim": "dim",
    "dim7": "dim7",
    "aug": "aug",
    "7": "7",
    "hdim7": "m7b5",  
    "min7": "m7",
    "maj7": "maj7",
    "minmaj7": "mmaj7",
    "maj6": "6",
    "min6": "m6",
    "9": "9",
    "maj9": "maj9",
    "min9": "m9",
    "sus4": "sus4",
    "sus2": "sus2",
}

SHORTHAND_TO_PYCHORD_SUFFIX_MAP = {
    "maj": "maj",
    "min": "min",
    "dim": "dim",
    "dim7": "dim7",
    "aug": "aug",
    "7": "7",
    "hdim7": "m7b5",  
    "min7": "m7",
    "maj7": "maj7",
    "minmaj7": "mmaj7",
    "maj6": "6",
    "min6": "m6",
    "9": "9",
    "maj9": "maj9",
    "min9": "m9",
    "sus4": "sus4",
    "sus2": "sus2",
}

REVERSAL_SUFFIX_MAP = {
    "maj": '',
    "min": 'm',
    "dim": "dim",
    "dim7": "dim7",
    "aug": "aug",
    "7": "7",
    "hdim7": "m7b5",  
    "min7": "m7",
    "maj7": "maj7",
    "minmaj7": "mmaj7",
    "maj6": "6",
    "min6": "m6",
    "9": "9",
    "maj9": "maj9",
    "min9": "m9",
    "sus4": "sus4",
    "sus2": "sus2",
}

CHORD_REVERSALS_MAP = {
    "maj": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
    },
    "min": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
    },
    "dim": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
    },
    "dim7": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
    },
    "aug": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
    },
    "7": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
    },
    "hdim7": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
    },
    "min7": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
    },
    "maj7": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
    },
    "minmaj7": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
    },
    "maj6": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        6: 3,   # 第三転回形: 6番目の音が最も低い
    },
    "min6": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        6: 3,   # 第三転回形: 6番目の音が最も低い
    },
    "9": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
        9: 4,   # 第四転回形: 9番目の音が最も低い
    },
    "maj9": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
        9: 4,   # 第四転回形: 9番目の音が最も低い
    },
    "min9": {
        3: 1,   # 第一転回形: 3番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
        7: 3,   # 第三転回形: 7番目の音が最も低い
        9: 4,   # 第四転回形: 9番目の音が最も低い
    },
    "sus4": {
        4: 1,   # 第一転回形: 4番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
    },
    "sus2": {
        2: 1,   # 第一転回形: 2番目の音が最も低い
        5: 2,   # 第二転回形: 5番目の音が最も低い
    }
}


class GuitarData:
    def __init__(self, json_file_path: str):
        # JSONファイルを開いてロード
        with open(json_file_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        # 必要なデータだけ抽出
        self.chords: Dict[str, Dict[str, List[int]]] = {
            key: {
                chord["suffix"]: chord["positions"][0]["midi"]  # 最初のポジションのMIDIのみ取得
                for chord in chord_list
            }
            for key, chord_list in raw_data["chords"].items()
        }

    def get_midi(self, key: str, suffix: str) -> List[int]:
        """
        指定された key と suffix から対応する MIDI を取得
        """
        if "/" in suffix:
            base_suffix, root_interval = suffix.split('/') # maj/3だったら maj, 3

            # pychordが認識できるsuffixに変換
            pychord_base_suffix = SHORTHAND_TO_PYCHORD_SUFFIX_MAP[base_suffix]

            # 第n転回形形式に変換
            reversal = CHORD_REVERSALS_MAP[base_suffix][int(root_interval)]
            c = pychord(key + pychord_base_suffix + '/' + str(reversal))

            # ルート音
            root_note = c.components()[0]

            # suffixを上書き
            suffix = REVERSAL_SUFFIX_MAP[base_suffix] + '/' + root_note
        else:
            suffix = SHORTHAND_TO_SUFFIX_MAP[suffix]
        return self.chords.get(key, {}).get(suffix, [60])

def convert_chords_to_midi(chords: List[Chord], bpm: float, program: int, save_path: Path):
    guitar_data = GuitarData(GUITAR_CHORD_DB_JSON_PATH)
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # BPM
    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # 音色設定
    track.append(Message('program_change', program=program, time=0))

    # 音の伸びを調整
    track.append(Message('control_change', channel=0, control=64, value=100))

    previous_no_chord = False
    for i, chord in enumerate(chords):
        if chord.value == 'N':
            previous_no_chord = True
            continue
        elif i == 0:
            start_tick = second2tick(chord.time, TICKS_PER_BEAT, mido.bpm2tempo(bpm))
        elif previous_no_chord:
            start_tick = second2tick(chords[i - 1].duration, TICKS_PER_BEAT, mido.bpm2tempo(bpm))
        else:
            start_tick = 0

        previous_no_chord = False
        duration_tick = second2tick(chord.duration, TICKS_PER_BEAT, mido.bpm2tempo(bpm))
        key_suffix = chord.value.split(':')
        notes = guitar_data.get_midi(key_suffix[0], key_suffix[1])

        # コードを鳴らす
        for i, note in enumerate(notes):
            if i == 0:
                track.append(Message('note_on', note=note, velocity=100, time=start_tick))
            else:
                track.append(Message('note_on', note=note, velocity=100, time=0))
        
        # コードを止める
        for i, note in enumerate(notes):
            if i == 0:
                track.append(Message('note_off', note=note, velocity=100, time=duration_tick))
            else:
                track.append(Message('note_off', note=note, velocity=100, time=0))
    
    mid.save(save_path)

# オーバライド
__all__ = ['FluidSynth']

DEFAULT_SOUND_FONT = '~/.fluidsynth/default_sound_font.sf2'
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_GAIN = 0.2

class CustomFluidSynth(FluidSynth):
    def __init__(self, sound_font=DEFAULT_SOUND_FONT, sample_rate=DEFAULT_SAMPLE_RATE, gain=DEFAULT_GAIN):
        # FluidSynthのコンストラクタを呼び出して、基本的な初期化
        super().__init__(sound_font, sample_rate)
        # gainパラメータを追加
        self.gain = gain

    def midi_to_audio(self, midi_file: str, audio_file: str, verbose=True):
        # 標準出力を抑制するオプション
        if verbose:
            stdout = None
        else:
            stdout = subprocess.DEVNULL
        
        # FluidSynthコマンドに-gオプションで音量調整を追加
        subprocess.call(
            ['fluidsynth', '-ni', '-g', str(self.gain), self.sound_font, midi_file, '-F', audio_file, '-r', str(self.sample_rate)], 
            stdout=stdout
        )

    def play_midi(self, midi_file):
        # MIDI再生時に音量調整を追加
        subprocess.call(
            ['fluidsynth', '-i', '-g', str(self.gain), self.sound_font, midi_file, '-r', str(self.sample_rate)]
        )

def convert_midi_to_audio(midi_file_path: Path, save_path: Path):
    fs = CustomFluidSynth(sound_font='/usr/share/sounds/sf2/FluidR3_GM.sf2', sample_rate=44100, gain=1)
    fs.midi_to_audio(midi_file_path, save_path)
            