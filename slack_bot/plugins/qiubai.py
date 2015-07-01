# coding:utf-8

"""
Copyright (c) 2013 Xiangyu Ye<yexiangyu1985@gmail.com>

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

description = """
糗事百科TOP10。触发条件: "糗百 | 笑话 [私聊]"。比如:
* 糗百
* 笑话
"""

# 糗事百科TOP10
import urllib2
import re
import time
import random

from slack_bot.ext import cache

key = time.strftime('%y-%m-%d')


def test(data):
    return any(w in data['message'] for w in ['糗百', '笑话'])


def handle(data):
    if cache is not None:
        r = cache.get(key)
        if r:
            return random.choice(r)
    r = urllib2.urlopen('http://feedproxy.feedburner.com/qiubai', timeout=60)
    p = r.read()
    r = re.findall('<\!\[CDATA\[<p>(.*)<br/>', p)
    if r:
        if cache is not None:
            cache.set(key, r, 1800)
        return random.choice(r)
    else:
        raise Exception


if __name__ == '__main__':
    print handle({'message': '糗百'})
    print handle({'message': '笑话'})
