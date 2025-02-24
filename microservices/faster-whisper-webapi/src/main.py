import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from pydantic import BaseModel, field_validator
from faster_whisper import WhisperModel, tokenizer
from datetime import datetime
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,  # INFO以上のログを出力
    format="%(asctime)s - %(levelname)s - %(message)s",  # フォーマットを指定
    handlers=[
        logging.StreamHandler()  # コンソールに出力
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model
    logger.info("モデルをロードします")
    model_size = 'large-v3-turbo'
    if os.getenv('GPU_MODE', 'True') == 'True':
        logger.info('GPUモードで起動します')
        whisper_model = WhisperModel(
            model_size_or_path=model_size)
    else:
        logger.info('CPUモードで起動します')
        whisper_model = WhisperModel(
            device='cpu',
            model_size_or_path=model_size,
            compute_type='int8'
        )
    
    logger.info("モデルのロードが完了しました")
    logging.basicConfig()
    logging.getLogger("faster_whisper").setLevel(logging.DEBUG)
    yield
    print("shutdown")

app = FastAPI(lifespan=lifespan)

class AnalyzeLyricRequest(BaseModel):
    file_path: str
    language_code: str

    @field_validator('language_code')
    def validate_language_code(cls, v):
        if v not in tokenizer._LANGUAGE_CODES:
            raise ValueError("Invalid language code.")
        return v


@app.post("/")
async def analyze_lyric(body: AnalyzeLyricRequest, request: Request):
    file_path = body.file_path
    now = datetime.now()
    logger.info(f'処理開始:{now}')
    
    try:
        segments, info = whisper_model.transcribe(file_path, language=body.language_code, word_timestamps=True, hallucination_silence_threshold=2)
        word_results = []
        segment_results = []
        for segment in segments:
            # 接続が切断されているか確認
            if await request.is_disconnected():
                logger.info('クライアントとの接続が切断されました')
                raise HTTPException(status_code=499, detail="Client Disconnected")
                
            segment_dics = {'start': segment.start, 'end': segment.end, 'text': segment.text}
            segment_results.append(segment_dics)
            for word in segment.words:
                if await request.is_disconnected():
                    logger.info('クライアントとの接続が切断されました')
                    raise HTTPException(status_code=499, detail="Client Disconnected")
                print("[%.2fs -> %.2fs] %s" % (word.start, word.end, word.word))
                word_dict = {'start': word.start, 'end': word.end, 'text': word.word}
                word_results.append(word_dict)
        
        with open(Path(file_path).parent.parent / 'lyric.txt', 'w', encoding='utf-8') as txt:
            json.dump({'segments': segment_results, 'word': word_results}, txt)
    except HTTPException as http_exception:
        raise http_exception 
    except Exception as e:
        print(f"エラーが発生:{e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    end_time = datetime.now()
    duration = end_time - now
    logger.info(f"end:{end_time}, duration:{duration}")
    return end_time