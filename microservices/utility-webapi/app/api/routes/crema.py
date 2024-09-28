from datetime import datetime
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sse_starlette import EventSourceResponse
import redis.asyncio
from app.api.deps import get_asyncio_redis_conn, get_audiofile, get_chords, get_structure
from app.core.heavy_job import HeavyJob
from app.models import Audiofile, ChordList
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
    apply_adjust_chord: bool = Query(True, alias='apply-adjust-chord'),
    eighth_beat: bool = Query(False, alias='eighth-beat'),
    audiofile: Audiofile = Depends(get_audiofile),
    chords: ChordList = Depends(get_chords),
    download_file_format: Literal['json', 'csv', 'mid'] = Query('json', alias='download-file-format')
):
    
    chord_directory = audiofile.audiofile_directory / 'chord'
    file_stem = 'adjusted_' if apply_adjust_chord else ''
    file_stem += 'chord'
    eighth_stem = 'eighth_beat_' if eighth_beat else ''
    
    if apply_adjust_chord or download_file_format == 'mid':
        structure = get_structure(audiofile, eighth_beat)

        if apply_adjust_chord:
            chords = adjust_chord_time(structure.beats, chords)
            chords.save_as_json_file(chord_directory / f'{file_stem}.json')

        if download_file_format == 'mid':
            convert_chords_to_midi(chords.chords, structure.bpm, chord_directory / f'{file_stem}.mid')
    
    if download_file_format == 'csv':
        chords.to_csv(chord_directory / f'{file_stem}.csv')
    
    return FileResponse(
                path=chord_directory / f'{file_stem}.{download_file_format}',
                media_type=media_types[download_file_format],
                headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_{eighth_stem}_{file_stem}.{download_file_format}'}
            )
    