import json
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse
from app.api.deps import get_audiofile, get_heavy_job
from app.core.heavy_job import ApiJob, HeavyJob
from app.core.config import settings
from app.models import Audiofile

router = APIRouter()

@router.post("/lyric/{audiofile_id}")
def analyze_lyric(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse:
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
    whisper_job = settings.whisper_webapi_job
    api_job = ApiJob(
        job_name=whisper_job.job_name,
        dst_api_url=f'http://{whisper_job.host}:{whisper_job.port}',
        queue_name=whisper_job.queue,
        request_path='/',
        job_timeout=whisper_job.timeout,
        request_body=request_body,
        request_read_timeout=whisper_job.read_timeout,
    )

    job = job_router.submit_jobs([api_job])[0]
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
    )

@router.get('/lyric/{audiofile_id}')
def response_lyric(audiofile: Audiofile = Depends(get_audiofile)):
    with open(audiofile.audiofile_directory / 'lyric.txt') as f:
        return json.load(f)