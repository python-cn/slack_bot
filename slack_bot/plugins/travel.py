# coding=utf-8
import re

from flask import current_app

from baidumap import travel_city, travel_attractions
from weather import get_city
from utils import chinese2digit, to_pinyin

description = '''
国内旅游推荐/景点介绍/X日游。触发条件: "xx旅游推荐|颐和园景点介绍|xx3(/三)日游"。比如:
* 沈阳旅游推荐
* 景点介绍颐和园
* 颐和园景点介绍
* 北京3日游
'''

ATTRACTIONS_REGEX = re.compile(r'(.*?)景点介绍(.*?)')
CITY_REGEX = re.compile(r'(旅游推荐)')
DAYS_REGEX = re.compile(r'(.*)日游')


def get_desc(regex, message):
    match = regex.search(message)
    if match:
        return next((m for m in match.groups() if m), None)


def get_itinerary(res, details=False):
    if not res['itineraries']:
        return '没找到对应的行程'
    text = []
    if details:
        text.append(res['description'])
    for i in res['itineraries']:
        text.append(u'类型: {0}: {1}'.format(i['name'], i['description']))
        for index, it in enumerate(i['itineraries'], 1):
            text.append(
                u'第{}天  '.format(index) + u' ->'.join(
                    [p['name'] for p in it['path']]))
            for t in ['description', 'dinning', 'accommodation']:
                text.append(it[t])
        text.append('\n')
    return '\n'.join(text)


def test(data):
    return get_city(data) and any([
        regex.search(data['message']) for regex in [CITY_REGEX, DAYS_REGEX]]) \
        or ATTRACTIONS_REGEX.search(data['message'])


def handle(data):
    app = current_app
    if app is None:
        ak = '18691b8e4206238f331ad2e1ca88357e'
    else:
        ak = app.config.get('BAIDU_AK')
    message = data['message']
    location = get_city(data)
    if location:
        message = message.replace(location.encode('utf-8'), '')
    days = get_desc(DAYS_REGEX, message)
    if days:
        if not isinstance(days, int):
            days = chinese2digit(days)
        res = travel_city(ak, location, days)
        return get_itinerary(res), None
    city = get_desc(CITY_REGEX, message)
    if city:
        res = travel_city(ak, location)
        return get_itinerary(res, details=True), None
    attractions = get_desc(ATTRACTIONS_REGEX, message)
    if attractions:
        return travel_attractions(ak, to_pinyin(attractions)), None
    return '没找到对应的旅游行程', None

if __name__ == '__main__':
    print handle({'message': '北京三日游'})
    print handle({'message': '北京旅游推荐'})
    print handle({'message': '颐和园景点介绍'})
