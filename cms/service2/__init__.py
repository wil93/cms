import os

import redis

redis_connection = redis.from_url(os.getenv("REDIS_URL"))
