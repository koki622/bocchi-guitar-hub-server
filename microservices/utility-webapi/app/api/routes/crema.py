import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sse_starlette import EventSourceResponse
from app.api.deps import get_audiofile, get_chords, get_heavy_job, get_structure
from app.core.heavy_job import ApiJob, HeavyJob
from app.models import Audiofile, ChordList
from app.core.config import settings
from app.services.adjust_chord import adjust_chord_time
from app.services.midi_generator import convert_chords_to_midi, convert_midi_to_audio

router = APIRouter()

@router.post("/chord/{audiofile_id}")
def analyze_chord(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse:
    if os.path.exists(audiofile.audiofile_directory / 'chord.json'):
        raise HTTPException(
            status_code=400,
            detail='既にコード進行の解析がされています。'
        )
    
    request_body = {'file_path': str(audiofile.audiofile_path)}
    crema_job = settings.crema_webapi_job
    api_job = ApiJob(
        job_name=crema_job.job_name,
        dst_api_url=f'http://{crema_job.host}:{crema_job.port}',
        queue_name=crema_job.queue,
        request_path='/',
        job_timeout=crema_job.timeout,
        request_body=request_body,
        request_read_timeout=crema_job.read_timeout,
    )

    job = job_router.submit_jobs([api_job])[0]
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
    )

media_types = {
    'json': 'application/json',
    'csv': 'text/csv',
    'mid': 'audio/midi',
    'ogg': 'audio/ogg'
}

@router.get('/chord/{audiofile_id}')
def response_chord(
    apply_adjust_chord: bool = Query(True, alias='apply-adjust-chord'),
    eighth_beat: bool = Query(False, alias='eighth-beat'),
    audiofile: Audiofile = Depends(get_audiofile),
    chords: ChordList = Depends(get_chords),
    download_file_format: Literal['json', 'csv', 'mid', 'ogg'] = Query('json', alias='download-file-format'),
    gm_program_no: int = Query(25, ge=0, le=127, description='General MIDIの音色番号', alias='gm-program-no')
):
    
    chord_directory = audiofile.audiofile_directory / 'chord'
    file_stem = 'adjusted_' if apply_adjust_chord else ''
    file_stem += 'chord'
    eighth_stem = 'eighth_beat_' if eighth_beat else ''
    
    if apply_adjust_chord or download_file_format == 'mid' or 'ogg':
        structure = get_structure(audiofile, eighth_beat)

        if apply_adjust_chord:
            chords = adjust_chord_time(structure.beats, chords)
            chords.save_as_json_file(chord_directory / f'{file_stem}.json')

        if download_file_format == 'mid' or 'ogg':
            midi_save_path = chord_directory / f'{file_stem}.mid'
            convert_chords_to_midi(chords.chords, structure.bpm, gm_program_no, midi_save_path)

            if download_file_format == 'ogg':
                # ダウンロードファイル形式がoggならmidiを音声ファイルに変換
                audio_save_path = chord_directory / f'{file_stem}.ogg'
                convert_midi_to_audio(midi_save_path, audio_save_path)
    
    if download_file_format == 'csv':
        chords.to_csv(chord_directory / f'{file_stem}.csv')
    
    return FileResponse(
                path=chord_directory / f'{file_stem}.{download_file_format}',
                media_type=media_types[download_file_format],
                headers={"Content-Disposition": f'attachment; filename={audiofile.audiofile_id}_{eighth_stem}_{file_stem}.{download_file_format}'}
            )
    