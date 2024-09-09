from rq import Worker, Queue, Connection
from redis import Redis

r = Redis(host="redis", port=6379)

with Connection(r):
    queue = Queue("gpu_queue")
    worker = Worker([queue], name="worker_gpu")
    worker.work()