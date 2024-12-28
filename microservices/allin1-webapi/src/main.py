import asyncio
from enum import Enum
import subprocess
from datetime import datetime
import logging
from pydantic import BaseModel
import torch

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request

# ログ設定
logging.basicConfig(
    level=logging.INFO,  # INFO以上のログを出力
    format="%(asctime)s - %(levelname)s - %(message)s",  # フォーマットを指定
    handlers=[
        logging.StreamHandler()  # コンソールに出力
    ]
)
logger = logging.getLogger(__name__)

class AnalyzeExecutionError(Exception):
    pass

class AnalyzeTerminatedException(Exception):
    pass

class ClientDisconnectException(Exception):
    pass

class AnalyzeType(Enum):
    spectrograms = 'スペクトログラム抽出'
    structure = '音楽構造解析'

async def monitor_disconnection(request: Request, process: asyncio.subprocess.Process):
    try:
        while True:
            message = await request.receive()
            if message["type"] == "http.disconnect":
                logger.info("Client disconnected")
                process.terminate()  # クライアントが切断された場合、プロセスを終了
                break
    except Exception as e:
        logger.error(f"Error while monitoring disconnection: {e}")
        process.terminate()  
    raise ClientDisconnectException()

async def monitor_analyze_process(process: asyncio.subprocess.Process, analyze_type: AnalyzeType):
    # 標準出力（およびエラー出力）をリアルタイムで読み取る
    async for line in process.stdout:
        print(line.decode().strip())

    # プロセスの終了を待つ
    await process.wait()

    if process.stderr:
        stderr_output = await process.stderr.read()
        logger.error("サブプロセスでエラー:", stderr_output.decode().strip())

    logger.info(f'プロセス終了コード:{process.returncode}')

    if process.returncode < 0:
        raise AnalyzeTerminatedException()
        
    # プロセスが非ゼロの終了コードで終了した場合
    elif process.returncode != 0:
        raise AnalyzeExecutionError(f'{analyze_type.value}処理で例外が発生:')
    
async def handle_subprocess(request: Request, start_time: datetime, process: asyncio.subprocess.Process, analyze_type: AnalyzeType):
    try:
        # クライアントとの接続状況を監視
        disconnection_task = asyncio.create_task(monitor_disconnection(request, process=process))

        # サブプロセスを監視
        await monitor_analyze_process(process=process, analyze_type=analyze_type)
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"end:{end_time}, duration:{duration}")
        return {"end":end_time}
    except subprocess.CalledProcessError:
        raise HTTPException(
            status_code=500,
            detail='解析処理失敗'
        )
    except AnalyzeTerminatedException:
        logger.info(f'{analyze_type.value}処理を中断しました')
    except ClientDisconnectException:
        logger.info(f"クライアントとの接続が失われたので{analyze_type.value}処理をキャンセルしました")
    finally:
        disconnection_task.cancel()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"{device} モードで起動")
    yield
    logger.info("shutdown")

app = FastAPI(lifespan=lifespan)

class SpectrogramsCreateBody(BaseModel):
    separated_path: str

class StructureCreateBody(BaseModel):
    file_path: str
    spectrograms_path: str


@app.post("/spectrograms")
async def ext_spectrograms(request: Request, body: SpectrogramsCreateBody):
    now = datetime.now()
    logger.info(f"処理開始:{now}")

    # 解析処理をサブプロセスで実行
    proc = await asyncio.create_subprocess_exec(
        'python3', '/app/src/spectrograms_process.py', body.separated_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    endtime = await handle_subprocess(request=request, start_time=now, process=proc, analyze_type=AnalyzeType.spectrograms)
    return endtime


    
@app.post("/structure")
async def analyze_structure(request: Request, body: StructureCreateBody):
    now = datetime.now()
    logger.info(f"処理開始:{now}")

    # 解析処理をサブプロセスで実行
    proc = await asyncio.create_subprocess_exec(
        'python3', '/app/src/structure_process.py', body.file_path, body.spectrograms_path, device,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    endtime = await handle_subprocess(request=request, start_time=now, process=proc, analyze_type=AnalyzeType.structure)
    return endtime