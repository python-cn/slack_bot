# coding=utf-8

DEBUG = False
SECRET_KEY = 'o\xdd\x02I\x0b\xbbBP4\x97\xab\xe0GF\xfba\x14_\x03\xa9\xe8\xfa\xf8c'   # noqa

SLACK_TOKEN = 'jLGMzrZn3P1lS2sD848KpPuN'
SLACK_CHAT_TOKEN = 'xoxp-4231087425-4231087427-4463321974-03a74a'
SLACK_CALLBACK = '/slack_callback'
REDIS_URL = 'redis://:password@localhost:6379/0'
ORG_NAME = 'python-cn'
BAIDU_AK = '18691b8e4206238f331ad2e1ca88357e'
SIMSIMI_KEY = '50c086cb-5ea3-4190-bdd6-69787a540ec4'

CACHE_TYPE = 'simple'

try:
    from local_settings import *  # noqa
except ImportError:
    print('You may need rename local_settings.py.example '
          'to local_settings.py, then update your settings')
