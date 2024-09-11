from pathlib import Path
import shutil
import shortuuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from app.core.config import settings
from app.api.deps import get_consumer_dir, get_audiofile_path
from pydub import AudioSegment

router = APIRouter()

@router.post("/", description='オーディオファイルをアップロードする。')
async def save_audiofile(request: Request, audiofile: UploadFile = File(...), consumer_dir: Path = Depends(get_consumer_dir)):
    audiofile_stem = Path(audiofile.filename).stem
    audiofile_suffix = Path(audiofile.filename).suffix

    if audiofile.content_type not in settings.UPLOAD_FILE_CONTENT_TYPE:
        raise HTTPException(
            status_code=400,
            detail=f'{audiofile.content_type} 形式はサポートしていません'
        )
    rand_dirname = shortuuid.ShortUUID().random(length=7)
    audiofile_dir = Path(consumer_dir / rand_dirname)
    audiofile_dir.mkdir()
    rand_filename = rand_dirname + audiofile_suffix
    audiofile_path = audiofile_dir / rand_filename

    with audiofile_path.open('wb') as buffer:
        shutil.copyfileobj(audiofile.file, buffer)

    if audiofile.content_type == 'audio/mpeg':
        # アップロードされた音声ファイルがmp3の場合、wavに変換
        mp3_audio = AudioSegment.from_mp3(audiofile_path)
        wav_audiofile_path = audiofile_dir / (rand_dirname + '.wav')
        mp3_audio.export(wav_audiofile_path, format='wav')

    return {'filename': audiofile.filename, 'dir_name': rand_dirname}

@router.delete("/", description='オーディオファイルを削除する。')
async def delete_audiofile(audiofile_path: Path = Depends(get_audiofile_path)):
    shutil.rmtree(audiofile_path.parent)
    return('ok')
