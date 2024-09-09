from datetime import datetime
from contextlib import asynccontextmanager
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
    # fileの拡張子を取得
    #file_extention = os.path.splitext(file.filename)[1]
    file_path = body.file_path
    now = datetime.now()
    print(f"処理開始:{now}")
    """
    with NamedTemporaryFile(delete=True, dir="../input", suffix=file_extention) as t:
        temp_file_path = t.name
        shutil.copyfileobj(file.file, t)

        jam = analyze(filename=temp_file_path)
    """
    jam = analyze(filename=file_path)
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time}