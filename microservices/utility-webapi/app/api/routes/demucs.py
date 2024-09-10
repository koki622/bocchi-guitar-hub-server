from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Depends
import redis.asyncio
import os
from sse_starlette import EventSourceResponse
from app.api.deps import get_asyncio_redis_conn, get_consumer_dir
from app.core.heavy_job import HeavyJob
from app.core.config import settings

router = APIRouter()

@router.post(
    "/separated-audio"
)
def separate(request: Request, dir_name: str, consumer_dir: Path = Depends(get_consumer_dir), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.DEMUCS_WEBAPI_HOST, 
        dst_api_port=settings.DEMUCS_WEBAPI_PORT
    )
    now = datetime.now()
    print(now)
    audiofile_path = consumer_dir / dir_name / (dir_name + '.wav')
    if os.path.exists(audiofile_path):
        request_body = {'file_path': str(audiofile_path)}
    else:
        raise HTTPException(
            status_code=400,
            detail='ディレクトリが存在しません'
        )
    if os.path.exists(consumer_dir / dir_name / 'separated'):
        raise HTTPException(
            status_code=400,
            detail='既に音声の分離がされています。'
        )
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