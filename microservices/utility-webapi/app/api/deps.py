import redis.asyncio
from app.core.config import settings, UPLOAD_FILE_CONTENT_TYPE
from app.core.heavy_job import HeavyJob
from app.models import Audiofile, ChordList, Consumer, ConsumerHeaders, Structure
from fastapi import Depends, File, HTTPException, Header, Path as fastapi_path, Query, Request, UploadFile
from pathlib import Path

def get_consumer_headers(consumer_id :str = Header(settings.ANONYMOUS_CONSUMER_NAME, alias=settings.HTTP_HEADER_CONSUMER_ID)) -> ConsumerHeaders:
    return ConsumerHeaders(consumer_id=consumer_id)

def get_consumer(consumer_headers: ConsumerHeaders = Depends(get_consumer_headers)) -> Consumer:
    consumer_dir = Path(settings.CONSUMER_VOLUME_PATH, consumer_headers.consumer_id)
    return Consumer(**consumer_headers.model_dump(), consumer_directory=consumer_dir)

def validate_audiofile(file: UploadFile = File(...)) -> UploadFile:
    if file.content_type not in UPLOAD_FILE_CONTENT_TYPE:
            raise HTTPException(
                status_code=400,
                detail=f'{file.content_type} 形式はサポートしていません'
            )
    else:
        return file

def get_audiofile(audiofile_id: str = fastapi_path(...), audiofile: Audiofile = Depends(get_consumer)) -> Audiofile:
    audiofile_dir = Path(audiofile.consumer_directory, audiofile_id)
    audiofile_path = audiofile_dir / (f'{audiofile_id}.wav')
    return Audiofile(**audiofile.model_dump(), audiofile_id=audiofile_id, audiofile_directory=audiofile_dir, audiofile_path=audiofile_path)

def get_chords(audiofile: Audiofile = Depends(get_audiofile)) -> ChordList:
    chord_directory = audiofile.audiofile_directory / 'chord'
    try:
        return ChordList.load_from_json_file(chord_directory / 'chord.json')
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail='コード進行の解析結果が見つかりませんでした。'
        )

def get_structure(
        audiofile: Audiofile = Depends(get_audiofile), 
        eighth_beat: bool = Query(False, alias='eighth-beat')
) -> Structure:
    try:
        structure = Structure.load_from_json_file(audiofile.audiofile_directory / 'structure' / 'structure.json')
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail='音楽構造の解析結果が見つかりません。'
        )
    return structure.convert_splited_beats_into_eighths() if eighth_beat else structure

_redis_pool = None
def get_redis_asyncio_pool():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.asyncio.Redis.from_pool(
            redis.asyncio.ConnectionPool(
                host=settings.REDIS_HOST, 
                port=settings.REDIS_PORT,
                decode_responses=True,
                health_check_interval=10,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                socket_keepalive=True
            )
        )
    print('最大接続数：' ,_redis_pool.connection_pool.max_connections)
    return _redis_pool

def get_heavy_job() -> HeavyJob:
    return HeavyJob(
        redis_host=settings.REDIS_HOST, 
        redis_port=settings.REDIS_PORT, 
        redis_asyncio_conn= get_redis_asyncio_pool(), 
    )