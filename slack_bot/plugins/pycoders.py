# coding=utf-8
import re
from HTMLParser import HTMLParser

import requests
from bs4 import BeautifulSoup

from slack_bot.ext import cache
from utils import check_cache

description = """
Pycoders Weekly。触发条件: "pycoders [list | ISSUE_ID] [私聊]"。比如:
* pycoders
* pycoders list
* pycoders 20
"""

API = 'http://us4.campaign-archive1.com/generate-js/?u=9735795484d2e4c204da82a29&fid=1817&show=500'  # noqa
ISSUES_REGEX = re.compile(r'<div class=\\"campaign\\">(.*?)<\\/a><\\/div>')
ISSUE_REGEX = re.compile(
    ur'(\d+\\/\d+\\/\d+).*href=\\"(.*)\\" title=\\"(.*?)\\"', re.UNICODE)  # noqa
TITLE_REGEX = re.compile(ur'Issue(.*)\)(\W*?):(\W*?)(.*)', re.UNICODE)  # noqa
SPAN_REGEX = re.compile(r'<span.*>(.*)</span>')

GET_ISSUE_KEY = 'pycoders:issue:{0}'
LIST_ISSUE_KEY = 'pycoders:issue:list'


class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self._tag = tag
        for name, value in attrs:
            if name == 'href':
                self._href = value

    def handle_data(self, data):
        self._data = data


def get_all_issues():
    r = requests.get(API)
    issues = ISSUES_REGEX.findall(r.text)
    for issue in issues:
        date_, url, title = ISSUE_REGEX.search(issue).groups()
        date_ = date_.replace('\\', '')
        url = url.replace('\\', '')
        match = TITLE_REGEX.search(title)
        if match:
            no, _, _, title = match.groups()
            no = no.strip()
            title = title.strip().replace('\u00a0', '')
        else:
            title = title.replace('Pycoders Weekly', '').strip()
            no = ''
        yield date_, url, no, title


def prase_tag(tag):
    text = ''
    parser = MyHTMLParser()
    count = 0
    block = [None] * 3  # [url, title, content]
    for t in tag.contents:
        t = unicode(t).strip()
        if not t or t in ('<br/>') or 'Shared by' in t:
            continue
        parser.feed(t)
        if parser._tag == 'h2':
            if text:
                text += '\n\n'
            text += parser._data + '\n'
        elif parser._tag == 'a':
            if not count % 2:
                block[0] = parser._href
            count += 1
        elif parser._tag == 'span':
            if t.startswith('<a'):
                match = SPAN_REGEX.search(t)
                if match:
                    block[1] = match.group(1)
            else:
                block[2] = parser._data
        if not filter(lambda x: x is None, block):
            text += u'<{0} |{1}>{2}'.format(*block) + '\n'
            block = [None] * 3
            parser._tag = None
            parser._href = None
            parser._data = None
    return text


def parse_issue_page(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    return '\n'.join([
        prase_tag(soup.findAll('td', {'class': 'mcnTextContent'})[index])
        for index in (6, 8, 9)
    ])


def get_issue(num=None):
    issues = list(get_all_issues())
    if num is None:
        num = len(issues)
    try:
        issue = list(get_all_issues())[::-1][num-1]
    except IndexError:
        return u'找不到这期咯'
    return parse_issue_page(issue[1])


def list_issues():
    return '\n'.join([
        '{0} <{1} |Issue {2}: {3}>'.format(date_, url, no, title)
        for date_, url, no, title in get_all_issues()
    ])


def test(data):
    return 'pycoder' in data['message']


def handle(data):
    msg = data['message'].split()
    if len(msg) == 1:
        return check_cache(cache, get_issue)
    elif msg[1] == 'list':
        return check_cache(cache, list_issues)
    elif msg[1].isdigit():
        return check_cache(cache, get_issue, int(msg[1]))
    return ('`pycoder`默认获得最近一次的weekly\n'
            '`pycoder list`获取全部weekly列表\n'
            '`pycoder X`获得第X次weekly')


if __name__ == '__main__':
    print handle({'message': 'pycoder'})
    print handle({'message': 'pycoder list'})
    print handle({'message': 'pycoder 167'})
