from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Union

TimeoutType = Union[int, float] | None

UPLOAD_FILE_CONTENT_TYPE = ['audio/mpeg', 'audio/wav']

class MachinePowerType(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    MACHINE_POWER: MachinePowerType = MachinePowerType.HIGH

    @field_validator("MACHINE_POWER", mode="before")
    @classmethod
    def validate_machine_power(cls, value):
        if isinstance(value, str):
            try:
                return MachinePowerType[value.upper()]  # 文字列をEnumに変換
            except KeyError:
                raise ValueError(f"Invalid MACHINE_POWER value: {value}")
        return value

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
    DEMUCS_JOB_READ_TIMEOUT: TimeoutType = 300 # webapiと接続が確立されてからのタイムアウト時間

    # crema-webapiの設定
    CREMA_HOST: str = 'crema-webapi'
    CREMA_JOB_NAME: str = 'crema'
    CREMA_JOB_QUEUE: str = 'cpu_queue'
    CREMA_JOB_TIMEOUT: TimeoutType = 30 # ジョブが実行されてからのタイムアウト時間
    CREMA_JOB_READ_TIMEOUT: TimeoutType = 30 # webapiと接続が確立されてからのタイムアウト時間

    # whisper-webapiの設定
    WHISPER_HOST: str = 'faster-whisper-webapi'
    WHISPER_JOB_NAME: str = 'whisper'
    WHISPER_JOB_QUEUE: str = 'gpu_queue'
    WHISPER_JOB_TIMEOUT: TimeoutType = 300 # ジョブが実行されてからのタイムアウト時間
    WHISPER_JOB_READ_TIMEOUT: TimeoutType = 300 # webapiと接続が確立されてからのタイムアウト時間

    # allin1-webapiの設定
    ALLIN1_HOST: str = 'allin1-webapi'
    ALLIN1_SPECTROGRAMS_JOB_NAME: str = 'allin1_spectrograms'
    ALLIN1_SPECTROGRAMS_JOB_QUEUE: str = 'cpu_queue'
    ALLIN1_SPECTROGRAMS_JOB_TIMEOUT: TimeoutType = 120 # ジョブが実行されてからのタイムアウト時間
    ALLIN1_SPECTROGRAMS_JOB_READ_TIMEOUT: TimeoutType = 120 # webapiと接続が確立されてからのタイムアウト時間

    ALLIN1_STRUCTURE_JOB_NAME: str = 'allin1_structure'
    ALLIN1_STRUCTURE_JOB_QUEUE: str = 'gpu_queue'
    ALLIN1_STRUCTURE_JOB_TIMEOUT: TimeoutType = 120 # ジョブが実行されてからのタイムアウト時間
    ALLIN1_STRUCTURE_JOB_READ_TIMEOUT: TimeoutType = 120 # webapiと接続が確立されてからのタイムアウト時間
    
    # zip圧縮webapiの設定
    COMPRESSION_HOST: str = 'localhost'
    COMPRESSION_JOB_NAME: str = 'compression'
    COMPRESSION_JOB_QUEUE: str = 'cpu_queue'
    COMPRESSION_JOB_TIMEOUT: TimeoutType = 120 # ジョブが実行されてからのタイムアウト時間
    COMPRESSION_JOB_READ_TIMEOUT: TimeoutType = 120 # webapiと接続が確立されてからのタイムアウト時間

    GPU_WORKER_QUEUE: str = 'gpu_queue'
    GPU_WORKER_MULTIPLICITY: int = 1

    CPU_WORKER_QUEUE: str = 'cpu_queue'
    CPU_WORKER_MULTIPLICITY: int = 1

    HTTP_HEADER_CONSUMER_ID: str = 'x_consumer_id'
settings = Settings()