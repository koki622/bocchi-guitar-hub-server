import os
from pathlib import Path
from fastapi import HTTPException
from pydantic import BaseModel, field_validator


class ConsumerHeaders(BaseModel):
    consumer_id: str

class Consumer(ConsumerHeaders):
    consumer_directory: Path

    @field_validator('consumer_directory', mode='before')
    def check_consumer_directory_exists(cls, v: Path) -> Path:
        if os.path.exists(v):
            return v
        else:
            raise HTTPException(
                status_code=400,
                detail='コンシューマーディレクトリが存在しません。'
            )

class ConsumerCreate(ConsumerHeaders):
    pass
        
class AudiofileCreateResponse(BaseModel):
    audiofile_id: str

class Audiofile(Consumer):
    audiofile_id: str
    audiofile_directory: Path
    audiofile_path: Path

    @field_validator('audiofile_directory', mode='before')
    def check_audiofile_directory_exists(cls, v:Path) -> Path:
        if os.path.exists(v):
            return v
        else:
            raise HTTPException(
                status_code=400,
                detail='音声ファイルディレクトリが存在しません。'
            )

