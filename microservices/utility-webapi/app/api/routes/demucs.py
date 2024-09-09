from datetime import datetime
from fastapi import APIRouter, Request, Depends
import redis.asyncio
from sse_starlette import EventSourceResponse
from app.api.deps import get_asyncio_redis_conn
from app.core.heavy_job import HeavyJob
from app.core.config import settings

router = APIRouter()

@router.post(
    "/separate-audio"
)
def separate(request: Request, r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.DEMUCS_WEBAPI_HOST, 
        dst_api_port=settings.DEMUCS_WEBAPI_PORT
    )
    now = datetime.now()
    print(now)
    temp_file_path = "../input/soramo_toberuhazu.wav"
    request_body = {"file_path":temp_file_path}

    return EventSourceResponse(
        job_router.stream(
            request=request, 
            pubsub_channel='gpu:channel', 
            queue_name='gpu_queue',
            job_timeout=settings.DEMUCS_WEBAPI_SEPARATE_JOB_TIMEOUT,
            request_path='/',
            request_body=request_body,
            request_connect_timeout=settings.DEMUCS_WEBAPI_CONNECT_TIMEOUT,
            request_read_timeout=settings.DEMUCS_WEBAPI_READ_TIMEOUT
        )
    )