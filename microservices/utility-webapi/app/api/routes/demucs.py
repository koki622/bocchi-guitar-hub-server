from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from fastapi.responses import FileResponse
import redis.asyncio
import os
import shutil
import tempfile
from pydub import AudioSegment
from sse_starlette import EventSourceResponse
from app.api.deps import get_asyncio_redis_conn, get_audiofile
from app.core.heavy_job import HeavyJob
from app.core.config import settings
from app.models import Audiofile

router = APIRouter()

@router.post("/separated-audio/{audiofile_id}")
def separate(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.DEMUCS_WEBAPI_HOST, 
        dst_api_port=settings.DEMUCS_WEBAPI_PORT
    )
    now = datetime.now()
    print(now)
    
    if os.path.exists(audiofile.audiofile_directory / 'separated'):
        raise HTTPException(
            status_code=400,
            detail='既に音声の分離がされています。'
        )
    request_body = {'file_path': str(audiofile.audiofile_path)}
    return EventSourceResponse(
        job_router.stream(
            request=request, 
            queue_name='gpu_queue',
            job_timeout=settings.DEMUCS_WEBAPI_JOB_TIMEOUT,
            request_path='/',
            request_body=request_body,
            request_connect_timeout=settings.DEMUCS_WEBAPI_CONNECT_TIMEOUT,
            request_read_timeout=settings.DEMUCS_WEBAPI_READ_TIMEOUT
        )
    )

@router.get('/separated-audio/{audiofile_id}')
def response_separated_audio(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)):
    separated_path = audiofile.audiofile_directory / 'separated'
    separated_zip_path = audiofile.audiofile_directory / 'separated.zip'
    if os.path.exists(separated_zip_path):
        return FileResponse(
            path=separated_zip_path, 
            media_type='application/zip', 
            headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_separated.zip'}
        )
    elif os.path.exists(separated_path):
        job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host='localhost', 
        dst_api_port=8000
        )
    
        return EventSourceResponse(
            job_router.stream(
                request=request, 
                queue_name='cpu_queue',
                job_timeout=60,
                request_path=f'/demucs/separated-audio/{audiofile.audiofile_id}/zip',
                request_headers={settings.HTTP_HEADER_CONSUMER_ID:audiofile.consumer_id},
                request_connect_timeout=3,
                request_read_timeout=60
            )
        )
        
    else:
        raise HTTPException(
            status_code=400,
            detail='音声の分離が完了していません。'
        )

@router.delete('/separated-audio/{audiofile_id}')
def delete_separated_audio(audiofile: Audiofile = Depends(get_audiofile)):
    delete_count = 0
    if os.path.exists(audiofile.audiofile_directory / 'separated'):
        shutil.rmtree(audiofile.audiofile_directory / 'separated')
        delete_count += 1
    if os.path.exists(audiofile.audiofile_directory / 'separated.zip'):
        os.remove(audiofile.audiofile_directory / 'separated.zip')
        delete_count += 1
    if delete_count == 0:
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が存在しません。'
        )
    return('ok')

@router.post('/separated-audio/{audiofile_id}/zip', description='内部処理用のため非公開。処理結果をZIP圧縮する。')
def zip_separated_audio(request: Request, audiofile: Audiofile = Depends(get_audiofile)) -> EventSourceResponse:
    if '127.0.0.1' != request.client[0]:
        raise HTTPException(
            status_code=404,
            detail='Not Found.'
        )
    separated_path = audiofile.audiofile_directory / 'separated'
    with tempfile.TemporaryDirectory() as tmp_dir:
            for f in os.listdir(separated_path):
                wav_audio = AudioSegment.from_wav(separated_path / f)
                wav_audio.export(Path(tmp_dir) / (Path(f).stem + '.mp3'), format='mp3')
            shutil.make_archive(separated_path, 'zip', tmp_dir)
    return 'ok'