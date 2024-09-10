from pathlib import Path
import shutil
from fastapi import APIRouter, HTTPException, Header
from app.core.config import settings

router = APIRouter()

@router.post("/", description='コンシューマーを初期化する。')
def create_consumer(consumer_id: str = Header(settings.ANONYMOUS_CONSUMER_NAME, alias=settings.HTTP_HEADER_CONSUMER_ID)):
    dir_path = Path(settings.CONSUMER_VOLUME_PATH, consumer_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    return 'ok'  

@router.delete("/", description='コンシューマーを削除する。')
def delete_consumer(consumer_id: str = Header(settings.ANONYMOUS_CONSUMER_NAME, alias=settings.HTTP_HEADER_CONSUMER_ID)):
    dir_path = Path(settings.CONSUMER_VOLUME_PATH, consumer_id)
    try:
        shutil.rmtree(dir_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail='コンシューマーディレクトリが存在しません。'
        )
    return('ok')