from datetime import datetime
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.api.deps import get_asyncio_redis_conn, get_audiofile
from app.core.heavy_job import HeavyJob
from app.models import Audiofile, ChordList, CsvConvertibleBase, Structure
from app.core.config import settings
from app.services.adjust_chord import adjust_chord_time
from app.services.midi_generator import convert_chords_to_midi

router = APIRouter()

@router.post("/chord/{audiofile_id}")
def analyze_chord(request: Request, audiofile: Audiofile = Depends(get_audiofile), r_asyncio: redis.asyncio.Redis = Depends(get_asyncio_redis_conn)) -> EventSourceResponse:
    job_router = HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn=r_asyncio, 
        dst_api_host=settings.crema_webapi.host,
        dst_api_port=settings.crema_webapi.port,
        dst_api_connect_timeout=settings.crema_webapi.connect_timeout
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
            queue_name=settings.crema_webapi_job.queue,
            job_timeout=settings.crema_webapi_job.timeout,
            request_path='/',
            request_body=request_body,
            request_read_timeout=settings.crema_webapi_job.read_timeout
        )
    )

media_types = {
    'json': 'application/json',
    'csv': 'text/csv',
    'mid': 'audio/midi'
}

@router.get('/chord/{audiofile_id}')
def response_chord(
    audiofile: Audiofile = Depends(get_audiofile),
    apply_adjust_chord: bool = Query(True, alias='apply-adjust-chord'), 
    eighth_beat: bool = Query(False, alias='eighth-beat'),
    download_file_format: Literal['json', 'csv', 'mid'] = Query('json', alias='download-file-format')
):
    chord_directory = audiofile.audiofile_directory / 'chord'

    try:
        chords = ChordList.load_from_json_file(chord_directory / 'chord.json')
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail='コード進行の解析結果が見つかりませんでした。'
        )
    
    chord_model: CsvConvertibleBase = None
    structure_model = None
    file_stem = ''

    if apply_adjust_chord:
        file_stem += 'adjusted_'
        try:
            structure = Structure.load_from_json_file(audiofile.audiofile_directory / 'structure' / 'structure.json')
        except FileNotFoundError:
            raise HTTPException(
                status_code=400,
                detail='コードのタイミングを調整するには、音楽構造の解析結果が必要です。'
            )
        if eighth_beat:
            eighth_structure = structure.convert_splited_beats_into_eighths()
            structure_model = eighth_structure
            file_stem += 'eighth_beat_chord'
        else:
            structure_model = structure
            file_stem += 'chord'
        beats = structure_model.beats

        # コードのタイミングを補正
        adjusted_chords = adjust_chord_time(beats, chords)
        adjusted_chords.save_as_json_file(chord_directory / f'{file_stem}.json')

        chord_model = adjusted_chords
    else:
        chord_model = chords
        file_stem += 'chord'

    if download_file_format == 'csv':
        chord_model.to_csv(chord_directory / f'{file_stem}.csv')
    
    if download_file_format == 'mid':
        structure_model = structure_model if structure_model else Structure.load_from_json_file(audiofile.audiofile_directory / 'structure' / 'structure.json')
        bpm = structure_model.calculate_bpm()
        convert_chords_to_midi(chord_model.chords, bpm, chord_directory / f'{file_stem}.mid')

    return FileResponse(
                path=chord_directory / f'{file_stem}.{download_file_format}',
                media_type=media_types[download_file_format],
                headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_{file_stem}.{download_file_format}'}
            )
    