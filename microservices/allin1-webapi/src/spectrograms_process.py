from datetime import datetime
import os
from pathlib import Path
import sys
from allin1.spectrogram import extract_spectrograms

def ext_spectrograms(separated_path: str):
    separated_path = Path(separated_path)
    save_path = separated_path.parent
    extract_spectrograms([separated_path], save_path, True)
    print('スペクトログラム抽出が完了')
    os.rename(separated_path.parent / 'separated.npy', separated_path.parent / 'spectrograms.npy')
    end_time = datetime.now()
    return {"end":end_time}

if __name__ == '__main__':
    separated_path = sys.argv[1]

    result = ext_spectrograms(separated_path=separated_path)