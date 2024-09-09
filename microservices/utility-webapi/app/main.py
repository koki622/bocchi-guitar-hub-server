from fastapi import FastAPI
from contextlib import asynccontextmanager
import subprocess

import uvicorn

from app.api.main import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    subprocess.Popen(["python3", "worker_gpu.py"])
    subprocess.Popen(["python3", "worker_cpu.py"])
    subprocess.Popen(["python3", "worker_cpu2.py"])
    yield
    
app = FastAPI(
    lifespan=lifespan,
    openapi_url='/docs/openapi.json'
)
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")