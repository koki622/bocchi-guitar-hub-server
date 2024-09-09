from datetime import datetime
import os
from pathlib import Path
from pydantic import BaseModel
import torch
from analyze import analyze
from allin1.models.loaders import load_pretrained_model
from allin1.spectrogram import extract_spectrograms
from contextlib import asynccontextmanager
from fastapi import FastAPI
from allin1.helpers import (
  run_inference
)
from distutils.dir_util import mkpath

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("modelロードします")
    model = load_pretrained_model("harmonix-all", device="cuda")
    print("modelロード完了")
    yield
    print("shutdown")

app = FastAPI(lifespan=lifespan)

class FilePathBody(BaseModel):
    file_path: str
    
@app.post("/spectrograms")
def ext_spectrograms(body: FilePathBody):
    file_path = Path(body.file_path)
    demix_paths = [file_path]
    spec_path = Path(file_path)
    now = datetime.now()
    print(f"処理開始:{now}")
    extract_spectrograms(demix_paths, file_path, True)
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    os.remove(file_path / "soramo_toberuhazu.npy")
    return {"end":end_time}

@app.post("/structure")
def analyze_structure(body: FilePathBody):
    file_path = Path(f"{body.file_path}.wav")
    spec_path = Path(f"{body.file_path}.npy")
    now = datetime.now()
    print(f"処理開始:{now}")
    with torch.no_grad():
        result = run_inference(
            path=file_path,
            spec_path=spec_path,
            model=model,
            device='cuda',
            include_activations=False,
            include_embeddings=False
        )
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time}