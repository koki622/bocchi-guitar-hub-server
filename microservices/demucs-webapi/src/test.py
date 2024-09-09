import json
import threading
from fastapi import FastAPI, UploadFile, Request
from tempfile import NamedTemporaryFile
from contextlib import asynccontextmanager
import tempfile
import demucs.api
import shutil
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import torch
from rq import Queue
from redis import Redis
import subprocess
import job

#separator = None
r = Redis(host="redis", port=6379)
queue = Queue("gpu_queue", connection=r)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model
    #global separator
    #separator = demucs.api.Separator(model="htdemucs_6s")
    job.init_demucs()
    subprocess.Popen(["python3", "test_queue.py"])
    yield
    print("shutdown")
    
app = FastAPI(lifespan=lifespan)

#def task_demucs(file_path: str, separator: demucs.api.Separator):
"""
def task_demucs(file_path: str):
    separator.separate_audio_file(file_path)
    return datetime.now()
"""


def process_file(file_path: str):
    try:
        yield "event: 処理始めるよ\n\n"
        #job = queue.enqueue(task_demucs, file_path, separator, meta={"task_type": "demucs"})
        task = queue.enqueue("job.task_demucs", file_path, meta={"task_type": "demucs"})
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



@app.post("/")
def separate(file: UploadFile, request: Request) -> EventSourceResponse:
    client_ip = request.client.count(3)
    now = datetime.now()
    print(now)
    temp_file_path = "../input/tmp_h_36xlm.wav"
    """
    # fileの拡張子を取得
    file_extention = os.path.splitext(file.filename)[1]
    file_content = file.read()
    with NamedTemporaryFile(delete=False, dir="../input", suffix=file_extention) as t:
        temp_file_path = t.name
        t.write(file_content)
    """
    
    return EventSourceResponse(
        process_file(temp_file_path)
    )
    
    #return StreamingResponse(process_file(temp_file_path), media_type="text/event-stream")
    
    # fileの拡張子を取得
    file_extention = os.path.splitext(file.filename)[1]

    with NamedTemporaryFile(delete=True, dir="../input", suffix=file_extention) as t:
        temp_file_path = t.name
        shutil.copyfileobj(file.file, t)
        """
        async with cuda_lock:  # CUDAデバイスへのアクセスを制御
            try :
                torch.cuda.synchronize()
                origin, separated = separator.separate_audio_file(temp_file_path)
            finally :
                now1 = datetime.now()
                torch.cuda.empty_cache()
        """
        separator.separate_audio_file(temp_file_path)
        now1 = datetime.now()
        #now1 = await asyncio.get_event_loop().run_in_executor(executor, test, temp_file_path)

    print(f"{client_ip}:{now}~{now1}")
    #temp_directory_path = tempfile.mkdtemp(dir="../output")
   
    #print(separated.keys)
    """
    print(f"separated{separated}")

    for a, b in separated.items():
        print(f"a{a}")
        print(f"b{b}")
    """
        #demucs.api.save_audio(b, f"{temp_directory_path}/{a}_{file.filename}", separator.samplerate)

        
    #return temp_directory_path
    return (f"{client_ip}{now}~{now1}")