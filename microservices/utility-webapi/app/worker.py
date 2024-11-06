"""RQワーカー起動モジュール
サブプロセスでワーカーを起動する関数を定義。
"""
import os
import subprocess
import sys
from rq import Worker, Queue, Connection
from redis import Redis
from app.core.config import settings

r = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

root_dir = os.path.dirname(__file__)
file_path = os.path.join(root_dir, 'worker.py')

def launch_workers(queue_name: str, worker_multiplicity: int):
    """サブプロセスで多重度分のワーカーを起動

    Args:
        queue_name (str): キュー名
        worker_multiplicity (int): ワーカーの多重度
    """

    for _ in range(worker_multiplicity):
        subprocess.Popen(["python3", file_path, queue_name])

def start_worker(queue_name: str):
    """ワーカーを起動

    Args:
        queue_name (str): キュー名
    """
    with Connection(r):
        queue = Queue(queue_name)
        worker = Worker([queue])
        worker.work()

if __name__ == '__main__':
    queue_name = sys.argv[1]
    start_worker(queue_name)

    