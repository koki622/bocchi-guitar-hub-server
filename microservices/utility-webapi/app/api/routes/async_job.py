import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse

from app.api.deps import get_audiofile, get_heavy_job
from app.core.config import settings
from app.core.heavy_job import ApiJob, HeavyJob
from app.models import Audiofile


router = APIRouter()

@router.get('/status')
def getJobStatus(request: Request, job_id: str, job_router: HeavyJob = Depends(get_heavy_job))-> EventSourceResponse: 
    job = job_router.get_job(job_id)
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
    )

@router.post('/process-audio/{audiofile_id}')
def processAudio(request: Request, audiofile: Audiofile = Depends(get_audiofile), job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse:
    # エラー条件とメッセージをリストで定義
    error_conditions = [
        (audiofile.audiofile_directory / 'chord.json', '既にコード進行の解析がされています。'),
        (audiofile.audiofile_directory / 'separated', '既に音声の分離がされています。'),
        (audiofile.audiofile_directory / 'spectrograms.npy', '既にスペクトログラムが生成されています。'),
        (audiofile.audiofile_directory / 'structure', '既に解析がされています。'),
        (audiofile.audiofile_directory / 'lyric.txt', '既に歌詞解析がされています。')
    ]
    
    # エラー条件の一括チェック
    for path, message in error_conditions:
        if os.path.exists(path):
            raise HTTPException(status_code=400, detail=message)
    
    crema_job = settings.crema_webapi_job
    demucs_job = settings.demucs_webapi_job
    allin1_spectrograms_job = settings.allin1_webapi_job_spectrograms
    allin1_structure_job = settings.allin1_webapi_job_structure
    whisper_job = settings.whisper_webapi_job

    api_jobs = [
        ApiJob(
            job_name=crema_job.job_name,
            dst_api_url=f'http://{crema_job.host}:{crema_job.port}',
            queue_name=crema_job.queue,
            request_path='/',
            job_timeout=crema_job.timeout,
            request_body={'file_path': str(audiofile.audiofile_path)},
            request_read_timeout=crema_job.read_timeout,
        ),
        ApiJob(
            job_name=demucs_job.job_name,
            dst_api_url=f'http://{demucs_job.host}:{demucs_job.port}',
            queue_name=demucs_job.queue,
            request_path='/',
            job_timeout=demucs_job.timeout,
            request_body={'file_path': str(audiofile.audiofile_path)},
            request_read_timeout=demucs_job.read_timeout,
        ),
        ApiJob(
            job_name=allin1_spectrograms_job.job_name,
            dst_api_url=f'http://{allin1_spectrograms_job.host}:{allin1_spectrograms_job.port}',
            queue_name=allin1_spectrograms_job.queue,
            request_path='/spectrograms',
            job_timeout=allin1_spectrograms_job.timeout,
            request_body={'separated_path':str(audiofile.audiofile_directory / 'separated')},
            request_read_timeout=allin1_spectrograms_job.read_timeout,
        ),
        ApiJob(
            job_name=allin1_structure_job.job_name,
            dst_api_url=f'http://{allin1_structure_job.host}:{allin1_structure_job.port}',
            queue_name=allin1_structure_job.queue,
            request_path='/structure',
            job_timeout=allin1_structure_job.timeout,
            request_body={"file_path":str(audiofile.audiofile_path), 'spectrograms_path':str(audiofile.audiofile_directory / 'spectrograms.npy')},
            request_read_timeout=allin1_structure_job.read_timeout,
        ),
        ApiJob(
            job_name=whisper_job.job_name,
            dst_api_url=f'http://{whisper_job.host}:{whisper_job.port}',
            queue_name=whisper_job.queue,
            request_path='/',
            job_timeout=whisper_job.timeout,
            request_body={'file_path': str(audiofile.audiofile_directory / 'separated' / 'vocals.wav')},
            request_read_timeout=whisper_job.read_timeout,
        )
    ]
    jobs = job_router.submit_jobs(api_jobs)
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=jobs[0])
    )