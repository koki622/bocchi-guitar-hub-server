from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager
import demucs.api
from datetime import datetime
from pydantic import BaseModel

separator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model
    global separator
    separator = demucs.api.Separator(model="htdemucs_6s", progress=True)
    yield
    print("shutdown")
    
app = FastAPI(lifespan=lifespan)

class FilePathBody(BaseModel):
    file_path: str


@app.post("/")
def separate(body: FilePathBody):
    file_path = body.file_path
    save_dir_path = Path(file_path).parent / 'separated'
    save_dir_path.mkdir()
    now = datetime.now()
    print(f"処理開始:{now}")
    origin, separated = separator.separate_audio_file(file_path)
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    
    for stem, source in separated.items():
        if stem == 'other': stem = 'other_6s'
        demucs.api.save_audio(source, save_dir_path / f'{stem}.wav', separator.samplerate)

    return {"end":end_time}    