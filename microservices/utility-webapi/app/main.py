from fastapi import FastAPI
from contextlib import asynccontextmanager

import uvicorn

from app.worker import launch_workers
from app.api.main import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    gpu_worker = settings.gpu_worker
    cpu_worker = settings.cpu_worker
    launch_workers(queue_name=gpu_worker.queue, worker_multiplicity=gpu_worker.multiplicity)
    launch_workers(queue_name=cpu_worker.queue, worker_multiplicity=cpu_worker.multiplicity)
    yield
    
app = FastAPI(
    lifespan=lifespan,
    docs_url='/docs',
    openapi_url='/docs/openapi.json'
)
app.include_router(api_router)

"""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
"""