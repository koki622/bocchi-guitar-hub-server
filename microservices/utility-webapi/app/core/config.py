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

    CREMA_WEBAPI_HOST: str = 'crema-webapi'
    CREMA_WEBAPI_PORT: int = 8000
    CREMA_WEBAPI_JOB_TIMEOUT : Union[int, float] | None = 60
    CREMA_WEBAPI_CONNECT_TIMEOUT: Union[int, float] | None = 3
    CREMA_WEBAPI_READ_TIMEOUT: Union[int, float] | None = 60

    WHISPER_WEBAPI_HOST: str = 'faster-whisper-webapi'
    WHISPER_WEBAPI_PORT: int = 8000
    WHISPER_WEBAPI_JOB_TIMEOUT : Union[int, float] | None = 60
    WHISPER_WEBAPI_CONNECT_TIMEOUT: Union[int, float] | None = 3
    WHISPER_WEBAPI_READ_TIMEOUT: Union[int, float] | None = 60

    ALLIN1_WEBAPI_HOST: str = 'allin1-webapi'
    ALLIN1_WEBAPI_PORT: int = 8000

    ALLIN1_WEBAPI_SPECTROGRAMS_JOB_TIMEOUT : Union[int, float] | None = 60
    ALLIN1_WEBAPI_SPECTROGRAMS_CONNECT_TIMEOUT: Union[int, float] | None = 3
    ALLIN1_WEBAPI_SPECTROGRAMS_READ_TIMEOUT: Union[int, float] | None = 60

    ALLIN1_WEBAPI_STRUCTURE_JOB_TIMEOUT : Union[int, float] | None = 60
    ALLIN1_WEBAPI_STRUCTURE_CONNECT_TIMEOUT: Union[int, float] | None = 3
    ALLIN1_WEBAPI_STRUCTURE_READ_TIMEOUT: Union[int, float] | None = 60

    UPLOAD_FILE_CONTENT_TYPE: list[str] = ['audio/mpeg', 'audio/wav']

    HTTP_HEADER_CONSUMER_ID: str = 'x_consumer_id'
settings = Settings()