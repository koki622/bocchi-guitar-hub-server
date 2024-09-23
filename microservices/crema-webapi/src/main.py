import csv
from datetime import datetime
from contextlib import asynccontextmanager
import json
from pathlib import Path
from typing import Annotated
from crema.analyze import analyze, _load_models
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, File, UploadFile
import shutil
import os

from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    now = datetime.now()
    print(f"モデルロード開始:{now}")
    _load_models
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    yield

app = FastAPI(lifespan=lifespan)

class FilePathBody(BaseModel):
    file_path: str
    
@app.get("/")
def read_root():
    jam = analyze(filename='../input/soramo_toberuhazu.wav')
    print(jam)
    return(jam)

@app.post("/")
def analyze_chord(body: FilePathBody):
    file_path = body.file_path
    now = datetime.now()
    print(f"処理開始:{now}")
    
    jam = analyze(filename=file_path)
    json_result = {'chords': []}
    
    annotations = jam.search(namespace='chord')
    for annotation in annotations:
        for obs in annotation.data:
            result_dict = {
                'time': round(obs.time, 2),
                'duration': round(obs.duration, 2),
                'value': obs.value
            }
            json_result['chords'].append(result_dict)
    save_dir = Path(file_path).parent / 'chord'
    save_dir.mkdir()        
    with open(save_dir / 'chord.json', 'w', encoding='utf-8') as f:
        json.dump(json_result, f)

    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time}