import sys
import os
import time
import traceback

sys.path.insert(0, os.path.dirname(__file__))

import redis
from rq import Queue
from rq.job import Job

conn = redis.from_url("redis://localhost:6379/0")
queue_names = ["high", "default", "low"]

print("Worker started (Windows-compatible mode)", flush=True)
print("Listening on high, default, low...", flush=True)

while True:
    for name in queue_names:
        job_id = conn.lpop(f"rq:queue:{name}")
        if job_id:
            job_id = job_id.decode()
            try:
                job = Job.fetch(job_id, connection=conn)
                print(f"Processing job {job_id}: {job.func_name}", flush=True)

                # Import and call the function
                module_path, func_name = job.func_name.rsplit(".", 1)
                mod = __import__(module_path, fromlist=[func_name])
                func = getattr(mod, func_name)

                result = func(*job.args, **job.kwargs)

                job._status = "finished"
                job.save()
                q = Queue(name, connection=conn)
                q.finished_job_registry.add(job)
                print(f"Job {job_id} completed", flush=True)

            except Exception as e:
                print(f"Job {job_id} failed: {e}", flush=True)
                traceback.print_exc()
                try:
                    job._status = "failed"
                    job.exc_info = traceback.format_exc()
                    job.save()
                    q = Queue(name, connection=conn)
                    q.failed_job_registry.add(job)
                except:
                    pass

    time.sleep(2)
