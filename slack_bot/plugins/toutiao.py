# coding=utf-8

import requests

from utils import datetime2timestamp, gen_attachment, trunc_utf8

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

description = """
今日头条。触发条件: "头条 [%s] [带图] [私聊]"。比如:
* 头条
* 头条 娱乐
""" % ' | '.join(CHANNEL_MAPS.keys())


API = 'http://toutiao.com/api/article/recent/?source=2&count=20&category={0}&max_behot_time={1}&utm_source=toutiao&offset=0'  # noqa


def get_content(channel):
    category = CHANNEL_MAPS.get(channel)
    r = requests.get(API.format(category, datetime2timestamp()))
    data = r.json()['data']

    for i in data:
        text = (u'<{seo_url}|{title}> 赞{bury_count} 踩{digg_count} - '
                '{source} {datetime}').format(**i)
        image_url = i.get('middle_image', '')
        if isinstance(image_url, dict):
            image_url = image_url['url']
        attach = gen_attachment(trunc_utf8(i['abstract']), image_url,
                                image_type='thumb', title=i['title'],
                                title_link=i['seo_url'], fallback=False)
        yield text, attach


def test(data):
    return any(w in data['message'] for w in ['toutiao', '头条'])


def handle(data):
    msg = data['message'].split()
    channel = '推荐' if len(msg) == 1 else msg[1].strip()
    if channel not in CHANNEL_MAPS:
        return '目前可选的频道包含: {}'.format('|'.join(CHANNEL_MAPS.keys()))
    ret = [r for r in get_content(channel)]
    return '\n'.join([r[0] for r in ret]), [r[1] for r in ret]


if __name__ == '__main__':
    print handle({'message': '头条'})
