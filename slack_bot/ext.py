# coding=utf-8
from flask_redis import FlaskRedis
from flask_cache import Cache

redis_store = FlaskRedis()
cache = Cache()
