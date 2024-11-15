from datetime import datetime
import json
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.api.deps import get_asyncio_redis_conn, get_audiofile
from app.core.heavy_job import HeavyJob
from app.models import Audiofile, Structure
from app.core.config import settings
from pydub import AudioSegment

router = APIRouter()

@router.post("/spectrograms/{audiofile_id}")
def spectrograms(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.allin1_webapi.host,
        dst_api_port=settings.allin1_webapi.port,
        dst_api_connect_timeout=settings.allin1_webapi.connect_timeout
    )
    now = datetime.now()
    print(now)
    separated_path = audiofile.audiofile_directory / 'separated'

    if os.path.exists(audiofile.audiofile_directory / 'spectrograms.npy'):
        raise HTTPException(
            status_code=400,
            detail='既にスペクトログラムが生成されています。'
        )
    
    if not os.path.exists(separated_path):
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が見つかりませんでした。解析には音声の分離結果が必要です。'
        )
    
    # separatedフォルダにother.wavがなければ生成する
    if not os.path.exists(separated_path / 'other.wav'):
        combined = AudioSegment.from_wav(separated_path / 'other_6s.wav')
        for file_name in ['piano.wav', 'guitar.wav']:
            audio = AudioSegment.from_wav(separated_path / file_name)
            # 音声を重ねる
            combined = combined.overlay(audio)

        combined.export(separated_path / 'other.wav', format='wav')

    request_body = {'separated_path':str(separated_path)}
    return EventSourceResponse(
        job_router.stream(
            request=request, 
            queue_name=settings.allin1_webapi_job_spectrograms.queue,
            job_timeout=settings.allin1_webapi_job_spectrograms.timeout,
            request_path='/spectrograms',
            request_body=request_body,
            request_read_timeout=settings.allin1_webapi_job_spectrograms.read_timeout
        )
    )

@router.post("/structure/{audiofile_id}")
def analyze_structure(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.allin1_webapi.host,
        dst_api_port=settings.allin1_webapi.port,
        dst_api_connect_timeout=settings.allin1_webapi.connect_timeout
    )
    now = datetime.now()
    print(now)
    
    if os.path.exists(audiofile.audiofile_directory / 'structure'):
        raise HTTPException(
            status_code=400,
            detail='既に解析がされています。'
        )
    if not os.path.exists(audiofile.audiofile_directory / 'spectrograms.npy'):
        raise HTTPException(
            status_code=400,
            detail='スペクトログラムが見つかりませんでした。解析にはスペクトログラムが必要です。'
        )
    request_body = {"file_path":str(audiofile.audiofile_path), 'spectrograms_path':str(audiofile.audiofile_directory / 'spectrograms.npy')}    
    return EventSourceResponse(
        job_router.stream(
            request=request, 
            queue_name=settings.allin1_webapi_job_structure.queue,
            job_timeout=settings.allin1_webapi_job_structure.timeout,
            request_path='/structure',
            request_body=request_body,
            request_read_timeout=settings.allin1_webapi_job_structure.read_timeout
        )
    )

@router.get("/structure/{audiofile_id}")
def response_structure(
    audiofile: Audiofile = Depends(get_audiofile), 
    download_file_format: Literal['json', 'csv'] = Query('json', alias='download-file-format'),
    csv_data: Literal['beats', 'segments'] = Query(None, alias='csv-data'),
    eighth_beat: bool = Query(False, alias='eighth-beat')
):
    structure_directory = audiofile.audiofile_directory / 'structure'
    try:
        structure = Structure.load_from_json_file(structure_directory / 'structure.json')
        if eighth_beat:
            structure = structure.convert_splited_beats_into_eighths()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail='結果が見つかりませんでした。'
        )
    if download_file_format == 'csv':
        if not csv_data:
            raise HTTPException(
                status_code=400,
                detail='"download-file-format=csv"の場合は、"csv-data"の入力が必須です。(beats または segments)'
            )
        elif csv_data == 'beats':
            stem = 'beats'
            structure.to_csv(structure_directory / f'{stem}.csv', ['beats', 'beat_positions'])
        elif csv_data == 'segments':
            stem = 'segments'
            structure.to_csv(structure_directory / f'{stem}.csv', ['segments'])
    else:
        stem = 'structure'
    return FileResponse(
        path=structure_directory / f'{stem}.{download_file_format}',
        headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_{stem}.{download_file_format}'}
    )

@router.get('/structure/click-sound/{audiofile_id}')
def response_click_sound(
    audiofile: Audiofile = Depends(get_audiofile), 
    click_sound_type: Literal['normal', '2x', 'half'] = Query(default='normal', alias='click-sound-type')
):
    structure_directory = audiofile.audiofile_directory / 'structure'
    click_sound_directory = None
    if click_sound_type == 'normal':
        click_sound_directory = structure_directory / 'clicks_normal.mp3'
    elif click_sound_type == '2x':
        click_sound_directory = structure_directory / 'clicks_2x.mp3'
    elif click_sound_type == 'half':
        click_sound_directory = structure_directory / 'clicks_half.mp3'

    try:
        return FileResponse(path=click_sound_directory, headers={"Content-Disposition": f'attachment; filename={click_sound_directory.stem}{click_sound_directory.suffix}'})
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail='結果が見つかりませんでした。'
        )
    except:
        raise HTTPException(
            status_code=500,
            detail='不明なエラー。'  
        )
    