from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Union

TimeoutType = Union[int, float] | None

UPLOAD_FILE_CONTENT_TYPE = ['audio/mpeg', 'audio/wav', 'audio/aac', 'audio/ogg', 'audio/flac']

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    GPU_MODE: bool = True

    ANONYMOUS_CONSUMER_NAME: str = 'anonymous'
    
    CONSUMER_VOLUME_PATH: str

    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379

    # demucs-webapiの設定
    DEMUCS_HOST: str = 'demucs-webapi'
    DEMUCS_JOB_NAME: str = 'demucs'
    DEMUCS_JOB_QUEUE: str = 'gpu_queue'
    DEMUCS_JOB_TIMEOUT: TimeoutType = 300 # ジョブが実行されてからのタイムアウト時間

    # crema-webapiの設定
    CREMA_HOST: str = 'crema-webapi'
    CREMA_JOB_NAME: str = 'crema'
    CREMA_JOB_QUEUE: str = 'cpu_queue'
    CREMA_JOB_TIMEOUT: TimeoutType = 30 # ジョブが実行されてからのタイムアウト時間

    # whisper-webapiの設定
    WHISPER_HOST: str = 'faster-whisper-webapi'
    WHISPER_JOB_NAME: str = 'whisper'
    WHISPER_JOB_QUEUE: str = 'gpu_queue'
    WHISPER_JOB_TIMEOUT: TimeoutType = 300 # ジョブが実行されてからのタイムアウト時間

    # allin1-webapiの設定
    ALLIN1_HOST: str = 'allin1-webapi'
    ALLIN1_SPECTROGRAMS_JOB_NAME: str = 'allin1_spectrograms'
    ALLIN1_SPECTROGRAMS_JOB_QUEUE: str = 'cpu_queue'
    ALLIN1_SPECTROGRAMS_JOB_TIMEOUT: TimeoutType = 120 # ジョブが実行されてからのタイムアウト時間

    ALLIN1_STRUCTURE_JOB_NAME: str = 'allin1_structure'
    ALLIN1_STRUCTURE_JOB_QUEUE: str = 'gpu_queue'
    ALLIN1_STRUCTURE_JOB_TIMEOUT: TimeoutType = 120 # ジョブが実行されてからのタイムアウト時間
    
    # zip圧縮webapiの設定
    COMPRESSION_HOST: str = 'localhost'
    COMPRESSION_JOB_NAME: str = 'compression'
    COMPRESSION_JOB_QUEUE: str = 'cpu_queue'
    COMPRESSION_JOB_TIMEOUT: TimeoutType = 120 # ジョブが実行されてからのタイムアウト時間

    GPU_WORKER_QUEUE: str = 'gpu_queue'
    GPU_WORKER_MULTIPLICITY: int = 1

    CPU_WORKER_QUEUE: str = 'cpu_queue'
    CPU_WORKER_MULTIPLICITY: int = 1

    HTTP_HEADER_CONSUMER_ID: str = 'x_consumer_id'
settings = Settings()