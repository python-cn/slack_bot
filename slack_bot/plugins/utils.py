# coding=utf-8
import os
import re
import random
import shutil
import calendar
from datetime import datetime

from flask import current_app
import pytz
import requests
from slacker import Slacker
from pypinyin import lazy_pinyin

from consts import ONE_DAY, COLORS

CANVAS_REGEX = re.compile(r'base64,(.*)')


def check_cache(cache, fn, *args, **kwargs):
    timeout = kwargs.get('timeout', ONE_DAY)
    return (cache.cached(timeout=timeout)(fn)
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


def check_time(dt=None, timezone='Asia/Shanghai'):
    if dt is None:
        dt = datetime.now()
    tz = pytz.timezone(timezone)
    dt = dt.replace(tzinfo=pytz.utc).astimezone(tz)
    return 'day' if 6 <= dt.hour <= 18 else 'night'


def to_pinyin(word):
    if not isinstance(word, unicode):
        word = word.decode('utf-8')
    return ''.join(lazy_pinyin(word))


def chinese2digit(ch):
    try:
        return ['一', '二', '三', '四', '五', '六', '七',
                '八', '九'].index(ch) + 1
    except ValueError:
        return ch


def upload_image(canvas_or_url, image_type, app=None, filename=None,
                 tmp_dir=None, deleted=False):
    here = os.path.abspath(os.path.dirname(__file__))
    if tmp_dir is None:
        tmp_dir = os.path.join(here, 'data')
    match = CANVAS_REGEX.search(canvas_or_url)
    if match:
        imgstr = match.group(1)
        if filename is None:
            filename = os.path.join(tmp_dir, '{}.png'.format(imgstr[:20]))
        output = open(filename, 'wb')
        output.write(imgstr.decode('base64'))
        output.close()
    else:
        r = requests.get(canvas_or_url, stream=True)
        if filename is None:
            filename = canvas_or_url.rsplit('/', 1)[1]
        with open(filename, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    if image_type == 'thumb':
        image_type = 'thumb_360'
    if app is None:
        token = 'xoxp-4231087425-4231087427-4463321974-03a74ae'
    else:
        token = app.config.get('SLACK_CHAT_TOKEN')
    slack = Slacker(token)
    ret = slack.files.upload(filename)
    if deleted:
        os.remove(filename)
    try:
        return ret.body['file'][image_type]
    except KeyError:
        return ret.body['file']['url']


def check_canvas(image_url, image_type):
    match = CANVAS_REGEX.search(image_url)
    if match:
        return upload_image(image_url, image_type)
    else:
        return image_url


def convert2unicode(s):
    if not isinstance(s, unicode):
        return s.decode('utf-8')
    return s


def convert2str(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return s


def gen_attachment(text, image_url='', image_type='url', title='',
                   title_link='', color='random', fallback=True):
    if color == 'random':
        color = random.choice(COLORS)
    key = 'thumb_url' if image_type == 'thumb' else 'image_url'
    attachment = {'text': text, 'title_link': title_link, 'color': color,
                  key: check_canvas(image_url, image_type),
                  'title': title}
    if fallback:
        attachment.update({
            'fallback': u'{0} {1}'.format(
                convert2unicode(title), convert2unicode(text))
        })
    return attachment


def trunc_utf8(s, length=50):
    s = convert2unicode(s)
    if s > length:
        s = s[:length] + '...'
    return s


def replaced(message, rep_words):
    for word in rep_words:
        message = message.replace(word, '', 1)
    return message
