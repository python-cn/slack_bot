# -*-coding:utf-8-*-

"""
Copyright (c) 2012 yangzhe1991 <ud1937@gmail.com>

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

# 维基百科

from bs4 import BeautifulSoup

import requests
import re

description = """
维基百科。触发条件: "什么是 内容 [私聊]"。比如:
* 什么是薛定谔方程啊
* 什么是CSS
"""


def test(data):
    return '什么是' in data['message']


def handle(data):
    m = re.search('(?<=什么是)(.+?)(?=啊|那|呢|哈|！|。|？|\?|\s|\Z)', data['message'])
    if m and m.groups():
        return wikipedia(m.groups()[0])
    raise Exception


def wikipedia(title):
    r = requests.get('http://zh.wikipedia.org/wiki/{0}'.format(title),
                     timeout=10)
    soup = BeautifulSoup(r.text)
    result = soup.find(id='mw-content-text').find('p').text
    return result if result else '我还不知道哎'

if __name__ == '__main__':
    for message in ['什么是SVM  ????', '什么是薛定谔方程啊', '什么是CSS？']:
        data = {'message': message}
        print message, test(data)
        if test(data):
            print handle(data)
