import asyncio
from pathlib import Path
from typing import Literal
import aiofiles
import aiofiles.os
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import FileResponse
import os
import shutil
import tempfile
from pydub import AudioSegment
from sse_starlette import EventSourceResponse
from app.api.deps import get_heavy_job, get_audiofile
from app.core.heavy_job import ApiJob, HeavyJob
from app.core.config import settings
from app.models import Audiofile
from app.services.audio_conversion import AudioConversionService

router = APIRouter()

MEDIA_TYPE = {
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'ogg': 'audio/ogg'
}

@router.post("/separated-audio/{audiofile_id}")
def separate(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse: 
    if os.path.exists(audiofile.audiofile_directory / 'separated'):
        raise HTTPException(
            status_code=400,
            detail='既に音声の分離がされています。'
        )
    
    request_body = {'file_path': str(audiofile.audiofile_path)}
    api_job = ApiJob(
        job_name=settings.DEMUCS_JOB_NAME,
        dst_api_url=f'http://{settings.DEMUCS_HOST}:{8000}',
        queue_name=settings.DEMUCS_JOB_QUEUE,
        request_path='/',
        job_timeout=settings.DEMUCS_JOB_TIMEOUT,
        request_body=request_body,
        request_read_timeout=settings.DEMUCS_JOB_TIMEOUT,
    )

    job = job_router.submit_jobs([api_job])[0]
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
    )

@router.get('/separated-audio/stem/{audiofile_id}')
def response_stem_audio(
    audiofile: Audiofile = Depends(get_audiofile),
    stem: Literal['vocals', 'drums', 'bass', 'guitar', 'piano', 'other'] = Query(alias='stem'),
    format: Literal['wav', 'mp3', 'ogg'] = Query(alias='format')
):
    separated_path = audiofile.audiofile_directory / 'separated'
    if not os.path.exists(separated_path):
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が存在しません。'
        )
    if stem == 'other':
        stem = 'other_6s'

    if format == 'wav':
        response_directory = separated_path
    else:
        response_directory = audiofile.audiofile_directory / f'separated_{format}'
        if not os.path.exists(response_directory / f'{stem}.{format}'):
            # 保存ディレクトリが存在しない場合、変換処理を行う
            if not os.path.exists(response_directory):
                os.mkdir(response_directory)
            
            AudioConversionService.convert_audiofile_to_format([separated_path / f'{stem}.wav'], 'wav', response_directory, format)
           
            '''
            input_files = [
                separated_path / 'vocals.wav',
                separated_path / 'drums.wav',
                separated_path / 'bass.wav',
                separated_path / 'guitar.wav',
                separated_path / 'piano.wav',
                separated_path / 'other_6s.wav',
            ]
            '''
    try:
        return FileResponse(
            path=response_directory / f'{stem}.{format}',
            media_type=MEDIA_TYPE[format],
            headers={"Content-Disposition": f'attachment; filename={stem}.{format}'}
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail='ファイルが見つかりませんでした。'
        )
    
@router.get('/separated-audio/{audiofile_id}')
def response_separated_audio(request: Request, audiofile: Audiofile = Depends(get_audiofile)):
    separated_zip_path = audiofile.audiofile_directory / 'separated.zip'
    if os.path.exists(separated_zip_path):
        return FileResponse(
            path=separated_zip_path, 
            media_type='application/zip', 
            headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_separated.zip'}
        )
    else:
        raise HTTPException(
            status_code=400,
            detail='圧縮する必要があります。'
        )

@router.delete('/separated-audio/{audiofile_id}')
async def delete_separated_audio(audiofile: Audiofile = Depends(get_audiofile)):
    delete_count = 0
    if await aiofiles.os.path.exists(audiofile.audiofile_directory / 'separated'):
        await asyncio.to_thread(shutil.rmtree, audiofile.audiofile_directory / 'separated')
        delete_count += 1
    if await aiofiles.os.path.exists(audiofile.audiofile_directory / 'separated.zip'):
        await aiofiles.os.remove(audiofile.audiofile_directory / 'separated.zip')
        delete_count += 1
    if delete_count == 0:
        raise HTTPException(
            status_code=404,
            detail='音声の分離結果が存在しません。'
        )
    return('ok')

@router.post('/separated-audio/compression/{audiofile_id}', description='処理結果を圧縮する。')
def compression_separated_audio(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)):
    separated_path = audiofile.audiofile_directory / 'separated'
    separated_zip_path = audiofile.audiofile_directory / 'separated.zip'
    if os.path.exists(separated_zip_path):
        raise HTTPException(
            status_code=400,
            detail='既に圧縮が完了しています。'
        )
    elif os.path.exists(separated_path):
        api_job = ApiJob(
            job_name=settings.COMPRESSION_JOB_NAME,
            dst_api_url=f'http://{settings.COMPRESSION_HOST}:{8000}',
            queue_name=settings.COMPRESSION_JOB_QUEUE,
            request_path=f'/demucs/separated-audio/{audiofile.audiofile_id}/zip',
            job_timeout=settings.COMPRESSION_JOB_TIMEOUT,
            request_headers={settings.HTTP_HEADER_CONSUMER_ID:audiofile.consumer_id},
            request_read_timeout=settings.COMPRESSION_JOB_TIMEOUT,
        )
        job = job_router.submit_jobs([api_job])[0]
        return EventSourceResponse(
            job_router.stream_job_status(request=request, job=job)
        )
        
    else:
        raise HTTPException(
            status_code=400,
            detail='音声の分離が完了していません。'
        )
    
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
                if f == 'other.wav':
                    continue
                wav_audio = AudioSegment.from_wav(separated_path / f)
                wav_audio.export(Path(tmp_dir) / (Path(f).stem + '.mp3'), format='mp3')
            shutil.make_archive(separated_path, 'zip', tmp_dir)
    return 'ok'