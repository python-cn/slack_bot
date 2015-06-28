# coding=utf-8
from __future__ import division
from datetime import date

import jieba
import requests
from bs4 import BeautifulSoup

from slack_bot.ext import cache
from utils import check_cache

description = """
获取以下网站的活动列表:
http://segmentfault.com/events
http://huiyi.csdn.net/activity/home
http://www.chekucafe.com/Party
http://www.huodongxing.com/events
触发条件: "最近有什么活动 [城市名称] [私聊]"。比如:
* 最近有什么活动
* 最近有什么活动 北京
"""

TODAY = date.today().strftime('%m-%d')

# segmentfault
SF_URL = 'http://segmentfault.com'
SF_EVENT_URL = 'http://segmentfault.com/events?city={0}'
SF_CITIES_MAP = {
    u'\u4e0a\u6d77': 310100,
    u'\u5317\u4eac': 110100,
    u'\u5357\u4eac': 320100,
    u'\u53a6\u95e8': 350200,
    u'\u53f0\u5317': 710100,
    u'\u5408\u80a5': 340100,
    u'\u5e7f\u5dde': 440100,
    u'\u6210\u90fd': 510100,
    u'\u65b0\u52a0\u5761': 190,
    u'\u676d\u5dde': 330100,
    u'\u6b66\u6c49': 420100,
    u'\u6df1\u5733': 440300,
    u'\u70df\u53f0': 370600,
    u'\u897f\u5b89': 610100,
    u'\u957f\u6c99': 430100,
    u'\u97e9\u56fd': 198
}

# 活动行(默认是科技频道)
HDX_EVENT_URL = 'http://www.huodongxing.com/events?orderby=n&tag=%E7%A7%91%E6%8A%80&city{0}&page={1}'  # noqa
HDX_URL = 'http://www.huodongxing.com'
HDX_MAX_PAGE = 10

# 车库咖啡
CK_EVENT_URL = 'http://www.chekucafe.com/Party'
CK_URL = 'http://www.chekucafe.com'

# CSDN 最近一个月的
CSDN_EVENT_URL = 'http://huiyi.csdn.net/activity/home?c={0}&s=one_month&page={1}'  # noqa
CSDN_CITIES_MAP = {
    u'\u4e0a\u6d77': '2',
    u'\u4e91\u5357': '25',
    u'\u5185\u8499\u53e4': '7',
    u'\u5317\u4eac': '1',
    u'\u53f0\u6e7e': '34',
    u'\u5409\u6797': '9',
    u'\u56db\u5ddd': '23',
    u'\u5929\u6d25': '3',
    u'\u5b81\u590f': '29',
    u'\u5b89\u5fbd': '13',
    u'\u5c71\u4e1c': '16',
    u'\u5c71\u897f': '6',
    u'\u5e7f\u4e1c': '20',
    u'\u5e7f\u897f': '21',
    u'\u65b0\u7586': '31',
    u'\u6c5f\u82cf': '11',
    u'\u6c5f\u897f': '15',
    u'\u6cb3\u5317': '5',
    u'\u6cb3\u5357': '17',
    u'\u6d59\u6c5f': '12',
    u'\u6d77\u5357': '22',
    u'\u6e56\u5317': '18',
    u'\u6e56\u5357': '19',
    u'\u6fb3\u95e8': '33',
    u'\u7518\u8083': '28',
    u'\u798f\u5efa': '14',
    u'\u897f\u85cf': '26',
    u'\u8d35\u5dde': '24',
    u'\u8fbd\u5b81': '8',
    u'\u91cd\u5e86': '4',
    u'\u9655\u897f': '27',
    u'\u9752\u6d77': '30',
    u'\u9999\u6e2f': '32',
    u'\u9ed1\u9f99\u6c5f': '10'
}

FILTER_WORDS = [
    u'推广', u'论坛', u'产业', u'敏捷', u'管理', u'形势', u'研讨会', u'选拔',
    u'寻找', u'博览会', u'展', u'招募', u'会员', u'职业', u'嘉年华', u'内测',
    'office', u'报名', u'交流', u'讲座'
]
THRESHOLD = 0.7


def check_filter(title):
    for word in FILTER_WORDS:
        if word in title:
            return True
    return False


def get_df_events(city):
    id = SF_CITIES_MAP.get(city, SF_CITIES_MAP[u'北京'])
    r = requests.get(SF_EVENT_URL.format(id))
    soup = BeautifulSoup(r.text)
    for event in soup.findAll('div', {'class': 'widget-event'}):
        if u'报名' in event.find('a', {'class': 'btn-sm'}).text:
            h2 = event.find('h2')
            title = h2.text
            if check_filter(title):
                continue
            time, others = [i.text for i in event.findAll('li')]
            url = SF_URL + h2.find('a').attrs.get('href')
            yield title, url, time, others
        else:
            break


def get_hdx_events(city, res=[], page=1):
    r = requests.get(HDX_EVENT_URL.format(city.encode('utf-8'), page))
    soup = BeautifulSoup(r.text)
    uls = soup.findAll('ul', {'class': 'event-vertical-list-new'})
    for ul in uls:
        for li in ul.findAll('li'):
            a = li.find('h3').find('a')
            title = a.text
            if check_filter(title):
                continue
            pull = li.find('span', {'class': 'pull-right'}).text
            time = li.find(
                'div', {'class': 'time'}).text.replace(pull, '').strip()
            if time <= TODAY:
                continue
            favorites, user = pull.split('|')
            url = HDX_URL + a.attrs.get('href')
            res.append((title, url, time,
                        u'收藏: {0}| 报名: {1}'.format(favorites, user)))
    if page == HDX_MAX_PAGE:
        return res
    page += 1
    return get_hdx_events(city, res=res, page=page)


def get_ck_events(city):
    r = requests.get(CK_EVENT_URL)
    soup = BeautifulSoup(r.text)
    for li in soup.find(id='party-list').findAll('li'):
        title = li.find('h3').text
        if check_filter(title):
            continue
        url = CK_URL + li.find('a').attrs.get('href')
        tds = li.findAll('td')
        time = tds[0].text
        others = u'|'.join([td.text for td in tds[2:]])
        yield title, url, time, others


def get_csdn_events(city, res=[], page=1):
    id = CSDN_CITIES_MAP.get(city, CSDN_CITIES_MAP[u'北京'])
    r = requests.get(CSDN_EVENT_URL.format(id, page))
    soup = BeautifulSoup(r.text)
    for item in soup.find('div', {'class': 'list-wraper'}).findAll(
            'div', {'class': 'item'}):
        a = item.find('a')
        title = a.attrs.get('title')
        if check_filter(title):
            continue
        url = a.attrs.get('href')
        dd = item.findAll('dd')
        time = dd.pop(1).text
        others = u'|'.join([d.text.replace('\n', '.') for d in dd])
        res.append((title, url, time, others))

    # 判断是否有下一页
    nav = soup.find('span', {'class': 'page-nav'})
    if nav.find(
            'a', {'class': 'btn-next'}).attrs.get('href').endswith(str(page)):
        return res
    page += 1
    return get_csdn_events(city, res=res, page=page)


def check_similar(seg_, seg_lists):
    seg_len = len(seg_)
    for seg_list in seg_lists:
        seg_list_len = len(seg_list)
        len_ = seg_list_len if seg_len > seg_len else seg_len
        if len(seg_.intersection(seg_list)) / len_ > THRESHOLD:
            return True
    return False


def get_events(city):
    all_events = [
        ('SegmentFault', get_df_events(city)),
        (u'活动行', get_hdx_events(city)),
        ('csdn', get_csdn_events(city))
    ]
    if city == u'北京':
        all_events.insert(1, (u'车库咖啡', get_ck_events(city)))

    events = []
    seg_lists = []
    for org_name, org_events in all_events:
        for title, url, time, others in org_events:
            seg_ = set(jieba.cut(title))
            if check_similar(seg_, seg_lists):
                continue
            seg_lists.append(seg_)
            events.append(
                u'<{0}|[{1}] {2}> {3} {4}'.format(
                    url, org_name, title, time, others))
    return events


def test(data):
    return '最近有什么活动' in data['message']


def handle(data):
    message = data['message']
    if not isinstance(message, unicode):
        message = message.decode('utf-8')
    msg = message.split()
    if len(msg) == 1 or (len(msg) == 2 and u'私聊' in msg[1]):
        city = u'北京'
    else:
        city = msg[1]
    return '\n'.join(check_cache(cache, get_events, city))


if __name__ == '__main__':
    print handle({'message': '最近有什么活动'})
    print handle({'message': '最近有什么活动 上海'})
