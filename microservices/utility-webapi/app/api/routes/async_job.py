import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette import EventSourceResponse

from app.api.deps import get_audiofile, get_heavy_job
from app.api.routes.whisper import LanguageCode
from app.core.config import settings
from app.core.heavy_job import ApiJob, HeavyJob
from app.models import Audiofile


router = APIRouter()

@router.get('/status')
def getJobStatus(job_id: str, job_router: HeavyJob = Depends(get_heavy_job))-> EventSourceResponse: 
    job = job_router.get_job(job_id)
    return EventSourceResponse(
        job_router.stream_job_status(job=job)
    )

@router.post('/process-audio/{audiofile_id}')
def processAudio(
    request: Request, 
    audiofile: Audiofile = Depends(get_audiofile), 
    job_router: HeavyJob = Depends(get_heavy_job),
    is_analyze_lyric: bool = Query(True, alias='is-analyze-lyric'),
    language_code: LanguageCode = Query(LanguageCode.ja, alias='language-code')
) -> EventSourceResponse:
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

    api_jobs = [
        ApiJob(
            job_name=settings.CREMA_JOB_NAME,
            dst_api_url=f'http://{settings.CREMA_HOST}:{8000}',
            queue_name=settings.CREMA_JOB_QUEUE,
            request_path='/',
            job_timeout=settings.CREMA_JOB_TIMEOUT,
            request_body={'file_path': str(audiofile.audiofile_path)},
            request_read_timeout=settings.CREMA_JOB_TIMEOUT,
        ),
        ApiJob(
            job_name=settings.DEMUCS_JOB_NAME,
            dst_api_url=f'http://{settings.DEMUCS_HOST}:{8000}',
            queue_name=settings.DEMUCS_JOB_QUEUE,
            request_path='/',
            job_timeout=settings.DEMUCS_JOB_TIMEOUT,
            request_body={'file_path': str(audiofile.audiofile_path)},
            request_read_timeout=settings.DEMUCS_JOB_TIMEOUT,
        ),
        ApiJob(
            job_name=settings.ALLIN1_SPECTROGRAMS_JOB_NAME,
            dst_api_url=f'http://{settings.ALLIN1_HOST}:{8000}',
            queue_name=settings.ALLIN1_SPECTROGRAMS_JOB_QUEUE,
            request_path='/spectrograms',
            job_timeout=settings.ALLIN1_SPECTROGRAMS_JOB_TIMEOUT,
            request_body={'separated_path':str(audiofile.audiofile_directory / 'separated')},
            request_read_timeout=settings.ALLIN1_SPECTROGRAMS_JOB_TIMEOUT,
        ),
        ApiJob(
            job_name=settings.ALLIN1_STRUCTURE_JOB_NAME,
            dst_api_url=f'http://{settings.ALLIN1_HOST}:{8000}',
            queue_name=settings.ALLIN1_STRUCTURE_JOB_QUEUE,
            request_path='/structure',
            job_timeout=settings.ALLIN1_STRUCTURE_JOB_TIMEOUT,
            request_body={"file_path":str(audiofile.audiofile_path), 'spectrograms_path':str(audiofile.audiofile_directory / 'spectrograms.npy')},
            request_read_timeout=settings.ALLIN1_STRUCTURE_JOB_TIMEOUT,
        ),
    ]
    analyze_lyric_apijob = ApiJob(
        job_name=settings.WHISPER_JOB_NAME,
        dst_api_url=f'http://{settings.WHISPER_HOST}:{8000}',
        queue_name=settings.WHISPER_JOB_QUEUE,
        request_path='/',
        job_timeout=settings.WHISPER_JOB_TIMEOUT,
        request_body={'file_path': str(audiofile.audiofile_directory / 'separated' / 'vocals.wav'), 'language_code': language_code},
        request_read_timeout=settings.WHISPER_JOB_TIMEOUT,
    )
    if is_analyze_lyric: 
        api_jobs.append(analyze_lyric_apijob)
        
    jobs = job_router.submit_jobs(api_jobs)
    return EventSourceResponse(
        job_router.stream_job_status(job=jobs[0])
    )