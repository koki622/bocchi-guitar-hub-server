from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Union

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    ANONYMOUS_CONSUMER_NAME: str = 'anonymous'
    
    CONSUMER_VOLUME_PATH: str

    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379

    DEMUCS_WEBAPI_HOST: str = 'demucs-webapi'
    DEMUCS_WEBAPI_PORT: int = 8000
    DEMUCS_WEBAPI_JOB_TIMEOUT : Union[int, float] | None = 60
    DEMUCS_WEBAPI_CONNECT_TIMEOUT: Union[int, float] | None = 3
    DEMUCS_WEBAPI_READ_TIMEOUT: Union[int, float] | None = 60

    WHISPER_WEBAPI_HOST: str = 'faster-whisper-webapi'
    WHISPER_WEBAPI_PORT: int = 8000
    WHISPER_WEBAPI_JOB_TIMEOUT : Union[int, float] | None = 60
    WHISPER_WEBAPI_CONNECT_TIMEOUT: Union[int, float] | None = 3
    WHISPER_WEBAPI_READ_TIMEOUT: Union[int, float] | None = 60

    UPLOAD_FILE_CONTENT_TYPE: list[str] = ['audio/mpeg', 'audio/wav']

    HTTP_HEADER_CONSUMER_ID: str = 'x_consumer_id'
settings = Settings()