# coding=utf-8

SLACK_TOKEN = 'jLGMzrZn3P1lS2sD848KpPuN'
SLACK_CHAT_TOKEN = 'xoxp-4231087425-4231087427-4463321974-03a74a'
SLACK_CALLBACK = '/slack_callback'
REDIS_URL = 'redis://:password@localhost:6379/0'
ORG_NAME = 'python-cn'
BAIDU_AK = '18691b8e4206238f331ad2e1ca88357e'
CACHE_TYPE = 'simple'

try:
    from local_settings import *  # noqa
except ImportError:
    print('You may need rename local_config.py.example to local_config.py, '
          'then update your settings')
