from datetime import datetime
from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.core.heavy_job import HeavyJob

router = APIRouter()

r_asyncio = redis.asyncio.Redis(
    host='redis', 
    port=6379, 
    decode_responses=True,
    health_check_interval=10,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    socket_keepalive=True)

@router.post("/spectrograms")
def spectrograms(request: Request) -> EventSourceResponse:
    job_router = HeavyJob("allin1-webapi", 8000)
    now = datetime.now()
    print(now)
    file_path = "../input/htdemucs/soramo_toberuhazu"
    request_body = {"file_path":file_path}
    return EventSourceResponse(
        job_router.stream(
            request, 
            'cpu:channel', 
            'cpu_queue', 
            job_router, 
            'redis', 
            '6379', 
            r_asyncio, 
            request_body=request_body)
    )

@router.post("/structure")
def analyze_structure(request: Request) -> EventSourceResponse:
    job_router = HeavyJobRouter("allin1-webapi", 8000)
    now = datetime.now()
    print(now)
    file_path = "../input/soramo_toberuhazu"
    request_body = {"file_path":file_path}
    return EventSourceResponse(
        heavy_job_res(
            request, 
            'gpu:channel', 
            'gpu_queue', 
            job_router, 
            'redis', 
            '6379', 
            r_asyncio, 
            request_body=request_body)
    )