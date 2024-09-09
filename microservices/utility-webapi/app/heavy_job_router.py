import asyncio
from redis import Redis
import redis.asyncio
from rq import Queue
import shortuuid
import requests
import json
from typing import Optional
from typing import Literal
from fastapi import Request

class HeavyJobRouter:
    def __init__(self, api_host: str, api_port: int):
        self.api_host = api_host
        self.api_port = api_port
    
    def route_job(self, pubsub_channel: str, pubsub_id: str, path: str="/", payload: json=None, timeout: Optional[float] = None):
        url = f"http://{self.api_host}:{self.api_port}{path}"
        pubsub_url = Redis.from_url(
            "redis://redis:6379?decode_responses=True",
            health_check_interval=10,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            socket_keepalive=True)
        try:
            response = requests.post(url=url, json=payload, timeout=timeout)

            pubsub_url.publish(pubsub_channel, f"success:{pubsub_id}")
            return response.text
        except Exception as e:
            pubsub_url.publish(pubsub_channel, f"failure:{pubsub_id}")
            return e

Pubsub_channel = Literal['gpu:channel', 'cpu:channel']
Queue_type = Literal['gpu', 'cpu']

async def heavy_job_res(
    request: Request, 
    pubsub_channel: Pubsub_channel,
    queue: Queue_type, 
    router: HeavyJobRouter, 
    request_path: str = "/", 
    request_body: dict = None, 
    request_timeout: int = 30
):
    async def job_reader(request: Request, channel: redis.client.PubSub, pubsub_id: str, queue_position: int = None):
        if queue_position is None:
            yield {"data": "処理しています"}
        else:
            yield {"data": f"現在のキュー:{queue_position}"}    
        while True:
            if await request.is_disconnected():
                break
            message = await channel.get_message(ignore_subscribe_messages=True)
            if message is not None:
                result, src_pubsub_id = message["data"].split(':')
                if src_pubsub_id == pubsub_id:
                    break
                queue_position -= 1
                yield {"data": f"現在のキュー:{queue_position}"}
    pubsub_url = redis.asyncio.Redis(
        host='redis',
        port=6379,
        decode_responses=True,
        health_check_interval=10,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        socket_keepalive=True)
    
    pubsub_id = shortuuid.ShortUUID().random(length=10)
    job_kwargs = {"pubsub_channel": pubsub_channel, "pubsub_id": pubsub_id, "path": request_path, "payload": request_body, "timeout": request_timeout}
    try:
        job_queue = queue.enqueue(router.route_task, 
                            kwargs=job_kwargs)
        job_id = job_queue.id
        yield {'data': {'task_id':job_id}}
        queue_position = job_queue.get_position()

        async with pubsub_url.pubsub() as pubsub:
            # ジョブの待ち状況を取得
            await pubsub.subscribe(pubsub_channel)
            async for message in job_reader(request, pubsub, pubsub_id, queue_position):
                yield {"data": f"{message['data']}"}
           
        while True:
            await asyncio.sleep(0.5)
            job_result = job_queue.result
            if job_result is not None:
                break
            print('Job Result is None')
        yield{'data': job_result}
    except asyncio.CancelledError as e:
        print("クライアントからの接続が切れました")
    except Exception as e:
        raise e