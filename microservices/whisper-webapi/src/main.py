from fastapi import FastAPI, UploadFile
from tempfile import NamedTemporaryFile
from contextlib import asynccontextmanager
from pydantic import BaseModel
import torch
import whisper
import shutil
import os
from rq import Queue
from redis import Redis
import subprocess
import job
import time
from sse_starlette.sse import EventSourceResponse
from datetime import datetime

r = Redis(host="redis", port=6379)
queue = Queue("gpu_queue", connection=r)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model
    print("モデルをロードします")
    whisper_model = whisper.load_model(name="large-v2", in_memory=False)
    print("モデルのロードが完了しました")
    yield
    print("shutdown")

app = FastAPI(lifespan=lifespan)

class FilePathBody(BaseModel):
    file_path: str

"""
def process_file(file_path: str):
    try:
        yield "event: 処理始めるよ\n\n"
        #job = queue.enqueue(task_demucs, file_path, separator, meta={"task_type": "demucs"})
        task = queue.enqueue("job.task_whisper", file_path, meta={"task_type": "whisper"})
        result = None
        while True:
            result = task.result
            if result is None:
                queue_position = task.get_position()
                yield f"event: {queue_position}\n\n"
                time.sleep(5)
            else:
                break

        #os.remove(file_path)
        yield f"data:{str(result)}\n\n"
    except Exception as e:
        print("error")
        print(e)
"""

@app.post("/")
def analyzeLyric(body: FilePathBody):
    file_path = body.file_path
    now = datetime.now()
    print(now)
    #temp_file_path = "../input/soramo_toberuhazu(vocal).wav"
    try:
        torch.cuda.empty_cache()
        whisper_model.transcribe(file_path, verbose=True, language="ja")
    except Exception as e:
        print(f"エラーが発生:{e}")
        return e
    end_time = datetime.now()
    print(f"end:{end_time}")
    return {"end":end_time}