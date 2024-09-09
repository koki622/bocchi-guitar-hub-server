from fastapi import FastAPI, UploadFile
from tempfile import NamedTemporaryFile
from contextlib import asynccontextmanager
from pydantic import BaseModel
import torch
from faster_whisper import WhisperModel
import shutil
import os
import subprocess
import time
from sse_starlette.sse import EventSourceResponse
from datetime import datetime
import logging
import pysubs2

@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model
    print("モデルをロードします")
    whisper_model = WhisperModel(
        model_size_or_path="large-v2", 
        device="cuda", 
        compute_type="float16")
    print("モデルのロードが完了しました")
    logging.basicConfig()
    logging.getLogger("faster_whisper").setLevel(logging.DEBUG)
    yield
    print("shutdown")

app = FastAPI(lifespan=lifespan)

class FilePathBody(BaseModel):
    file_path: str

"""
def process_file(file_path: str):
    try:
        yield "event: 処理始めるよ\n\n"
        #job = queue.enqueue(task_demucs, file_path, separator, meta={"task_type": "demucs"})
        task = queue.enqueue("job.task_whisper", file_path, meta={"task_type": "whisper"})
        result = None
        while True:
            result = task.result
            if result is None:
                queue_position = task.get_position()
                yield f"event: {queue_position}\n\n"
                time.sleep(5)
            else:
                break

        #os.remove(file_path)
        yield f"data:{str(result)}\n\n"
    except Exception as e:
        print("error")
        print(e)
"""

@app.post("/")
def analyzeLyric(body: FilePathBody):
    file_path = body.file_path
    now = datetime.now()
    print(now)
    #temp_file_path = "../input/soramo_toberuhazu(vocal).wav"
    try:
        segments, info = whisper_model.transcribe(file_path, language="ja", word_timestamps=True)
        word_results= []
        segment_results = []
        for segment in segments:
            segment_dics = {'start':segment.start,'end':segment.end,'text':segment.text}
            segment_results.append(segment_dics)
            for word in segment.words:
                print("[%.2fs -> %.2fs] %s" % (word.start, word.end, word.word))
                word_dict = {'start':word.start,'end':word.end,'text':word.word}
                word_results.append(word_dict)
        """
        wsubs = pysubs2.load_from_whisper(word_results)
        wsubs.save(path="../output/soramo_word.srt")
        ssubs = pysubs2.load_from_whisper(segment_results)
        ssubs.save(path="../output/soramo_seg.srt")
        """
    except Exception as e:
        print(f"エラーが発生:{e}")
        return e
    end_time = datetime.now()
    duration = end_time - now
    print(f"end:{end_time}, duration:{duration}")
    return {"end":end_time, "result":segments}