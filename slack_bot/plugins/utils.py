# coding=utf-8
import calendar
from datetime import datetime

import pytz


def check_cache(cache, fn, *args, **kwargs):
    return (cache.cached(fn) if cache is not None else fn)(*args, **kwargs)


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
