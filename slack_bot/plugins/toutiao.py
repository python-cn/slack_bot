# coding=utf-8

import requests

from utils import datetime2timestamp

CHANNEL_MAPS = {
    '推荐': '__all__',
    '热点': 'news_hot',
    '社会': 'news_society',
    '娱乐': 'news_entertainment',
    '科技': 'news_tech',
    '军事': 'news_military',
    '美食': 'news_food',
    '游戏': 'news_game',
    '体育': 'news_sports'
}


API = 'http://toutiao.com/api/article/recent/?source=2&count=20&category={0}&max_behot_time={1}&utm_source=toutiao&offset=0'  # noqa


def get_content(channel):
    if channel not in CHANNEL_MAPS:
        return '目前可选的频道包含: {}'.format('|'.join(CHANNEL_MAPS.keys()))
    category = CHANNEL_MAPS.get(channel)
    r = requests.get(API.format(category, datetime2timestamp()))
    data = r.json()['data']

    return '\n'.join([
        (u'<{seo_url}|{title}> 赞{bury_count} 踩{digg_count} - '
         '{source} {datetime}').format(**i) for i in data])


def test(data, bot):
    return any(w in data['message'] for w in ['toutiao', '头条'])


def handle(data, bot, cache=None, app=None):
    msg = data['message'].split()
    channel = '推荐' if len(msg) == 1 else msg[1].strip()
    return get_content(channel)


if __name__ == '__main__':
    print handle({'message': '头条'}, None, None, None)
