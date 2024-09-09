from rq import Worker, Queue, Connection
from redis import Redis

r = Redis(host="redis", port=6379)

with Connection(r):
    queue = Queue("cpu_queue")
    worker = Worker([queue], name="worker_cpu2")
    worker.work()