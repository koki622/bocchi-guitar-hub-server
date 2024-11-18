from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Union
from redis import Redis

TimeoutType = Union[int, float] | None

# WEB APIごとのジョブキュー設定用のクラス
class WebAPISettings(BaseModel):
    host: str
    port: int = Field(default=8000, ge=1, le=65535)
    connect_timeout: TimeoutType = 3
    

class WebAPIJobSettings(WebAPISettings):
    queue: str
    job_name: str
    timeout: TimeoutType = 300 # ジョブが実行されてからのタイムアウト時間
    read_timeout: TimeoutType = 300 # webapiと接続が確立されてからのタイムアウト時間

class JobWorkerSettings(BaseModel):
    queue: str
    multiplicity: int # ワーカーの起動数

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    ANONYMOUS_CONSUMER_NAME: str = 'anonymous'
    
    CONSUMER_VOLUME_PATH: str

    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379

    # demucs-webapiの設定
    demucs_webapi: WebAPISettings = WebAPISettings(
        host='demucs-webapi'
    )
    # demucs-webapiのジョブキュー設定
    demucs_webapi_job: WebAPIJobSettings = WebAPIJobSettings(
        **demucs_webapi.model_dump(),
        job_name='demucs',
        queue='gpu_queue'
    )

    # crema-webapiの設定
    crema_webapi: WebAPISettings = WebAPISettings(
        host='crema-webapi'
    )
    # crema-webapiのジョブキュー設定
    crema_webapi_job: WebAPIJobSettings = WebAPIJobSettings(
        **crema_webapi.model_dump(),
        job_name='crema',
        queue='cpu_queue'
    )

    # whisper-webapiの設定
    whisper_webapi: WebAPISettings = WebAPISettings(
        host='faster-whisper-webapi'
    )
    # whisper-webapiのジョブキュー設定
    whisper_webapi_job: WebAPIJobSettings = WebAPIJobSettings(
        **whisper_webapi.model_dump(),
        job_name='whisper',
        queue='gpu_queue'
    )

    # allin1-webapiの設定
    allin1_webapi: WebAPISettings = WebAPISettings(
        host='allin1-webapi'
    )

    # allin1-webapiのスペクトログラム解析のジョブキュー設定
    allin1_webapi_job_spectrograms: WebAPIJobSettings = WebAPIJobSettings(
        **allin1_webapi.model_dump(),
        job_name='allin1_spectrograms',
        queue='cpu_queue'
    )

    # allin1-webapiの構造解析のジョブキュー設定
    allin1_webapi_job_structure: WebAPIJobSettings = WebAPIJobSettings(
        **allin1_webapi.model_dump(), 
        job_name='allin1_structure',
        queue='gpu_queue'
    )

    # zip圧縮webapiの設定
    compression_webapi: WebAPISettings = WebAPISettings(
        host='localhost'
    )
    # zip圧縮webapiのジョブキュー設定
    compression_webapi_job: WebAPIJobSettings = WebAPIJobSettings(
        **compression_webapi.model_dump(),
        job_name='compression',
        queue='cpu_queue'
    )

    gpu_worker: JobWorkerSettings = JobWorkerSettings(
        queue='gpu_queue',
        multiplicity=1
    )

    cpu_worker: JobWorkerSettings = JobWorkerSettings(
        queue='cpu_queue',
        multiplicity=1
    )

    UPLOAD_FILE_CONTENT_TYPE: list[str] = ['audio/mpeg', 'audio/wav']

    HTTP_HEADER_CONSUMER_ID: str = 'x_consumer_id'
settings = Settings()