# coding=utf-8

# 天气
import os
import re
import cPickle as pickle

from flask import current_app

from baidumap import weather
from utils import gen_attachment, check_time


description = """
今天的天气情况, 触发条件: "[城市名称] 天气 [私聊]"。比如:
* 天气
* 上海天气
"""

DAY = {0: u'今天', 1: u'明天', 2: u'后天'}
TEMPERATURE_REGEX = re.compile(ur'(\d+)℃')


def get_city(data):
    cityidDict = pickle.load(file(
        os.path.join(os.path.dirname(__file__),
                     'data' + os.path.sep + 'cityid'), 'r'))
    return next(
        (c for c in cityidDict if c.encode('utf8') in data['message']), False)


def test(data):
    return '天气' in data['message'] and get_city(data)


def handle(data):
    app = current_app
    if app is None:
        ak = '18691b8e4206238f331ad2e1ca88357e'
    else:
        ak = app.config.get('BAIDU_AK')
    city = get_city(data)
    if not city:
        return '不会自己去看天气预报啊'
    res = weather(ak, city)[:3]
    ret = []
    attaches = []
    for idx, day in enumerate(res):
        if idx == 0:
            current = TEMPERATURE_REGEX.search(day['date']).groups()[0]
            text = u'{0}: {1} {2} {3} 温度: {4}'.format(
                DAY[idx], current, day['weather'],
                day['wind'], day['temperature'])
        else:
            text = u'{0}: {1} {2} 温度: {3}'.format(
                DAY[idx], day['weather'],
                day['wind'], day['temperature'])
        ret.append(text)
        type = 'dayPictureUrl' if check_time() == 'day' else 'dayPictureUrl'
        attaches.append(gen_attachment(text, day[type], image_type='thumb',
                                       title=u'{}天气预报'.format(city),
                                       title_link=''))
    return '\n'.join(ret), attaches


if __name__ == '__main__':
    print test({'message': '天气怎么样'})
    print test({'message': '北京天气怎么样'})
    print handle({'message': '北京天气怎么样'})
