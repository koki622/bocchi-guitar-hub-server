import redis.asyncio
from app.core.config import settings

def get_asyncio_redis_conn() -> redis.asyncio.Redis:
    return redis.asyncio.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True,
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True
    )