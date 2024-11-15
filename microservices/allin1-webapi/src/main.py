from datetime import datetime
import os
from pathlib import Path
from pydantic import BaseModel
import torch
from .utility import adjust_segments_to_beat, analysis_result_to_json, generate_click_sound
from allin1.models.loaders import load_pretrained_model
from allin1.spectrogram import extract_spectrograms
from contextlib import asynccontextmanager
from fastapi import FastAPI
import demucs.separate
from allin1.helpers import (
  run_inference
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("modelロードします")
    model = load_pretrained_model(device='cuda' if torch.cuda.is_available() else 'cpu') # model_nameにharmonix-allを使用するとlemonの最初の部分のビートがうまく認識されなかった
    print("modelロード完了")
    yield
    print("shutdown")

app = FastAPI(lifespan=lifespan)

class SpectrogramsCreateBody(BaseModel):
    separated_path: str

class StructureCreateBody(BaseModel):
    file_path: str
    spectrograms_path: str

@app.post("/spectrograms")
def ext_spectrograms(body: SpectrogramsCreateBody):
    separated_path = Path(body.separated_path)
    save_path = separated_path.parent
    now = datetime.now()
    print(f"処理開始:{now}")
    extract_spectrograms([separated_path], save_path, True)
    os.rename(separated_path.parent / 'separated.npy', separated_path.parent / 'spectrograms.npy')
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")

    return {"end":end_time}

@app.post("/structure")
def analyze_structure(body: StructureCreateBody):
    file_path = Path(body.file_path)
    spec_path = Path(body.spectrograms_path)
    now = datetime.now()
    print(f"処理開始:{now}")
    
    with torch.no_grad():
        result = run_inference(
            path=file_path,
            spec_path=spec_path,
            model=model,
            device='cuda' if torch.cuda.is_available() else 'cpu',
            include_activations=False,
            include_embeddings=False
        )
    save_dir = Path(file_path.parent / 'structure')
    save_dir.mkdir()

    # 曲のセクションのタイミングをビートに補正
    result.segments = adjust_segments_to_beat(result.beats, result.segments)

    # 結果をjsonとして保存
    analysis_result_to_json(result, save_dir)

    y = demucs.separate.load_track(file_path, 2, 44100).numpy()
    length = y.shape[-1]
    # ビートの結果からクリック音を生成
    generate_click_sound(result, length, save_dir)
    
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time}