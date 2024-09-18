import json
from pathlib import Path
from allin1.typings import AnalysisResult

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