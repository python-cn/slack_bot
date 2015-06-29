# coding=utf-8

# debug模式主要用在gunicorn启动的时候可能看到错误堆栈
DEBUG = True
SECRET_KEY = 'o\xdd\x02I\x0b\xbbBP4\x97\xab\xe0GF\xfba\x14_\x03\xa9\xe8\xfa\xf8c'   # noqa

# clask chat token 注册地址: https://api.slack.com/web
SLACK_CHAT_TOKEN = 'xoxp-4231087425-4231087427-4463321974-03a74a'
# 你希望slack的outgoing-webhook调用你的回调的路由
SLACK_CALLBACK = '/slack_callback'
# 使用Github-issue插件需要指定组织的地址
ORG_NAME = 'python-cn'
# 百度地图api key, 注册地址: http://lbsyun.baidu.com/apiconsole/key
BAIDU_AK = '18691b8e4206238f331ad2e1ca88357e'
# simsim key, 注册地址: http://developer.simsimi.com/
SIMSIMI_KEY = '50c086cb-5ea3-4190-bdd6-69787a540ec4'
# 大众点评应用, 注册地址: http://developer.dianping.com/dashboard/info/app
DIANPING_APPKEY = '41502445'
DIANPING_SECRET = 'f0c2cc0b4f1048bebffc1527acbaeeb8'

# Flask-cache的类型, 默认为SimpleCache
CACHE_TYPE = 'simple'
# 假如使用RedisCache, 也就是CACHE_TYPE = 'redis'需要配置CACHE_REDIS_URL
CACHE_REDIS_URL = 'redis://user:password@localhost:6379/0'

# 使用`python manage.py send`时候的模拟数据
TEST_DATA = {
    'token': 'jLGMzrZn3P1lS2sD848KpPuN',
    'text': 'text',
    'team_id': 'T0001',
    'team_domain': 'example',
    'channel_id': 'C2147483705',
    'channel_name': 'channel_name',
    'timestamp': '1355517523',
    'user_id': 'U2147483697',
    'user_name': 'Steve',
    'trigger_word': '',
}

try:
    from local_settings import *  # noqa
except ImportError:
    print('You may need rename local_settings.py.example '
          'to local_settings.py, then update your settings')
