from rq import SimpleWorker, Queue, Connection
from redis import Redis
from rq.job import Job
import job
import time

r = Redis(host="redis", port=6379)
global separator
separator = None

class CustomWorker(SimpleWorker):
    def execute_job(self, job: Job, queue: Queue):
        print("execute_jobにいます")
        print(job.func_name)
        task_type = job.meta.get("task_type")
        print(task_type)
        if (task_type == "demucs"): 
            print("super().execute_jobします")  
            super().execute_job(job, queue)
        else:
            # ジョブをキューの先頭に再キューイング
            self.enqueue_job_at_front(job, queue)
            time.sleep(3)

    def enqueue_job_at_front(self, job: Job, queue: Queue):
        r.lpush(queue.key, job.id)

with Connection(r):
    job.init_demucs()
    print(job.__separator)
    queue = Queue("gpu_queue")
    worker_demucs = CustomWorker([queue], name="worker_demucs") # CustomWorkerにしないと上手く動作しない
    #worker_demucs = Worker([queue], connection=r, name="worker_demucs")
    worker_demucs.work()

