# coding=utf-8
import os
import re

from flask import Flask

from flask_slackbot import SlackBot

import settings
import plugins
from ext import redis_store, cache
from utils import timeout
from plugins.utils import convert2str, replaced


plugin_modules = []
for plugin_name in plugins.__all__:
    __import__('slack_bot.plugins.%s' % plugin_name)
    plugin_modules.append(getattr(plugins, plugin_name))


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(settings)

    if isinstance(config, dict):
        app.config.update(config)
    elif config:
        app.config.from_pyfile(os.path.realpath(config))

    redis_store.init_app(app)
    cache.init_app(app)
    app.cache = cache
    app.plugin_modules = plugin_modules

    slackbot = SlackBot(app)
    slackbot.set_handler(callback)
    slackbot.filter_outgoing(_filter)

    return app


def callback(kwargs):
    s = convert2str(kwargs['text'])
    trigger_word = convert2str(kwargs['trigger_word'])
    # remove trigger_words
    if trigger_word is not None:
        s = replaced(s, trigger_word.split(','))
    # remove metion block
    s = re.sub(r'(@.*?)\W', '', s)
    private = any([word in s for word in ['private', '私聊']])
    attachmented = any([word in s for word in ['带图', '附件']])
    data = {
        'message': replaced(s, ['private', '私聊', '带图', '附件']).strip()
    }

    if not data['message']:
        return {'text': ''}

    for plugin_module in plugin_modules:
        if plugin_module.test(data):
            ret = plugin_module.handle(data)
            if not isinstance(ret, tuple):
                text = ret
                attaches = None
            else:
                text, attaches = ret
            if trigger_word is None:
                text = '!' + text
            if attachmented and attaches:
                return {'text': ' ', 'private': private,
                        'attachments': attaches}
            return {'text': text, 'private': private}

    return {'text': '!呵呵'}


def _filter(line):
    return line.startswith('!')


if __name__ == '__main__':
    app = create_app()
    app.debug = True
    app.run()
