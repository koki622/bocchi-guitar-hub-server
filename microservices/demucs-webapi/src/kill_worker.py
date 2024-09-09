from redis import Redis
from rq.command import send_kill_horse_command
from rq.worker import Worker, WorkerStatus

r = Redis(host="redis", port=6379)

send_kill_horse_command(r, "worker_demucs")