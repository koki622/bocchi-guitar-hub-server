import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, Request
import time
import json
import subprocess
from datetime import datetime
import redis.asyncio
import redis.client
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from contextlib import asynccontextmanager
from rq import Queue
from redis import Redis
#from heavy_job_router import HeavyJobRouter
from core.heavy_job import HeavyJobRouter, heavy_job_res
from pathlib import Path
import os
import shortuuid
import shutil
from typing import Literal

r = Redis(
    host="redis", 
    port=6379)

r_asyncio = redis.asyncio.Redis(
    host='redis', 
    port=6379, 
    decode_responses=True,
    health_check_interval=10,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    socket_keepalive=True)
Pubsub_channel = Literal['gpu:channel', 'cpu:channel']
gpu_queue = Queue("gpu_queue", connection=r, default_timeout=60)
cpu_queue = Queue("cpu_queue", connection=r, default_timeout=60)
VOLUME_PATH = Path(os.getenv("CONSUMER_VOLUME_PATH"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    subprocess.Popen(["python3", "worker_gpu.py"])
    subprocess.Popen(["python3", "worker_cpu.py"])
    subprocess.Popen(["python3", "worker_cpu2.py"])
    yield

app = FastAPI(lifespan=lifespan)

async def job_reader(request: Request, channel: redis.client.PubSub, pubsub_id: str, queue_position: int = None):
    if queue_position is None:
        yield {"data": "処理しています"}
    else:
        yield {"data": f"現在のキュー:{queue_position}"}    
    while True:
        if await request.is_disconnected():
            break
        message = await channel.get_message(ignore_subscribe_messages=True)
        if message is not None:
            result, src_pubsub_id = message["data"].split(':')
            if src_pubsub_id == pubsub_id:
                break
            queue_position -= 1
            yield {"data": f"現在のキュー:{queue_position}"}
    
def pubsub_receive(url: Redis, pubsub_id: str, queue_position: int = None):
    with url.pubsub(ignore_subscribe_messages=True) as pubsub:
            pubsub.subscribe('channel:gpu')
            for message in pubsub.listen():
                if message['type'] == 'message':
                    result, src_pubsub_id = message['data'].split(':')
                    if src_pubsub_id == pubsub_id:
                        break
                    queue_position -= 1
                    yield {'data': f'現在のキュー:{queue_position}'}

def sse_response(queue: Queue, router: HeavyJobRouter, request_path: str = "/", request_body: dict = None, request_timeout: int = 30):
    url = redis.from_url(
        "redis://redis:6379?decode_responses=True",
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True)
    
    pubsub_id = shortuuid.ShortUUID().random(length=10)
    job_kwargs = {"pubsub_channel": "channel:gpu", "pubsub_id": pubsub_id, "path": request_path, "payload": request_body, "timeout": request_timeout}
    try:
        task = queue.enqueue(router.route_task, 
                            kwargs=job_kwargs)
        task_id = task.id
        yield {"data": task_id}
        queue_position = task.get_position()
        if queue_position is None:
            yield {"data": "処理しています"}
        else:
            yield {"data": f"現在のキュー:{queue_position}"}
        with url.pubsub(ignore_subscribe_messages=True) as pubsub:
            pubsub.subscribe('channel:gpu')
            for message in pubsub.listen():
                if message['type'] == 'message':
                    result, src_pubsub_id = message['data'].split(':')
                    if src_pubsub_id == pubsub_id:
                        break
                    queue_position -= 1
                    yield {'data': f'現在のキュー:{queue_position}'}
        #job_result = task.result()
        #print(job_result)
        #yield{"data": job_result}
    except asyncio.CancelledError as e:
        print("クライアントからの接続が切れました")
    except Exception as e:
        print('error')
        raise e
    finally:
        print('end')
"""
async def heavy_job_res(
    request: Request, 
    pubsub_channel: Pubsub_channel,
    queue: Queue, 
    router: HeavyJobRouter, 
    request_path: str = "/", 
    request_body: dict = None, 
    request_timeout: int = 30
):
    pubsub_url = redis.asyncio.Redis(
        host='redis',
        port=6379,
        decode_responses=True,
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True)
    
    yield ServerSentEvent('受け付けました', event='data')
    
    pubsub_id = shortuuid.ShortUUID().random(length=10)
    job_kwargs = {"pubsub_channel": pubsub_channel, "pubsub_id": pubsub_id, "path": request_path, "payload": request_body, "timeout": request_timeout}
    try:
        job_queue = queue.enqueue(router.route_task, 
                            kwargs=job_kwargs)
        job_id = job_queue.id
        yield {'data': {'task_id':job_id}}
        queue_position = job_queue.get_position()

        async with pubsub_url.pubsub() as pubsub:
            # ジョブの待ち状況を取得
            await pubsub.subscribe(pubsub_channel)
            async for message in job_reader(request, pubsub, pubsub_id, queue_position):
                yield {"data": f"{message['data']}"}
           
        while True:
            await asyncio.sleep(0.5)
            job_result = job_queue.result
            if job_result is not None:
                break
            print('Job Result is None')
        yield{'data': job_result}
    except asyncio.CancelledError as e:
        print("クライアントからの接続が切れました")
    except Exception as e:
        raise e
"""

@app.post("/audiofile")
def upload_audiofile(file: UploadFile):
    try:
        user_id = 'unknown'
        dir_name = shortuuid.ShortUUID().random(length=10)
        dir_path = Path(VOLUME_PATH / user_id / dir_name)
        dir_path.mkdir(parents=True)
        save_path = dir_path / file.filename
        with save_path.open('wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": file.filename, "save_dir_name": dir_name}
    finally:
        file.file.close()

@app.post("/demucs")
def separate(request: Request) -> EventSourceResponse:
    router = HeavyJobRouter("demucs-webapi", 8000)
    now = datetime.now()
    print(now)
    temp_file_path = "../input/soramo_toberuhazu.wav"
    request_body = {"file_path":temp_file_path}
    return EventSourceResponse(
        heavy_job_res(request, 'gpu:channel', 'gpu_queue', router, 'redis', '6379', r_asyncio, request_body=request_body)
    )
    """
    # fileの拡張子を取得
    file_extention = os.path.splitext(file.filename)[1]
    file_content = file.read()
    with NamedTemporaryFile(delete=False, dir="../input", suffix=file_extention) as t:
        temp_file_path = t.name
        t.write(file_content)
    """
    

@app.post("/whisper")
def analyzeLyric() -> EventSourceResponse:
    router = HeavyJobRouter("faster-whisper-webapi", 8001)
    now = datetime.now()
    print(now)
    temp_file_path = "../input/soramo_toberuhazu(vocal).wav"
    request_body = {"file_path":temp_file_path}
    return EventSourceResponse(
        heavy_job_res(gpu_queue, router, "/", request_body, 60)
    )

@app.post("/allin1/spectrograms")
def spectrograms() -> EventSourceResponse:
    router = HeavyJobRouter("allin1-webapi", 8003)
    now = datetime.now()
    print(now)
    file_path = "../input/htdemucs/soramo_toberuhazu"
    request_body = {"file_path":file_path}
    return EventSourceResponse(
        heavy_job_res(cpu_queue, router, "/spectrograms", request_body, 60)
    )

@app.post("/allin1/structure")
def analyze_structure() -> EventSourceResponse:
    router = HeavyJobRouter("allin1-webapi", 8003)
    now = datetime.now()
    print(now)
    file_path = "../input/soramo_toberuhazu"
    request_body = {"file_path":file_path}
    return EventSourceResponse(
        heavy_job_res(gpu_queue, router, "/structure", request_body, 60)
    )

@app.post("/crema/chord")
def analyze_chord(request: Request) -> EventSourceResponse:
    router = HeavyJobRouter("crema-webapi", 8000)
    now = datetime.now()
    print(now)
    file_path = "../input/rairakku.wav"
    request_body = {'file_path':file_path}
    return EventSourceResponse(
        heavy_job_res(request, 'cpu:channel', cpu_queue, router, "/", request_body, 60)
    )