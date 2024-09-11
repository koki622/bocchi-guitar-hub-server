import asyncio
from redis import Redis
import redis.asyncio
import redis.asyncio
import redis.client
from rq import Queue, Callback
from rq.job import Job
from rq.results import Result
import shortuuid
import requests
from requests.exceptions import Timeout
import json
from typing import Literal, Union
from fastapi import Request
import time
from datetime import datetime, timezone
from collections.abc import AsyncGenerator

async def get_job_result(job: Job, sleep_time: Union[int, float]) -> any:
    while True:
        await asyncio.sleep(sleep_time)
        job_result = job.latest_result()
        print(job_result)
        if job_result is not None:
            if job_result.type == Result.Type.SUCCESSFUL:
                print('success')
                print(job.return_value())
            break
        print('Job Result is None')
    return job_result

def datetime_to_stream_id(dt: datetime, sequence: Union[int, None] = 0) -> str:
    """datetimeをRedis StreamsのStreamId形式に変換する

    Args:
        dt (datetime): datetime型の日時。
        sequence (Union[int, None], optional): StreamIdの末尾に付くシーケンス番号。デフォルトは0。

    Returns:
        str: Redis StreamsでStreamIdとして使うことができる。
    """
    timestamp_ms = int(dt.replace(tzinfo=None).timestamp() * 1000)
    if sequence is None:
        return str(timestamp_ms)
    return f"{timestamp_ms}-{sequence}"

def notify_job_success(job: Job, connection, result, *args, **kwargs):
    """ジョブが成功したことをRedis Streamsで通知する。

    rqでジョブをキューに入れる際に、ジョブ成功後に呼び出されるコールバック関数として用いる。

    Args:
        job (Job): _description_
        connection (_type_): _description_
        result (_type_): ジョブの結果。
    """
    stream_id = datetime_to_stream_id(datetime.now(timezone.utc), None)
    print(stream_id)
    #meta = job.meta.get('queue_name')
    print(job.origin)
    s_id = connection.xadd('gpu_stream', {'message':f"{result}:{job.id}"}, id=stream_id)
    print('メッセージを送信しました', 'sid:', s_id)

def notify_job_failure(job: Job, connection, type, value, traceback):
    stream_id = datetime_to_stream_id(datetime.now(timezone.utc), None)
    s_id = connection.xadd('gpu_stream', {'message':f"{type}:{job.id}"}, id=stream_id)
    print('メッセージを送信しました', 'sid:', s_id)

async def route_job(
    dst_api_host: str,
    dst_api_port: int,
    path: str="/",
    headers: json=None,
    payload: json=None, 
    connect_timeout: Union[float, int] = None,
    read_timeout: Union[float, int] = None
):
    url = f"http://{dst_api_host}:{dst_api_port}{path}"
    try:
        response = requests.post(url=url, json=payload, headers=headers, timeout=(connect_timeout, read_timeout))
        return 'ok'
    except Timeout as e:
        raise e
    except Exception as e:
        raise e
    
class HeavyJob:
    def __init__(
        self,
        redis_host: str,
        redis_port: int,
        redis_asyncio_conn: redis.asyncio.Redis,
        dst_api_host: str, 
        dst_api_port: int
    ):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_asyncio_conn = redis_asyncio_conn
        self.dst_api_host = dst_api_host
        self.dst_api_port = dst_api_port

    async def response_queue_status_from_stream (
            self, 
            request:Request, 
            stream_name:str, 
            job_id:str, 
            queue_position: Union[int, None], 
            enqueued_at:datetime
    ) -> AsyncGenerator[int, None]:
        last_stream_id = datetime_to_stream_id(enqueued_at)
        is_finished: bool= False
        while True:
            messages = await self.redis_asyncio_conn.xread(streams={stream_name: last_stream_id})
            for stream, message_list in messages:
                for message_id, message_body in message_list:
                    result, src_stream_id = message_body['message'].split(':')
                    if src_stream_id == job_id:
                        is_finished = True 
                        break
                    if queue_position is not None:
                        queue_position -= 1
                        yield queue_position
                    last_stream_id = message_id
                if is_finished: 
                    break
            if is_finished: 
                break
            
    """
    async def response_queue_status(self, request: Request, pubsub_channel: str, pubsub_id: str , queue_position: Union[int, None]):
        async def job_reader(
            request: Request, 
            channel: redis.client.PubSub,
            pubsub_id: str, 
            queue_position: int = None
        ):
            if queue_position is None:
                yield {"data": "処理しています"}
            else:
                yield {"data": f"現在のキュー:{queue_position}"}  

            while True:
                if await request.is_disconnected():
                    break
                
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    #yield{"data":message}
                    result, src_pubsub_id = message["data"].split(':')
                    if src_pubsub_id == pubsub_id:
                        break
                    queue_position -= 1
                    yield {"data": f"現在のキュー:{queue_position}"}

        async with self.redis_asyncio_conn.pubsub() as pubsub:
            # ジョブの待ち状況を取得
            await pubsub.subscribe(pubsub_channel)
            async for message in job_reader(request, pubsub, pubsub_id, queue_position):
                yield {"data": f"{message['data']}"}
    """
    def generate_job_status_message(self, job_id: str, job_status: Literal['processing soon', 'queued', 'enqueue success'], queue_position: int = None) -> dict:
        print(job_status)
        return {
            'event':'job status notification', 
            'data':{
                'job_id': job_id,
                'job_status':job_status, 
                'queue_position':queue_position
            }
        }
    
    async def stream(
        self,
        request: Request, 
        pubsub_channel: str,
        queue_name: str, 
        job_timeout: Union[int, str] = 60,
        request_path: str = "/",
        request_headers: dict = None,
        request_body: dict = None, 
        request_connect_timeout: Union[int, float] = None,
        request_read_timeout: Union[int, float] = None
    ):
        redis_conn = Redis(self.redis_host, self.redis_port)
        q = Queue(name=queue_name, connection=redis_conn)
        job_id = shortuuid.ShortUUID().random(length=10)
        job_kwargs = {
            "dst_api_host": self.dst_api_host,
            "dst_api_port": self.dst_api_port,
            "path": request_path, 
            'headers':request_headers,
            "payload": request_body, 
            "connect_timeout": request_connect_timeout,
            "read_timeout": request_read_timeout
        }
        
        try:  
            job_queue = q.enqueue(
                f=route_job,
                job_id=job_id,
                job_timeout=job_timeout,
                meta={'queue_name':queue_name},
                kwargs=job_kwargs,
                on_success=Callback(notify_job_success),
                on_failure=Callback(notify_job_failure)
            )
            job_id = job_queue.id
            enqueued_at = job_queue.enqueued_at
            print(datetime_to_stream_id(enqueued_at))
            yield self.generate_job_status_message(job_id, 'enqueue success')
    
            queue_position = job_queue.get_position()
            if queue_position is None:
                yield self.generate_job_status_message(job_id, 'processing soon')
            async for queue_position in self.response_queue_status_from_stream(request, 'gpu_stream', job_id, queue_position, enqueued_at):
                if queue_position < 0:
                    yield self.generate_job_status_message(job_id, 'processing soon')
                else:
                    yield self.generate_job_status_message(job_id, 'queued', queue_position)

            job_result = await get_job_result(job_queue, 0.1)
            yield{'event':'result','data': job_result}

        except asyncio.CancelledError as e:
            print("クライアントからの接続が切れました")

        except Exception as e:
            raise e