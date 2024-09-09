from typing import Annotated
from crema.analyze import analyze
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, File, UploadFile
import shutil
import os

app = FastAPI()

@app.get("/")
def read_root():
    jam = analyze(filename='/workspaces/crema-webapi/input/soramo_toberuhazu.wav')
    print(jam)
    return(jam)

@app.post("/")
def analyze_chord(file: UploadFile):
    # fileの拡張子を取得
    file_extention = os.path.splitext(file.filename)[1]

    with NamedTemporaryFile(delete=True, dir="../input", suffix=file_extention) as t:
        temp_file_path = t.name
        shutil.copyfileobj(file.file, t)

        jam = analyze(filename=temp_file_path)
    return (jam)