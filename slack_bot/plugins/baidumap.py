# coding=utf-8

# 百度地图
import os
import re
import cPickle as pickle
from datetime import datetime

from flask import current_app as app
import requests

from utils import to_pinyin

description = """
路线规划, 触发条件: "从 地名 到|去 地名 [出行方式] [私聊]"。比如：
我想从兆维工业园到北京南站 步行
"""

HERE = os.path.abspath(os.path.dirname(__file__))
REGEX = re.compile(ur'从(\w+)[\u53bb|\u5230](\w+)', re.UNICODE)
HTML_REGEX = re.compile(r'(<.*?>)')
SUGGESTION_API = 'http://api.map.baidu.com/place/v2/suggestion'
DIRECTION_API = 'http://api.map.baidu.com/direction/v1'
GEOCODING_API = 'http://api.map.baidu.com/geocoder/v2/'
POINT_API = 'http://api.map.baidu.com/telematics/v3/point'
TRAVEL_ATTRACTIONS_API = 'http://api.map.baidu.com/telematics/v3/travel_attractions'  # noqa
TRAVEL_CITY_API = 'http://api.map.baidu.com/telematics/v3/travel_city'
LOCAL_API = 'http://api.map.baidu.com/telematics/v3/local'
WEATHER_API = 'http://api.map.baidu.com/telematics/v3/weather'

DIRECTION = 0
NODIRECTION = 1
NOSCHEME = 2

TagList = pickle.load(
    open(os.path.join(HERE, 'data' + os.path.sep + 'baidu_tag.pkl'), 'rb'))


def address2geo(ak, address, city=u'北京'):
    res = requests.get(GEOCODING_API, params={
        'city': city, 'address': address, 'ak': ak, 'output': 'json'})
    data = res.json()
    if data['status']:
        # 一般是无相关结果
        return False
    if not data['result']['precise'] and data['result']['confidence'] <= 50:
        # 可信度太低, 需要确认
        return False
    return data['result']['location']


def geo2address(ak, location):
    res = requests.get(GEOCODING_API, params={
        'location': location, 'ak': ak, 'output': 'json'})
    data = res.json()
    if data['status']:
        return False
    return data['result']['formatted_address']


def place_suggestion(ak, pos):
    res = requests.get(SUGGESTION_API, params={
        'query': pos, 'region': 131, 'ak': ak, 'output': 'json'})
    return [r['name'] for r in res.json()['result']]


def place_direction(ak, origin, destination, mode='transit', tactics=11,
                    region='北京', origin_region='北京',
                    destination_region='北京'):
    params = {
        'origin': origin, 'destination': destination, 'ak': ak,
        'output': 'json', 'mode': mode, 'tactics': tactics
    }
    if mode != 'transit':
        params.update({
            'origin_region': origin_region,
            'destination_region': destination_region
        })
    else:
        params.update({'region': region})
    res = requests.get(DIRECTION_API, params=params).json()
    result = res.get('result', [])

    # type=1起终点模糊
    if res['type'] == 1:
        if not result:
            return (NOSCHEME, place_suggestion(ak, origin),
                    place_suggestion(ak, destination))
        if mode != 'transit':
            _origin = result['origin']['content']
            _dest = result['destination']['content']
        else:
            _origin = result.get('origin', [])
            _dest = result.get('destination', [])
        o = ['{0}: {1}'.format(
            r['name'].encode('utf-8') if r['name'] else '',
            r['address'].encode('utf-8') if r['address'] else '')
            for r in _origin]
        d = ['{0}: {1}'.format(
            r['name'].encode('utf-8') if r['name'] else '',
            r['address'].encode('utf-8') if r['address'] else '')
            for r in _dest]
        return (NODIRECTION, o, d)
    # 起终点明确
    if mode == 'driving':
        # 驾车
        taxi = result['taxi']
        for d in taxi['detail']:
            if u'白天' in d['desc']:
                daytime = d
            else:
                night = d
        is_daytime = 5 < datetime.now().hour < 23
        price = daytime['total_price'] if is_daytime else night['total_price']
        remark = taxi['remark']
        taxi_text = u'{0} 预计打车费用 {1}元'.format(remark, price)
        steps = result['routes'][0]['steps']
        steps = [re.sub(HTML_REGEX, '', s['instructions']) for s in steps]
        return (DIRECTION, '\n'.join(steps), taxi_text)
    elif mode == 'walking':
        steps = result['routes'][0]['steps']
        steps = [re.sub(HTML_REGEX, '', s['instructions']) for s in steps]
        return (DIRECTION, '\n'.join(steps), '')
    else:
        schemes = result['routes']
        steps = []
        for index, scheme in enumerate(schemes, 1):
            scheme = scheme['scheme'][0]
            step = '*方案{0} [距离: {1}公里, 花费: {2}元, 耗时: {3}分钟]:\n'.format(
                index, scheme['distance'] / 1000,
                scheme['price'] / 100,
                scheme['duration'] / 60)
            step += '\n'.join([
                re.sub(HTML_REGEX, '',
                       s[0]['stepInstruction'].encode('utf-8'))
                for s in scheme['steps']
            ])
            step += '\n' + '-' * 40
            steps.append(step)
        return (DIRECTION, steps, '')


# 车联网API
def point(ak, keyword, city=u'北京'):
    '''兴趣点查询'''
    res = requests.get(POINT_API, params={
        'keyword': keyword, 'city': city, 'ak': ak, 'output': 'json'})
    data = res.json()
    return data['pointList']


def travel_attractions(ak, id):
    '''景点详情'''
    id = to_pinyin(id)
    res = requests.get(TRAVEL_ATTRACTIONS_API, params={
        'id': id, 'ak': ak, 'output': 'json'})
    data = res.json()
    if data['error']:
        return '找不到这个景点'
    data = res.json()['result']
    return '\n'.join([
        data['description'],
        u'票价: ' + data['ticket_info']['price'],
        u'开放时间: ' + data['ticket_info']['open_time']
    ])


def travel_city(ak, location=u'北京', day='all'):
    '''X日游'''
    res = requests.get(TRAVEL_CITY_API, params={
        'location': location, 'day': day, 'ak': ak, 'output': 'json'})
    return res.json()['result']


def local(ak, tag, keyword, location=u'北京', radius=3000, city=u'北京'):
    '''周边检索'''
    res = requests.get(LOCAL_API, params={
        'cityName': city, 'radius': radius, 'tag': tag,
        'keyWord': keyword, 'location': location, 'ak': ak, 'output': 'json'})
    return res.json()['pointList']


def weather(ak, location=u'北京'):
    # location可是是城市名, 也可以是geo
    res = requests.get(WEATHER_API, params={
        'location': location, 'ak': ak, 'output': 'json'})
    return res.json()['results'][0]['weather_data']


def test(data):
    message = data['message']
    if not isinstance(message, unicode):
        message = message.decode('utf-8')
    return REGEX.search(message)


def handle(data):
    if app is None:
        ak = '18691b8e4206238f331ad2e1ca88357e'
    else:
        ak = app.config.get('BAIDU_AK')
    message = data['message']
    if not isinstance(message, unicode):
        message = message.decode('utf-8')
    origin, dest = REGEX.search(message).groups()

    tmpl = '最优路线: {0} {1}'
    if any([text in message for text in [u'开车', u'驾车']]):
        mode = 'driving'
        tmpl = '最优路线: {0} \n[{1}]'
    elif u'步行' in message:
        mode = 'walking'
    else:
        # 公交
        mode = 'transit'

    result = place_direction(ak, origin, dest, mode)
    if result[0] == NOSCHEME:
        text = '\n'.join(['输入的太模糊了, 你要找得起点可以选择:',
                          '|'.join(result[1]),
                          '终点可以选择:',
                          '|'.join(result[2])])
    elif result[0] == NODIRECTION:
        reg = ''
        if result[1]:
            reg += '起点'
        if result[2]:
            reg += '终点'
        msg = ['输入的{}太模糊了: 以下是参考:'.format(reg)] + \
            result[1] + result[2]

        text = '\n'.join(msg)
    else:
        if isinstance(result[1], list):
            _result = '\n'.join(result[1])
        else:
            _result = result[1].encode('utf-8')
        text = tmpl.format(_result, result[2].encode('utf-8'))
    return text


if __name__ == '__main__':
    print handle({'message': '我想从兆维工业园到北京南站'})
    print handle({'message': '我想从人大到北京南站'})
    print handle({'message': '我想从人大到豆瓣'})
    print handle({'message': '我想从兆维工业园到北京南站 步行'})
    print handle({'message': '我想从兆维工业园到北京南站 开车'})
    print handle({'message': '从酒仙桥去798'})
