import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import redis
from rq import Queue, Worker

conn = redis.from_url("redis://localhost:6379/0")

worker = Worker(["high", "default", "low"], connection=conn)
worker.work()
