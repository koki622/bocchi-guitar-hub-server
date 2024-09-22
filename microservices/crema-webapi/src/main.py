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
    json_result = []
    csv_result = []
    csv_header = ['Time', 'Duration', 'Value']
    annotations = jam.search(namespace='chord')
    for annotation in annotations:
        for obs in annotation.data:
            result_dict = {
                'Time': round(obs.time, 2),
                'Duration': round(obs.duration, 2),
                'Value': obs.value
            }
            json_result.append(result_dict)
            row = [
                obs.time,
                obs.duration,
                obs.value
            ]
            csv_result.append(row)

    with open(Path(file_path).parent / 'chord.json', 'w', encoding='utf-8') as f:
        json.dump(json_result, f)

    with open(Path(file_path).parent / 'chord.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        # ヘッダーを書き込む
        writer.writerow(csv_header)
        # データを書き込む
        writer.writerows(csv_result)

    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time}