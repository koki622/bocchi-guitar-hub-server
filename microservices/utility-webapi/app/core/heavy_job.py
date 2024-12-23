"""ジョブの管理と、その状況の通知を扱うモジュール。

このモジュールは、Python RQを用いたジョブの管理と、ジョブの状態や結果をリアルタイムで通知するための機能を提供します。
ジョブは、宛先APIへのリクエストで構成され、ジョブの実行は、宛先のAPIへリクエストが送信することを指します。
サーバーサイドで実行されるジョブのキューイング、ジョブの状況と結果の通知を非同期に行います。

"""
import asyncio
from redis import Redis
import redis.asyncio
import redis.client
from rq import Queue, Callback
from rq.job import Job, JobStatus
from rq.results import Result
import shortuuid
import requests
from requests.exceptions import Timeout
import json
from typing import Literal, Optional, Union
from fastapi import Request
from datetime import datetime, timezone
from collections.abc import AsyncGenerator
from pydantic import BaseModel

async def get_job_result(job: Job, sleep_time: Union[int, float]) -> Result:
    """ジョブの結果を待つ。

    ジョブの結果をsleep_time間隔で取得する。

    Args:
        job (Job): Jobのインスタンス。
        sleep_time (Union[int, float]): どのくらいの頻度で結果を確認するか。

    Returns:
        any: Jobの結果。
    """
    while True:
        await asyncio.sleep(sleep_time)
        job_result = job.latest_result()
        print(job_result)
        if job_result is not None:
            
            break
        print('Job Result is None')
    return job_result

def _datetime_to_stream_id(dt: datetime, sequence: Union[int, None] = 0) -> str:
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

def _queue_name_to_stream_name(queue_name: str) -> str:
    return f'{queue_name}_notify_stream'

def _notify_job(job: Job, connection, send_data: dict):
    """ジョブの結果をRedis Streamsを用いて通知する。

    Args:
        job (Job): Jobのインスタンス。
        connection (_type_): Redisのコネクション。
        send_data (dict): Redis Streamsで送信するデータ。
    """
    # ストリームIDを現在時刻から生成する
    stream_id = _datetime_to_stream_id(datetime.now(timezone.utc), None)

    # 結果の通知先ストリームチャンネル名をキュー名から取得する
    notify_stream_name = _queue_name_to_stream_name(job.meta.get('queue_name'))

    s_id = connection.xadd(notify_stream_name, send_data, id=stream_id)
    print('メッセージを送信しました', 'sid:', s_id)

def _notify_job_success(job: Job, connection, result, *args, **kwargs):
    """ジョブが成功したことを通知する。

    rqでジョブをキューに入れる際に、ジョブ成功後に呼び出されるコールバック関数として用いる。

    Args:
        job (Job): jobのインスタンス。
        connection (_type_): Redisのコネクション。
        result (_type_): ジョブの結果。
    """
    send_data = {'message':f"{job.id}"}
    _notify_job(job, connection, send_data)

def _notify_job_failure(job: Job, connection, type, value, traceback):
    """ジョブが失敗したことを通知する。

    rqでジョブをキューに入れる際に、ジョブ成功後に呼び出されるコールバック関数として用いる。
    
    Args:
        job (Job): jobのインスタンス。
        connection (_type_): Redisのコネクション。
        type (_type_): _description_
        value (_type_): _description_
        traceback (_type_): _description_
    """
    send_data = {'message':f"{job.id}"}
    _notify_job(job, connection, send_data)

class ApiJob(BaseModel):
    job_name: str
    dst_api_url: str
    queue_name: str 
    request_path: str = "/"
    job_timeout: Union[int, str] = 60
    dst_api_connect_timeout: Union[int, float] = None
    request_headers: dict = None
    request_body: dict = None
    request_read_timeout: Union[int, float] = None

async def route_job(
    api_job: ApiJob,
    next_job_id: Optional[str],
):
    url = api_job.dst_api_url + api_job.request_path
    try:
        response = requests.post(
            url=url, 
            json=api_job.request_body, 
            headers=api_job.request_headers, 
            timeout=(api_job.dst_api_connect_timeout, api_job.request_read_timeout)
        )
        response.raise_for_status()
        return {'next_job_id': next_job_id}
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
    ):
        self.redis_conn = Redis(redis_host, redis_port)
        self.redis_asyncio_conn = redis_asyncio_conn

    async def response_queue_status_from_stream (
            self, 
            request:Request, 
            stream_name:str, 
            job_id:str, 
            queue_position: Union[int, None], 
            enqueued_at:datetime
    ) -> AsyncGenerator[int, None]:
        last_stream_id = _datetime_to_stream_id(enqueued_at)
        is_finished: bool= False
        while True:
            messages = await self.redis_asyncio_conn.xread(streams={stream_name: last_stream_id})
            for stream, message_list in messages:
                for message_id, message_body in message_list:
                    src_stream_id = message_body['message']
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
            
    def _generate_job_status_message(self, job_name: str, job_id: str, job_status: Literal['processing soon', 'queued', 'enqueue success', 'job success', 'job failed', 'job completed'], queue_position: int = None) -> dict:
        data = {
            'job_name': job_name,
            'job_id': job_id,
            'job_status':job_status, 
            'queue_position':queue_position
        }
        
        return f"{json.dumps(data)}\n\n"
    
    def get_job(self, job_id: str) -> Job:
        job = Job.fetch(job_id, self.redis_conn)
        return job

    def submit_jobs(self, api_jobs: list[ApiJob]) -> list[Job]:
        api_jobs_with_ids = [{'job_id': shortuuid.ShortUUID().random(length=10), 'api_job': api_job} for api_job in api_jobs]
        job_list: list[Job] = []
        for index, api_job_with_id in enumerate(api_jobs_with_ids):
            depends_job = None
            dependent_job_id = None
            if index != 0:
                # 先頭のジョブでなければ依存先のジョブをセット
                depends_job = job_list[index - 1]
            if len(api_jobs_with_ids) -1 > index:
                # 次に実行するジョブIDをセット
                dependent_job_id = api_jobs_with_ids[index + 1]['job_id']
            job = self._enqueue_job(api_job_with_id['api_job'], api_job_with_id['job_id'], depends_job, dependent_job_id)
            job_list.append(job)
        
        return job_list

    def _enqueue_job(self, api_job: ApiJob, api_job_id: str, depends_job: Optional[Job], dependent_job_id: Optional[str]) -> Job:
        
        q = Queue(name=api_job.queue_name, connection=self.redis_conn)

        job_kwargs = {
            'next_job_id': dependent_job_id,
            'api_job': api_job
        }

        job_queue = q.enqueue(
            f=route_job,
            job_id=api_job_id,
            result_ttl=259200, # 3day
            job_timeout=api_job.job_timeout,
            meta={'queue_name': api_job.queue_name, 'job_name': api_job.job_name},
            kwargs=job_kwargs,
            depends_on=depends_job,
            on_success=Callback(_notify_job_success),
            on_failure=Callback(_notify_job_failure))
        
        return job_queue
    
    async def stream_job_status(
        self,
        request: Request,
        job: Job
    ): 
        current_status = job.get_status()
        if current_status == (JobStatus.FAILED or JobStatus.CANCELED):
            yield '中止された'

        while (True):
            enqueued_at = job.enqueued_at
            job_id = job.get_id()
            job_name = job.meta.get('job_name')
            yield self._generate_job_status_message(job_name, job_id, 'enqueue success')
            notify_stream_name = _queue_name_to_stream_name(job.origin)

            queue_position = job.get_position()

            try:
                if queue_position is None:
                    # queue_positionが空の状態は、既に処理中であることを示す。
                    yield self._generate_job_status_message(job_name, job_id, 'processing soon')

                # queue_positionの初期値から現在のキューの位置を推定し、位置に変化がある度に通知する。
                async for queue_position in self.response_queue_status_from_stream(request, notify_stream_name, job_id, queue_position, enqueued_at):
                    if queue_position < 0:
                        # 0未満はキューを抜け出して、処理が始まることを示す。
                        yield self._generate_job_status_message(job_name, job_id, 'processing soon')
                    else:
                        yield self._generate_job_status_message(job_name, job_id, 'queued', queue_position)

                # すぐに結果が反映されないので、0.1秒待ってから結果を取得
                job_result = await get_job_result(job, 0.1)
                job_result_status = None
                next_job_id = None
                if job_result.type == Result.Type.SUCCESSFUL:
                    job_result_status = 'job success'
                    next_job_id = job_result.return_value['next_job_id']
                else:
                    job_result_status = 'job failed'
                
                # ジョブの成否を通知    
                yield self._generate_job_status_message(job_name, job_id, job_result_status)
                if job_result_status == 'job failed':
                    break
                
                if next_job_id is None:
                    yield self._generate_job_status_message(job_name, job_id, 'job completed')
                    break
                else:
                    job = Job.fetch(next_job_id, self.redis_conn)
            except asyncio.CancelledError as e:
                print("クライアントからの接続が切れました")
                break

    '''
    async def stream(
        self,
        api_job: Job
    ):
        """ジョブキューの状況をServer Sent Eventsでレスポンスするためのジェネレータを返します。

        Args:
            request (Request): _description_
            queue_name (str): _description_
            job_timeout (Union[int, str], optional): _description_. Defaults to 60.
            request_path (str, optional): _description_. Defaults to "/".
            request_headers (dict, optional): _description_. Defaults to None.
            request_body (dict, optional): _description_. Defaults to None.
            request_read_timeout (Union[int, float], optional): _description_. Defaults to None.

        Raises:
            e: _description_

        Yields:
            _type_: _description_
        """
        redis_conn = Redis(self.redis_host, self.redis_port)
        q = Queue(name=queue_name, connection=redis_conn)
    
        job_id = shortuuid.ShortUUID().random(length=10)
        job_kwargs = {
            "dst_api_host": self.dst_api_host,
            "dst_api_port": self.dst_api_port,
            "connect_timeout": self.dst_api_conenect_timeout,
            "path": request_path, 
            'headers':request_headers,
            "payload": request_body, 
            "read_timeout": request_read_timeout
        }
        
        try:  
            job_queue = q.enqueue(
                f=route_job,
                job_id=job_id,
                job_timeout=job_timeout,
                meta={'queue_name':queue_name},
                kwargs=job_kwargs,
                on_success=Callback(_notify_job_success),
                on_failure=Callback(_notify_job_failure)
            )

            job_id = job_queue.id
            enqueued_at = job_queue.enqueued_at
            
            yield self.generate_job_status_message(job_id, 'enqueue success')
    
            queue_position = job_queue.get_position()
        
            notify_stream_name = _queue_name_to_stream_name(queue_name)

            if queue_position is None:
                # queue_positionが空の状態は、既に処理中であることを示す。
                yield self.generate_job_status_message(job_id, 'processing soon')

            # queue_positionの初期値から現在のキューの位置を推定し、位置に変化がある度に通知する。
            async for queue_position in self.response_queue_status_from_stream(request, notify_stream_name, job_id, queue_position, enqueued_at):
                if queue_position < 0:
                    # 0未満はキューを抜け出して、処理が始まることを示す。
                    yield self.generate_job_status_message(job_id, 'processing soon')
                else:
                    yield self.generate_job_status_message(job_id, 'queued', queue_position)

            # すぐに結果が反映されないので、0.1秒待ってから結果を取得
            job_result = await get_job_result(job_queue, 0.1)
            job_result_status = None
            if job_result.type == Result.Type.SUCCESSFUL:
                job_result_status = 'job success'
            else:
                job_result_status = 'job failed'

            # ジョブの成否を通知    
            yield self.generate_job_status_message(job_id, job_result_status)

        except asyncio.CancelledError as e:
            print("クライアントからの接続が切れました")

        except Exception as e:
            raise e
    '''
