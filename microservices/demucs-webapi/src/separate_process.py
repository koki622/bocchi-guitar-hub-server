from datetime import datetime
from pathlib import Path
import sys
from pydub import AudioSegment
import demucs.api


def separate(model_name: str, file_path: str, save_dir_path: str):
    separator = demucs.api.Separator(model=model_name, progress=True)
    file_path = Path(file_path)
    origin, separated = separator.separate_audio_file(file_path)
    print('分離処理が完了')
    save_dir_path: Path = Path(save_dir_path)
    save_dir_path.mkdir()

    for stem, source in separated.items():
        if stem == 'other': stem = 'other_6s'
        demucs.api.save_audio(source, save_dir_path / f'{stem}.wav', separator.samplerate)
    
    # ピアノ、ギター、その他パートの音声を重ねてother.wavを生成する
    combined = AudioSegment.from_wav(save_dir_path / 'other_6s.wav')
    for file_name in ['piano.wav', 'guitar.wav']:
            audio = AudioSegment.from_wav(save_dir_path / file_name)
            # 音声を重ねる
            combined = combined.overlay(audio)

    combined.export(save_dir_path / 'other.wav', format='wav')

    end_time = datetime.now
    return {"end":end_time}    

if __name__ == "__main__":
     model_name = sys.argv[1]
     file_path = sys.argv[2]
     save_dir_path = sys.argv[3]

     separate(model_name=model_name, file_path=file_path, save_dir_path=save_dir_path)