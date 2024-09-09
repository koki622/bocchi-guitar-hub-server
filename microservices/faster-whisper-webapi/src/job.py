import whisper
from datetime import datetime

def init_whisper():
    global __model
    __model = whisper.load_model("large-v2")

def task_whisper(file_path: str):
    __model.transcribe(file_path, verbose=True, language="ja")
    return datetime.now()