from datetime import datetime
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.api.deps import get_asyncio_redis_conn, get_audiofile_path
from app.core.heavy_job import HeavyJob
from app.core.config import settings

router = APIRouter()

@router.post("/lyric")
def analyze_lyric(request: Request, audiofile_path: Path = Depends(get_audiofile_path), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.WHISPER_WEBAPI_HOST, 
        dst_api_port=settings.WHISPER_WEBAPI_PORT
    )
    now = datetime.now()
    print(now)
    
    if os.path.exists(audiofile_path.parent / 'lyric.txt'):
        raise HTTPException(
            status_code=400,
            detail='既に歌詞解析がされています。'
        )
    if not os.path.exists(audiofile_path.parent / 'separated'):
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が見つかりませんでした。解析には音声の分離結果が必要です。'
        )
    request_body = {'file_path': str(audiofile_path.parent / 'separated' / 'vocals.wav')}
    return EventSourceResponse(
        job_router.stream(
            request=request, 
            queue_name='gpu_queue',
            job_timeout=settings.WHISPER_WEBAPI_JOB_TIMEOUT,
            request_path='/',
            request_body=request_body,
            request_connect_timeout=settings.WHISPER_WEBAPI_CONNECT_TIMEOUT,
            request_read_timeout=settings.WHISPER_WEBAPI_READ_TIMEOUT
        )
    )

@router.get('/lyric')
def response_lyric(audiofile_path: Path = Depends(get_audiofile_path)):
    with open(audiofile_path.parent / 'lyric.txt') as f:
        return json.load(f)