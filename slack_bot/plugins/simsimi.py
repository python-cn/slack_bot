# -*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>
Copyright (c) 2012 hupili <hpl1989@gmail.com>

Original Author:
    Wong2 <wonderfuly@gmail.com>
Changes Statement:
    Changes made by Pili Hu <hpl1989@gmail.com> on
    Jan 13 2013:
        Support Keepalive by using requests.Session

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


# 从simsimi读数据

import sys
sys.path.append('..')

import requests
import random

try:
    from settings import SIMSIMI_KEY
except:
    SIMSIMI_KEY = '50c086cb-5ea3-4190-bdd6-69787a540ec4'

description = """
色色的小黄鸡。触发条件：所有未触发其他插件的内容。
"""

COOKIE = """
sid=s%3AcsxS39Tq1oLXQj5WKdBN7UZz.T%2FdtU%2BGkt056rKQb
%2BwmwD0iJXguRCsyRsv6745ftwfk; Filtering=0.0; Filtering=0.0;
isFirst=1; isFirst=1; simsimi_uid=102256985; simsimi_uid=102256985;
selected_nc_name=Chinese%20%u2013%20Simplified%20%28%u7C21%u9AD4%29;
selected_nc_name=Chinese%20%u2013%20Simplified%20%28%u7C21%u9AD4%29;
simsimi_makeup=undefined; simsimi_makeup=undefined; selected_nc=ch;
selected_nc=ch; __utmt=1; __utma=119922954.1015526052.1433822720.
1433826650.1433836017.4; __utmb=119922954.8.9.1433836034315;
__utmc=119922954; __utmz=119922954.1433822720.1.1.utmcsr=(direct)
|utmccn=(direct)|utmcmd=(none)
"""


class SimSimi:

    def __init__(self):

        self.session = requests.Session()

        self.chat_url = (
            'http://www.simsimi.com/func/reqN?lc=ch&ft=0.0&req={0}'
            '&fl=http%3A%2F%2Fwww.simsimi.com%2Ftalk.htm&reqType='
        )
        self.api_url = ('http://sandbox.api.simsimi.com/request.p?'
                        'key=%s&lc=ch&ft=1.0&text=%s')

        if not SIMSIMI_KEY:
            self.initSimSimiCookie()

    def initSimSimiCookie(self):
        self.session.headers.update(
            {'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)'
                            ' AppleWebKit/537.36 (KHTML, like Gecko)'
                            ' Chrome/43.0.2357.81 Safari/537.36')}
        )
        self.session.get('http://www.simsimi.com/talk.htm')
        self.session.headers.update(
            {'Referer': 'http://www.simsimi.com/talk.htm'})
        self.session.get('http://www.simsimi.com/talk.htm?lc=ch')
        self.session.headers.update(
            {'Referer': 'http://www.simsimi.com/talk.htm?lc=ch'})
        self.session.headers.update(
            {'Accept': 'application/json, text/javascript, */*; q=0.01'})
        self.session.headers.update({'Accept-Encoding': 'gzip, deflate, sdch'})
        self.session.headers.update(
            {'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'})
        self.session.headers.update({'Cache-Control': 'no-cache'})
        self.session.headers.update({'Connection': 'keep-alive'})
        self.session.headers.update(
            {'Content-Type': 'application/json; charset=utf-8'})
        self.session.headers.update({'Host': 'www.simsimi.com'})
        self.session.headers.update({'Pragma': 'no-cache'})
        self.session.headers.update({'X-Requested-With': 'XMLHttpRequest'})
        self.session.headers.update(
            {'Cookie': COOKIE})

    def getSimSimiResult(self, message, method='normal'):
        if method == 'normal':
            print self.chat_url.format(message)
            r = self.session.get(self.chat_url.format(message))
        else:
            url = self.api_url % (SIMSIMI_KEY, message)
            r = requests.get(url)
        return r

    def chat(self, message=''):
        if message:
            r = self.getSimSimiResult(
                message, 'normal' if not SIMSIMI_KEY else 'api')
            try:
                answer = r.json()['response'].encode('utf-8')
                return answer
            except:
                return random.choice(['呵呵', '。。。', '= =', '=。='])
        else:
            return '叫我干嘛'

simsimi = SimSimi()


def test(data):
    return True


def handle(data):
    return simsimi.chat(data['message']), None

if __name__ == '__main__':
    print handle({'message': '最后一个问题'})
    print handle({'message': '还有一个问题'})
    print handle({'message': '其实我有三个问题'})
