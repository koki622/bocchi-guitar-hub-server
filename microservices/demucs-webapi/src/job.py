import demucs.api
from datetime import datetime

def init_demucs():
    global __separator
    __separator = demucs.api.Separator(model="htdemucs_6s")

def task_demucs(file_path: str):
    __separator.separate_audio_file(file_path)
    return datetime.now()