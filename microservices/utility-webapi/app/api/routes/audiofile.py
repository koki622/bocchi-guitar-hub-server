import asyncio
from pathlib import Path
import shutil
import anyio
import shortuuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.models import Audiofile, AudiofileCreateResponse, Consumer
from app.api.deps import get_audiofile, get_consumer, validate_audiofile
from pydub import AudioSegment

router = APIRouter()

@router.post("/", response_model=AudiofileCreateResponse, description='オーディオファイルをアップロードする。')
async def save_audiofile(validated_file: UploadFile = Depends(validate_audiofile), consumer: Consumer = Depends(get_consumer)):
    audiofile_stem = Path(validated_file.filename).stem
    audiofile_suffix = Path(validated_file.filename).suffix

    
    audiofile_id = shortuuid.ShortUUID().random(length=7)
    audiofile_dir = Path(consumer.consumer_directory / audiofile_id)
    audiofile_dir.mkdir()
    audiofile_path = audiofile_dir / (audiofile_id + audiofile_suffix)
  
    async with await anyio.open_file(audiofile_path, 'wb') as buffer:
        while chunk := await validated_file.read(2048):
            await buffer.write(chunk)

    if validated_file.content_type == 'audio/mpeg':
        # アップロードされた音声ファイルがmp3の場合、wavに変換
        mp3_audio = AudioSegment.from_mp3(audiofile_path)
        wav_audiofile_path = audiofile_dir / (audiofile_id + '.wav')
        mp3_audio.export(wav_audiofile_path, format='wav')

    return AudiofileCreateResponse(audiofile_id=audiofile_id)

@router.delete("/{audiofile_id}", description='オーディオファイルを削除する。')
async def delete_audiofile(audiofile: Audiofile = Depends(get_audiofile)):
    try:
        await asyncio.to_thread(shutil.rmtree, audiofile.audiofile_directory)
        return('ok')
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail='ファイルが見つかりませんでした。'
        )
