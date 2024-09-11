import os
import redis.asyncio
from app.core.config import settings
from fastapi import HTTPException, Header
from pathlib import Path

def get_consumer_dir(consumer_id: str = Header(settings.ANONYMOUS_CONSUMER_NAME, alias=settings.HTTP_HEADER_CONSUMER_ID)):
    print('受信しました')
    
    consumer_dir_path = Path(settings.CONSUMER_VOLUME_PATH, consumer_id)
    if os.path.exists(consumer_dir_path):
        return consumer_dir_path
    else:
        raise HTTPException(
            status_code=400,
            detail='コンシューマーディレクトリが存在しません。'
        )

def get_audiofile_path(dir_name: str, consumer_id: str = Header(settings.ANONYMOUS_CONSUMER_NAME, alias=settings.HTTP_HEADER_CONSUMER_ID)):
    consumer_dir = get_consumer_dir(consumer_id)
    audiofile_path = consumer_dir / dir_name / (dir_name + '.wav')
    if os.path.exists(audiofile_path):
        return audiofile_path
    else:
        raise HTTPException(
            status_code=400,
            detail='ディレクトリまたは音声ファイルが存在しません。'
        )

def get_asyncio_redis_conn() -> redis.asyncio.Redis:
    return redis.asyncio.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True,
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True
    )