from rq import SimpleWorker, Queue, Connection
from redis import Redis
from rq.job import Job
import job
import time

r = Redis(host="redis", port=6379)

class CustomWorker(SimpleWorker):
    def execute_job(self, job: Job, queue: Queue):
        task_type = job.meta.get("task_type")
        if (task_type == "whisper"): 
            super().execute_job(job, queue)
        else:
            # ジョブをキューの先頭に再キューイング
            self.enqueue_job_at_front(job, queue)
            time.sleep(3)
    def enqueue_job_at_front(self, job: Job, queue: Queue):
        r.lpush(queue.key, job.id)

with Connection(r):
    job.init_whisper()
    queue = Queue("gpu_queue")
    worker_whisper = CustomWorker([queue], name="worker_whisper") # CustomWorkerにしないと上手く動作しない
    worker_whisper.work()