from pathlib import Path
from typing import List
import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack, second2tick
from app.models import Chord
from app.services.chord_db import GuitarData
from midi2audio import FluidSynth
from pydub import AudioSegment
import subprocess

TICKS_PER_BEAT = 480

def convert_chords_to_midi(chords: List[Chord], bpm: float, program: int, save_path: Path):
    guitar_data = GuitarData()
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
            if i - 1 == 0:
                # 前回のコードが先頭
                start_tick = second2tick(chords[0].time + chords[i - 1].duration, TICKS_PER_BEAT, mido.bpm2tempo(bpm))
            else:
                start_tick = second2tick(chords[i - 1].duration, TICKS_PER_BEAT, mido.bpm2tempo(bpm))
        else:
            start_tick = 0

        previous_no_chord = False
        duration_tick = second2tick(chord.duration, TICKS_PER_BEAT, mido.bpm2tempo(bpm))
        # 範囲外のコード(X)の場合
        if chord.value == 'X':
            notes = [60]
        else :
            notes = guitar_data.get_midi_notes(chord.value)
        print(f'notes:{notes}, start_tick:{start_tick}, duration_tick:{duration_tick}')
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

def match_audio_length(source_audio_path, target_audio_path, output_path):
    # 音声ファイルを読み込む
    source_audio = AudioSegment.from_file(source_audio_path)
    target_audio = AudioSegment.from_file(target_audio_path)
    
    # 音声の長さを取得（ミリ秒単位）
    source_length = len(source_audio)
    target_length = len(target_audio)
    
    # 目標の長さに合わせるため、無音を追加
    if source_length < target_length:
        # 足りない時間を無音で補う
        silence_duration = target_length - source_length
        silence = AudioSegment.silent(duration=silence_duration)
        # 無音を後ろに追加
        adjusted_audio = source_audio + silence
    else:
        # 長さが長い場合はカット
        adjusted_audio = source_audio[:target_length]
    
    # 出力ファイルに保存
    adjusted_audio.export(output_path, format="ogg")
   
def convert_midi_to_audio(midi_file_path: Path, save_path: Path):
    fs = CustomFluidSynth(sound_font='/usr/share/sounds/sf2/FluidR3_GM.sf2', sample_rate=44100, gain=1)
    fs.midi_to_audio(midi_file_path, save_path)
            