from pathlib import Path
import shutil
from fastapi import APIRouter, Depends
from app.models import Consumer, ConsumerHeaders
from app.core.config import settings
from app.api.deps import get_consumer, get_consumer_headers

router = APIRouter()

@router.post("/", description='コンシューマーを初期化する。')
def create_consumer(consumer_headers: ConsumerHeaders = Depends(get_consumer_headers)):
    dir_path = Path(settings.CONSUMER_VOLUME_PATH, consumer_headers.consumer_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    return 'ok' 

@router.delete("/", description='コンシューマーを削除する。')
def delete_consumer(consumer: Consumer = Depends(get_consumer)):
    shutil.rmtree(consumer.consumer_directory)
    return('ok')