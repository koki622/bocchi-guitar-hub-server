from fastapi import FastAPI
from contextlib import asynccontextmanager

import uvicorn

from app.worker import launch_workers
from app.api.main import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    launch_workers(queue_name=settings.GPU_WORKER_QUEUE, worker_multiplicity=settings.GPU_WORKER_MULTIPLICITY)
    launch_workers(queue_name=settings.CPU_WORKER_QUEUE, worker_multiplicity=settings.CPU_WORKER_MULTIPLICITY)
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