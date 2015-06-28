# coding=utf-8
import cgi
from datetime import datetime

from lxml import etree
import requests

from slack_bot.ext import cache
from consts import ONE_DAY, ONE_MINUTE

NODES = ['linux', 'macosx', 'create', 'android', 'python', 'programmer', 'vim',
         'jobs', 'react', 'beijing', 'redis', 'mongodb', 'tornado', 'emacs',
         'django', 'flask', 'go', 'lisp']
TAGS = ['title', 'published', 'updated', 'content']
MAX_FEEDS_LEN = 50
FEED_URL = 'https://www.v2ex.com/feed/{0}.xml'
TOPIC_URL = 'http://www.v2ex.com/t/{0}'
NODE_URL = 'http://www.v2ex.com/go/{0}'
NODE_KEY = 'v2ex:node:{0}'
TOPIC_KEY = 'v2ex:topic:{0}'
NODE_UPDATE_KEY = 'v2ex:update:{0}'  # node 缓存时间根据发布topic频繁程度而不同
description = """
v2ex feed. 触发条件: "v2ex [%s] [私聊]". 比如:
* v2ex
* v2ex python
""" % ' | '.join(NODES)


def get_updated_interval(node_name, feeds, default=ONE_DAY):
    updated_times = []
    for id in feeds:
        topic = cache.get(TOPIC_KEY.format(id))
        if topic:
            updated_times.append(topic['updated'])
        else:
            print 'topic {} not cached!'.format(id)
    min = default
    for i in range(len(updated_times) - 1):
        sec = (updated_times[i] - updated_times[i + 1]).total_seconds()
        if sec < min:
            min = sec
        if min < ONE_MINUTE:
            min = ONE_MINUTE
            break
    return min


def fetch2cache(node_name):
    print 'Fetch {}'.format(node_name)
    r = requests.get(FEED_URL.format(node_name), verify=False)
    root = etree.fromstring(r.text.encode('utf-8'))
    entries = root.findall('{http://www.w3.org/2005/Atom}entry')
    node_key = NODE_KEY.format(node_name)
    feeds = cache.get(node_key) or []
    new_feeds = []
    for entry in entries:
        topic = {}
        id = entry[2].text.rpartition('/')[-1]
        key = TOPIC_KEY.format(id)
        for el in entry:
            for tag in TAGS:
                if el.tag.endswith(tag):
                    res = el.text
                    if tag in ('published', 'updated'):
                        res = datetime.strptime(res, '%Y-%m-%dT%H:%M:%SZ')
                    topic[tag] = res
            topic['node'] = node_name
        cache.set(key, topic, ONE_DAY)
        new_feeds.append(id)
    if new_feeds:
        new_feeds += feeds[:MAX_FEEDS_LEN - len(new_feeds)]
        interval = get_updated_interval(node_name, new_feeds)
        cache.set(node_key, new_feeds, interval)


def fetch(force=False):
    ids = set()
    for node in NODES:
        node_key = NODE_KEY.format(node)
        res = cache.get(node_key)
        if res and not force:
            ids.update(res)
            continue
        fetch2cache(node)
        ids.update(cache.get(node_key))
    ids = list(set(ids))

    def _key(id):
        topic = cache.get(TOPIC_KEY.format(id))
        if not topic:
            return datetime(1970, 1, 1)
        return topic['published']

    return sorted(ids, key=_key, reverse=True)[:MAX_FEEDS_LEN]


def test(data):
    return data['message'].startswith('v2ex')


def handle(data):
    message = data['message']
    ids = fetch(force=(True if u'刷新' in message else False))
    contents = []
    for id in ids:
        topic = cache.get(TOPIC_KEY.format(id))
        if not topic:
            continue
        node = topic['node']
        msg = u'<{0}|{1} [{2}]>   <{3}|{4}>'.format(TOPIC_URL.format(id),
                                                    cgi.escape(topic['title']),
                                                    topic['published'],
                                                    NODE_URL.format(node),
                                                    node)
        contents.append(msg)
    return '\n'.join(contents)


if __name__ == '__main__':
    pass
    # 由于更换了cache引入方式，这里的测试暂不可用，如有需要在`python manager send v2ex`
    # from flask import Flask
    # from flask_cache import Cache
    # app = Flask(__name__)
    # cache = Cache()
    # cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    # with app.app_context():
    #     print handle({'message': 'v2ex'})
