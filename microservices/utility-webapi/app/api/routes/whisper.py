from datetime import datetime
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.api.deps import get_asyncio_redis_conn, get_audiofile
from app.core.heavy_job import HeavyJob
from app.core.config import settings
from app.models import Audiofile

router = APIRouter()

@router.post("/lyric/{audiofile_id}")
def analyze_lyric(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.whisper_webapi.host,
        dst_api_port=settings.whisper_webapi.port,
        dst_api_connect_timeout=settings.whisper_webapi.connect_timeout
    )
    now = datetime.now()
    print(now)
    
    if os.path.exists(audiofile.audiofile_directory / 'lyric.txt'):
        raise HTTPException(
            status_code=400,
            detail='既に歌詞解析がされています。'
        )
    if not os.path.exists(audiofile.audiofile_directory / 'separated'):
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が見つかりませんでした。解析には音声の分離結果が必要です。'
        )
    
    file_path = str(audiofile.audiofile_directory / 'separated' / 'vocals.wav')
    request_body = {'file_path': file_path}
    return EventSourceResponse(
        job_router.stream(
            request=request, 
            queue_name=settings.whisper_webapi_job.queue,
            job_timeout=settings.whisper_webapi_job.timeout,
            request_path='/',
            request_body=request_body,
            request_read_timeout=settings.whisper_webapi_job.read_timeout
        )
    )

@router.get('/lyric/{audiofile_id}')
def response_lyric(audiofile: Audiofile = Depends(get_audiofile)):
    with open(audiofile.audiofile_directory / 'lyric.txt') as f:
        return json.load(f)