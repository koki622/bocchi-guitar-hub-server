import json
from pathlib import Path
from allin1.typings import AnalysisResult, Segment
from pydub import AudioSegment
import librosa
import numpy as np
import soundfile as sf

def adjust_segments_to_beat(beats: list[int], segments: list[Segment]) -> Segment:
    # ビートのリストをnumpy配列に変換
    beats = np.array(beats)

    # セグメントのstartとendを最寄りのビートに補正
    for segment in segments:
        if segment.label == 'start':
            # "start"ラベルの場合、startは0に固定し、endは最寄りのビートに補正
            segment.start = 0
            segment.end = beats[np.abs(beats - segment.end).argmin()]
        else:
            # その他のラベルの場合、startとendを最寄りのビートに補正
            segment.start = beats[np.abs(beats - segment.start).argmin()]
            segment.end = beats[np.abs(beats - segment.end).argmin()]
    return segments

def analysis_result_to_json(result: AnalysisResult, save_dir: Path):
    data = {
        'bpm': result.bpm,
        'beats': result.beats,
        'downbeats': result.downbeats,
        'beat_positions': result.beat_positions,
        'segments': [{
                'start': seg.start,
                'end': seg.end,
                'label': seg.label
            } for seg in result.segments]
    }

    with open(save_dir / 'structure.json', 'w') as f:
        json.dump(data, f)

def generate_click_sound(result: AnalysisResult, length: int, save_dir: Path):
    downbeats = np.asarray(result.downbeats)
    beats = np.asarray(result.beats)
    dists = np.abs(downbeats[:, np.newaxis] - beats).min(axis=0)
    beats = beats[dists > 0.03]

    clicks_beat = librosa.clicks(
    times=beats,
    sr=44100,
    click_freq=1500,
    click_duration=0.1,
    length=length
    )
    # 通常の速さのビートのクリック音
    clicks_beat = librosa.clicks(
        times=beats,
        sr=44100,
        click_freq=1500,
        click_duration=0.1,
        length=length
    )
    
    # 通常の速さのダウンビートのクリック音
    clicks_downbeat = librosa.clicks(
        times=downbeats,
        sr=44100,
        click_freq=3000,
        click_duration=0.1,
        length=length
    )

    # 2倍速のビートのクリック音
    beats_2x = beats / 2  # ビートのタイミングを半分にすることで2倍速に
    clicks_beat_2x = librosa.clicks(
        times=beats_2x,
        sr=44100,
        click_freq=1500,
        click_duration=0.1,
        length=length
    )
    
    # 2倍速のダウンビートのクリック音
    downbeats_2x = downbeats / 2  # ダウンビートのタイミングを半分にすることで2倍速に
    clicks_downbeat_2x = librosa.clicks(
        times=downbeats_2x,
        sr=44100,
        click_freq=3000,
        click_duration=0.1,
        length=length
    )
    
    # 半分速のビートのクリック音
    beats_half = beats * 2  # ビートのタイミングを2倍にすることで半分速に
    clicks_beat_half = librosa.clicks(
        times=beats_half,
        sr=44100,
        click_freq=1500,
        click_duration=0.1,
        length=length
    )

    # 半分速のダウンビートのクリック音
    downbeats_half = downbeats * 2  # ダウンビートのタイミングを2倍にすることで半分速に
    clicks_downbeat_half = librosa.clicks(
        times=downbeats_half,
        sr=44100,
        click_freq=3000,
        click_duration=0.1,
        length=length
    )

    # 各速度のクリック音を個別に保存
    wav_path_normal = save_dir / 'clicks_normal.wav'
    sf.write(wav_path_normal, clicks_beat + clicks_downbeat, 44100)
    
    wav_path_2x = save_dir / 'clicks_2x.wav'
    sf.write(wav_path_2x, clicks_beat_2x + clicks_downbeat_2x, 44100)

    wav_path_half = save_dir / 'clicks_half.wav'
    sf.write(wav_path_half, clicks_beat_half + clicks_downbeat_half, 44100)

    # mp3形式に変換して保存
    mp3_path_normal = save_dir / 'clicks_normal.mp3'
    AudioSegment.from_wav(wav_path_normal).export(mp3_path_normal, format='mp3')

    mp3_path_2x = save_dir / 'clicks_2x.mp3'
    AudioSegment.from_wav(wav_path_2x).export(mp3_path_2x, format='mp3')

    mp3_path_half = save_dir / 'clicks_half.mp3'
    AudioSegment.from_wav(wav_path_half).export(mp3_path_half, format='mp3')


def analysis_result_to_sonic_visualizer(result: AnalysisResult, save_dir: Path):
    def write_beats(beats, beat_positions, output_file):
        with open(output_file, 'w') as f:
            for beat, position in zip(beats, beat_positions):
                f.write(f'{beat}\t{position}\n')
    
    def write_segments(segments, output_file):
        with open(output_file, 'w') as f:
            for segment in segments:
                f.write(f"{segment.start}\t{segment.end}\t{segment.label}\n")
    
    beats = result.beats
    beat_positions = result.beat_positions
    segments = result.segments
    
    write_beats(beats, beat_positions, save_dir / 'beats.txt')
    write_segments(segments, save_dir / 'segments.txt')