# coding=utf-8
import calendar
from datetime import datetime

import pytz
from pypinyin import lazy_pinyin

from consts import ONE_DAY


def check_cache(cache, fn, *args, **kwargs):
    timeout = kwargs.get('timeout', ONE_DAY)
    return (cache.cached(timeout=timeout)(fn) \
            if cache is not None else fn)(*args, **kwargs)


def timestamp2str(timestamp, fmt='%H:%M:%S', timezone='Asia/Shanghai'):
    dt = datetime.utcfromtimestamp(float(timestamp)).replace(tzinfo=pytz.utc)
    tz = pytz.timezone(timezone)
    return tz.normalize(dt.astimezone(tz)).strftime(fmt)


def datetime2timestamp(dt=None, timezone='Asia/Shanghai'):
    if dt is None:
        dt = datetime.now()
    tz = pytz.timezone(timezone)
    dt = dt.replace(tzinfo=pytz.utc).astimezone(tz)
    return calendar.timegm(dt.timetuple())


def to_pinyin(word):
    if not isinstance(word, unicode):
        word = word.decode('utf-8')
    return ''.join(lazy_pinyin(word))


def chinese2digit(ch):
    return ['一', '二', '三', '四', '五', '六', '七', '八', '九'].index(ch) + 1
