# coding=utf-8

import requests
from bs4 import BeautifulSoup

from utils import to_pinyin, gen_attachment

description = """
最近上映的电影信息。触发条件:
"[上映 | 热映 | 有什么 | 将] 电影 [上映 | 热映 | 有什么 | 将] [城市名称] [带图] [私聊]"
比如:
* 最近要将上映的电影
* 有什么电影 上海
"""

CURRENT_URL = 'http://movie.douban.com/nowplaying/{0}/'
LATER_URL = 'http://movie.douban.com/later/{0}/'


def get_later_movie_info(city):
    r = requests.get(LATER_URL.format(city))
    soup = BeautifulSoup(r.text)
    items = soup.find(id='showing-soon').findAll('div', {'item'})
    for i in items:
        h = i.find('h3').find('a')
        url = h.attrs['href']
        title = h.text
        content = '|'.join([li.text for li in i.findAll('li')[:4]])
        image_url = i.find('a').find('img').attrs.get('src', '')
        yield u'<{url}|{title}> {content}'.format(**locals()), gen_attachment(
            content, image_url.replace('spst', 'mpst'), image_type='thumb',
            title=title, title_link=url)


def get_current_movie_info(city):
    r = requests.get(CURRENT_URL.format(city))
    soup = BeautifulSoup(r.text)
    items = soup.find(id='nowplaying').find('ul', {'class': 'lists'}).findAll(
        'li', {'class': 'poster'})
    for i in items:
        img = i.find('img')
        title = img.attrs.get('alt', '')
        content = '|'.join([li.text for li in i.findAll('li')[:4]])
        url = i.find('a').attrs.get('href', '')
        image_url = img.attrs.get('src', '')
        yield u'<{url}|{title}>'.format(**locals()), gen_attachment(
            content, image_url.replace('spst', 'mpst'), image_type='thumb',
            title=title, title_link=url)


def test(data):
    return '电影' in data['message'] and \
        any([i in data['message'] for i in ['上映', '热映', '有什么', '将']])


def handle(data, cache=None, app=None):
    message = data['message']
    if not isinstance(message, unicode):
        message = message.decode('utf-8')
    msg = message.split()
    if len(msg) == 1 or (len(msg) == 2 and u'私聊' in msg[1]):
        city = 'beijing'
    else:
        city = to_pinyin(msg[1])
    if u'将' in message:
        fn = get_later_movie_info
    else:
        fn = get_current_movie_info
    ret = [r for r in fn(city)]
    return '\n'.join([r[0] for r in ret]), [r[1] for r in ret]


if __name__ == '__main__':
    print handle({'message': '最近要将上映的电影'}, None, None)
    print handle({'message': '有什么电影 上海'}, None, None)
