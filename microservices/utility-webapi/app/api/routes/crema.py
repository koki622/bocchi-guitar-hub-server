from datetime import datetime
import json
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.api.deps import get_asyncio_redis_conn, get_audiofile
from app.core.heavy_job import HeavyJob
from app.models import Audiofile
from app.core.config import settings

router = APIRouter()

@router.post("/chord/{audiofile_id}")
def analyze_chord(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.CREMA_WEBAPI_HOST, 
        dst_api_port=settings.CREMA_WEBAPI_PORT
    )
    now = datetime.now()
    print(now)

    if os.path.exists(audiofile.audiofile_directory / 'chord.json'):
        raise HTTPException(
            status_code=400,
            detail='既にコード進行の解析がされています。'
        )
    
    request_body = {'file_path': str(audiofile.audiofile_path)}
    return EventSourceResponse(
        job_router.stream(
            request=request, 
            queue_name='cpu_queue',
            job_timeout=settings.CREMA_WEBAPI_JOB_TIMEOUT,
            request_path='/',
            request_body=request_body,
            request_connect_timeout=settings.CREMA_WEBAPI_CONNECT_TIMEOUT,
            request_read_timeout=settings.CREMA_WEBAPI_READ_TIMEOUT    
        )
    )

@router.post('/chord/{audiofile_id}/adjusted')
def adjust_chord_timing(request: Request, audiofile: Audiofile = Depends(get_audiofile)):
    if not os.path.exists(audiofile.audiofile_directory / 'chord.json'):
        raise HTTPException(
            status_code=400,
            detail='コード進行の解析結果が見つかりませんでした。'
        )
    
    if not os.path.exists(audiofile.audiofile_directory / 'beat.txt'):
        raise HTTPException(
            status_code=400,
            detail='ビートの解析結果が見つかりませんでした。'
        )

@router.get('/chord/{audiofile_id}')
def response_lyric(audiofile: Audiofile = Depends(get_audiofile), download: bool = False, download_file_format: Literal['json', 'csv'] = 'json'):
    try:
        if download:
            return FileResponse(
                path=audiofile.audiofile_directory / f'chord.{download_file_format}',
                headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_chord.{download_file_format}'}
            )
        else:
            with open(audiofile.audiofile_directory / 'chord.json') as f:
                return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail='コード進行の解析結果が見つかりませんでした。'
        )