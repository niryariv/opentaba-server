"""
Scrapping worker
"""

import os
import redis
from rq import Worker, Queue, Connection
import logging

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(name)s %(levelname)s %(message)s', level=logging.WARNING)
    
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work(burst=True)
