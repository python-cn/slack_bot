# coding=utf-8
import re

import requests
from bs4 import BeautifulSoup

from slack_bot.ext import cache
from utils import check_cache
from pycoders import MyHTMLParser

URL = 'http://us2.campaign-archive1.com/home/?u=e2e180baf855ac797ef407fc7&id=9e26887fc5'  # noqa
ISSUE_REGEX = re.compile(r'(\d+\/\d+\/\d+).*Issue\W+(\d+)')
GET_ISSUE_KEY = 'pythonweekly:issue:{0}'
LIST_ISSUE_KEY = 'pythonweekly:issue:list'
MAX_LENGTH = 120

description = """
Python Weekly。触发条件: "pythonweekly [list | ISSUE_ID] [私聊]"。比如:
* pythonweekly
* pythonweekly list
* pythonweekly 20
"""


def get_all_issues():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text)
    for li in soup.findAll('li', {'class': 'campaign'}):
        url = li.find('a').attrs.get('href')
        time, no = ISSUE_REGEX.search(li.text).groups()
        yield url, no, time


def parse_issue_page(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    tag = soup.find('td', {'class': 'defaultText'})
    text = []
    parser = MyHTMLParser()
    start = False
    block = [None] * 3  # [url, title, content]
    for t in tag.contents:
        t = unicode(t).strip()
        if not t or t in ('<br/>'):
            continue
        parser.feed(t)
        if parser._data == 'News':
            start = True
        if not start:
            continue
        if parser._tag == 'a':
            block[1] = parser._data
            block[0] = parser._href
        elif '<' not in t:
            if parser._data < MAX_LENGTH:
                block[2] = parser._data
            else:
                block[2] = parser._data[:MAX_LENGTH] + '...'
        elif parser._tag == 'span':
            text.append('\n{}'.format(parser._data))
        parser._tag = None
        parser._href = None
        parser._data = None
        if not filter(lambda x: x is None, block):
            text.append(u'<{0} |{1}>{2}'.format(*block))
            block = [None] * 3
    return '\n'.join(text)


def list_lastest_issues():
    return '\n'.join([
        '<{0} |Issue {1}: {2}>'.format(url, no, time)
        for url, no, time in get_all_issues()
    ])


def get_issue_pw(num=None):
    issues = list(get_all_issues())
    if num is None:
        num = len(issues)
    try:
        issue = list(get_all_issues())[::-1][num-1]
    except IndexError:
        return u'找不到这期咯'
    return parse_issue_page(issue[0])


def test(data):
    return all([i in data['message'] for i in ['python', 'weekly']])


def handle(data):
    msg = data['message'].split()
    if len(msg) == 1:
        return check_cache(cache, get_issue_pw)
    elif msg[1] == 'list':
        return check_cache(cache, list_lastest_issues)
    elif msg[1].isdigit():
        return check_cache(cache, get_issue_pw, int(msg[1]))
    return ('`pythonweekly`默认获得最近一次的weekly\n'
            '`pythonweekly list`获取最近20个weekly列表(找不到更早的了)\n'
            '`pythonweekly X`获得倒数第X次weekly(X不能超过20)')


if __name__ == '__main__':
    print handle({'message': 'pythonweekly'})
    print handle({'message': 'pythonweekly list'})
    print handle({'message': 'pythonweekly 1'})
