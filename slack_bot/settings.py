# coding=utf-8

SLACK_TOKEN = 'jLGMzrZn3P1lS2sD848KpPuN'
SLACK_CALLBACK = '/slack_callback'
REDIS_URL = 'redis://:password@localhost:6379/0'
PLUGINS = ['simsimi']
ORG_NAME = 'python-cn'

try:
    from local_settings import *  # noqa
except ImportError:
    print('You may need rename local_config.py.example to local_config.py, '
          'then update your settings')
