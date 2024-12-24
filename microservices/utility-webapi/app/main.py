from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.worker import launch_workers, kill_worker
from app.api.main import api_router
from app.core.config import settings
from app.api.deps import get_redis_asyncio_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    app.state.redis_asyncio_conn = get_redis_asyncio_pool()
    kill_worker()
    launch_workers(queue_name=settings.GPU_WORKER_QUEUE, worker_multiplicity=settings.GPU_WORKER_MULTIPLICITY)
    launch_workers(queue_name=settings.CPU_WORKER_QUEUE, worker_multiplicity=settings.CPU_WORKER_MULTIPLICITY)

    yield
    # 起動中のワーカーをキル
    kill_worker()
    await app.state.redis_asyncio_conn.close()
    
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