import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sse_starlette import EventSourceResponse
from app.api.deps import get_audiofile, get_heavy_job
from app.core.heavy_job import ApiJob, HeavyJob
from app.models import Audiofile, Structure
from app.core.config import settings

from app.services.audio_conversion import AudioConversionService

router = APIRouter()

MEDIA_TYPE = {
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'ogg': 'audio/ogg'
}

@router.post("/spectrograms/{audiofile_id}")
def spectrograms(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse:
    separated_path = audiofile.audiofile_directory / 'separated'

    if os.path.exists(audiofile.audiofile_directory / 'spectrograms.npy'):
        raise HTTPException(
            status_code=400,
            detail='既にスペクトログラムが生成されています。'
        )
    
    if not os.path.exists(separated_path / 'vocals.wav'):
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が見つかりませんでした。解析には音声の分離結果が必要です。'
        )
    
    request_body = {'separated_path':str(separated_path)}
    allin1_spectrograms_job = settings.allin1_webapi_job_spectrograms
    api_job = ApiJob(
        job_name=allin1_spectrograms_job.job_name,
        dst_api_url=f'http://{allin1_spectrograms_job.host}:{allin1_spectrograms_job.port}',
        queue_name=allin1_spectrograms_job.queue,
        request_path='/spectrograms',
        job_timeout=allin1_spectrograms_job.timeout,
        request_body=request_body,
        request_read_timeout=allin1_spectrograms_job.read_timeout,
    )

    job = job_router.submit_jobs([api_job])[0]
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
    )

@router.post("/structure/{audiofile_id}")
def analyze_structure(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse:
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
    allin1_structure_job = settings.allin1_webapi_job_structure
    api_job = ApiJob(
        job_name=allin1_structure_job.job_name,
        dst_api_url=f'http://{allin1_structure_job.host}:{allin1_structure_job.port}',
        queue_name=allin1_structure_job.queue,
        request_path='/structure',
        job_timeout=allin1_structure_job.timeout,
        request_body=request_body,
        request_read_timeout=allin1_structure_job.read_timeout,
    )

    job = job_router.submit_jobs([api_job])[0]
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
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
    click_sound_type: Literal['normal', '2x', 'half'] = Query(default='normal', alias='click-sound-type'),
    format: Literal['wav', 'mp3', 'ogg'] = Query(alias='format')
):
    structure_directory = audiofile.audiofile_directory / 'structure'

    # 初期はmp3ファイルしか存在しない
    mp3_click_sound_path = structure_directory / f'clicks_{click_sound_type}.mp3'

    if not os.path.exists(mp3_click_sound_path):
        raise HTTPException(
            status_code=404,
            detail='結果が見つかりませんでした。'
        )

    # 実際にダウンロードされる拡張子のファイルパス
    download_click_sound_path = mp3_click_sound_path.with_suffix(f'.{format}')
    
    if not format == 'mp3':
        if not os.path.exists(download_click_sound_path):
            AudioConversionService.convert_audiofile_to_format([mp3_click_sound_path], 'mp3', structure_directory, format)

    try:
        return FileResponse(
            path=download_click_sound_path, 
            media_type=MEDIA_TYPE[format],
            headers={"Content-Disposition": f'attachment; filename={download_click_sound_path.stem}{download_click_sound_path.suffix}'})
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail='結果が見つかりませんでした。'
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='不明なエラー。'  
        )
    