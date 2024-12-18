import json
import os
from pathlib import Path
from typing import List
from pychord import Chord as pychord, utils as pychord_utils

# Cremaが出力したコード名のキーをコードDBで扱える形式に変換
SHORTHAND_TO_KEY_MAP = {
    'C': 'C',
    'C#': 'C#',
    'D': 'D',
    'D#': 'D#',
    'E': 'E',
    'F': 'F',
    'F#': 'F#',
    'G': 'G',
    'G#': 'G#',
    'A': 'A',
    'A#': 'A#',
    'B': 'B',
}

# Cremaが出力したコード名のサフィックスをコードDBで扱える形式に変換
SHORTHAND_TO_SUFFIX_MAP = {
    "maj": "",
    "min": "m",
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

# Cremaが出力したコード名のサフィックスをPychordで扱える形式に変換
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

# 分数コードの/より左側の部分をコードDB形式に変換するためのマップ
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

# REVERSAL_SUFFIX_MAPを分数コードじゃない普通のサフィックスに変換
REVERSAL_SUFFIX_TO_NORMAL_SUFFIX_MAP = {
    '': "major",
    'm': "minor",
    "dim": "dim",
    "dim7": "dim7",
    "aug": "aug",
    "7": "7",
    "m7b5": "m7b5",  
    "m7": "m7",
    "maj7": "maj7",
    "mmaj7": "mmaj7",
    "6": "6",
    "m6": "m6",
    "9": "9",
    "maj9": "maj9",
    "m9": "m9",
    "sus4": "sus4",
    "sus2": "sus2",
}

GUITAR_CHORD_DB_JSON_PATH = Path(os.path.dirname(__file__), '..', 'assets', 'chords.json')

class GuitarData:
    def __init__(self):
        # JSONファイルを開いてロード
        with open(GUITAR_CHORD_DB_JSON_PATH, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        self.chord_index = raw_data

    def _convert_to_correct_reversal(self, key: str, suffix: str) -> str:
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
        base_suffix, root_interval = suffix.split('/') # maj/3だったら maj, 3
        # pychordが認識できるsuffixに変換
        pychord_base_suffix = SHORTHAND_TO_PYCHORD_SUFFIX_MAP[base_suffix]

        if 'b' in root_interval or '#' in root_interval:
            # 分数コードの右側にbや#が含まれる場合
            accidentals = None
            if 'b' in root_interval:
                accidentals = 'b'
            elif '#' in root_interval:
                accidentals = '#'
            replaced_root_interval = root_interval.replace(accidentals, '')
            
            reversal = CHORD_REVERSALS_MAP[base_suffix][int(replaced_root_interval)]
            c = pychord(key + pychord_base_suffix + '/' + str(reversal))
            if accidentals == '#':
                root_note = pychord_utils.transpose_note(c.components()[0], 1)
            elif accidentals == 'b':
                root_note = pychord_utils.transpose_note(c.components()[0], -1)
        else:
            # 第n転回形形式に変換
            reversal = CHORD_REVERSALS_MAP[base_suffix][int(root_interval)]
            c = pychord(key + pychord_base_suffix + '/' + str(reversal))

            # ルート音
            root_note = c.components()[0]

        # suffixを上書き
        suffix = REVERSAL_SUFFIX_MAP[base_suffix] + '/' + root_note
        return suffix
    
    def convert_shorthand_to_chords_json_format(self, chord_name: str) -> str:
        """Cremaが出力するコード名の形式を'chords.json'の形式に変換

        Args:
            chord_name (str): Cremaが出力したコード名

        Returns:
            str: 'chords.json'のキーとして扱えるコード名
        """
        if chord_name in ('N', 'X'):
            return chord_name
        
        key_suffix = chord_name.split(':')
        key = key_suffix[0]
        suffix = key_suffix[1]
    
        if "/" in suffix:
            # 分数コードであれば第n転回形式に変換
         
            suffix = self._convert_to_correct_reversal(key, suffix)
        else:
            suffix = SHORTHAND_TO_SUFFIX_MAP[suffix]
        key = SHORTHAND_TO_KEY_MAP[key]
        return key + suffix

    def get_chord_info(self, chord_name) -> any:
        try:
            # 該当するコードの先頭の情報を返す
            return self.chord_index[chord_name][0]
        except (KeyError, IndexError):
            # 該当なしの場合はNone を返す
            return None
        
    def get_midi_notes(self, shorthand_chord_name: str) -> List[int]:
        """Cremaの出力結果のコード名からmidiのノートを取得

        Args:
            shorthand_chord_name (str): Cremaが出力したコード名

        Returns:
            List[int]: midiノート
        """
        STANDARTD_TUNING_OPEN_STRINGS_NOTE = {
            6: 40,
            5: 45,
            4: 50,
            3: 55,
            2: 59,
            1: 64,
        }
        converted_chord_name = self.convert_shorthand_to_chords_json_format(shorthand_chord_name)
        chord_info = self.get_chord_info(converted_chord_name)
        midi_notes = []
        if chord_info is None:
            return [60]
        else:
            for index, position in enumerate(chord_info['positions']):
                if position != 'x':
                    midi_notes.append(STANDARTD_TUNING_OPEN_STRINGS_NOTE[6 - index] + int(position))
            return midi_notes