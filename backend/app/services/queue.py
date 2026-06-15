import redis
from rq import Queue

from app.core.config import settings


class QueueService:
    def __init__(self):
        self._conn = redis.from_url(settings.REDIS_URL)
        self._high = Queue("high", connection=self._conn)
        self._default = Queue("default", connection=self._conn)
        self._low = Queue("low", connection=self._conn)

    def enqueue_job(self, job_id: str, priority: str = "default"):
        from app.workers.video_worker import process_video_job

        queue = {"high": self._high, "default": self._default, "low": self._low}.get(priority, self._default)
        return queue.enqueue(
            process_video_job,
            job_id,
            job_timeout="10m",
            result_ttl=3600,
        )

    def get_job_status(self, rq_job_id: str):
        from rq.job import Job

        try:
            job = Job.fetch(rq_job_id, connection=self._conn)
            return {
                "status": job.get_status(),
                "result": job.result,
                "exc_info": job.exc_info,
            }
        except Exception:
            return None


queue_service = QueueService()
