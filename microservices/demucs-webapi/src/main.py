from pathlib import Path
from fastapi import FastAPI, UploadFile
from tempfile import NamedTemporaryFile
from contextlib import asynccontextmanager
import tempfile
import demucs.api
import shutil
import os
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

from fastapi.responses import FileResponse
import torch

separator = None
cuda_lock = asyncio.Lock()  # CUDAデバイス用のロックを作成

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model
    global separator
    separator = demucs.api.Separator(model="htdemucs_6s", progress=True)
    yield
    print("shutdown")
    
app = FastAPI(lifespan=lifespan)
executor = ThreadPoolExecutor()

class FilePathBody(BaseModel):
    file_path: str

async def test(temp_file_path):
    async with cuda_lock:
        try :
            torch.cuda.synchronize()
            origin, separated = separator.separate_audio_file(temp_file_path)
        finally :
            end = datetime.now()
            torch.cuda.empty_cache()
            return separated

@app.post("/")
def separate(body: FilePathBody):
    file_path = body.file_path
    save_dir_path = Path(file_path).parent / 'separated'
    save_dir_path.mkdir()
    now = datetime.now()
    print(f"処理開始:{now}")
    origin, separated = separator.separate_audio_file(file_path)
    torch.cuda.empty_cache()
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    
    for stem, source in separated.items():
        if stem == 'other': stem = 'other_6s'
        demucs.api.save_audio(source, save_dir_path / f'{stem}.wav', separator.samplerate)

    return {"end":end_time}
    """
    # fileの拡張子を取得
    file_extention = os.path.splitext(file.filename)[1]
    """
    """
    with NamedTemporaryFile(delete=True, dir="../input", suffix=file_extention) as t:
        temp_file_path = t.name
        shutil.copyfileobj(file.file, t)
    """
       
        #now1 = await test(temp_file_path)
        #now1 = await asyncio.get_event_loop().run_in_executor(executor, test, temp_file_path)

    #print(f"{now}~{now1}")
    #temp_directory_path = tempfile.mkdtemp(dir="../output")
   
    #print(separated.keys)

    #print(f"separated{separated}")
    """
    for a, b in now1.items():
        print(f"a{a}")
        print(f"b{b}")
        demucs.api.save_audio(b, f"{temp_directory_path}/{a}_{file.filename}", separator.samplerate)
    result_file_path = shutil.make_archive("result", "zip", temp_directory_path)
    return FileResponse(path=result_file_path)
    """
        
    #return temp_directory_path
    #return (f"{now}~{now1}")
    