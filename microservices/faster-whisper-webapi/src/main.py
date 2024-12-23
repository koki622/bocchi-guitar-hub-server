import json
from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
from faster_whisper import WhisperModel
from datetime import datetime
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model
    print("モデルをロードします")
    whisper_model = WhisperModel(
        model_size_or_path="large-v2")
    print("モデルのロードが完了しました")
    logging.basicConfig()
    logging.getLogger("faster_whisper").setLevel(logging.DEBUG)
    yield
    print("shutdown")

app = FastAPI(lifespan=lifespan)

class FilePathBody(BaseModel):
    file_path: str

@app.post("/")
def analyze_lyric(body: FilePathBody):
    file_path = body.file_path
    now = datetime.now()
    print(now)
 
    try:
        segments, info = whisper_model.transcribe(file_path, language="ja", word_timestamps=True)
        word_results= []
        segment_results = []
        for segment in segments:
            segment_dics = {'start':segment.start,'end':segment.end,'text':segment.text}
            segment_results.append(segment_dics)
            for word in segment.words:
                print("[%.2fs -> %.2fs] %s" % (word.start, word.end, word.word))
                word_dict = {'start':word.start,'end':word.end,'text':word.word}
                word_results.append(word_dict)
        
        with open(Path(file_path).parent.parent / 'lyric.txt', 'w', encoding='utf-8') as txt:
            json.dump({'segments':segment_results, 'word':word_results}, txt)
    except Exception as e:
        print(f"エラーが発生:{e}")
        return e
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time, "result":segments}