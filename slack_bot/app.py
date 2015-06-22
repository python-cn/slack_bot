# coding=utf-8
import os
from functools import partial

from flask import Flask

from flask_slackbot import SlackBot

import settings
import plugins
from ext import redis_store, cache


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
    app.plugin_modules = plugin_modules

    slackbot = SlackBot(app)
    _callback = partial(callback, app=app)
    slackbot.set_handler(_callback)
    slackbot.filter_outgoing(_filter)

    return app


def replaced(message, rep_words):
    for word in rep_words:
        message = message.replace(word, '', 1)
    return message


def callback(kwargs, app):
    s = kwargs['text']
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    private = True if 'private' in s or '私聊' in s else False
    attachmented = True if '带图' in s or '附件' in s else False
    data = {
        'message': replaced(s, ['private', '私聊', '带图', '附件']).strip()
    }

    if not data['message']:
        return {'text': ''}

    for plugin_module in plugin_modules:
        if plugin_module.test(data):
            ret = plugin_module.handle(data, cache=cache, app=app)
            if not isinstance(ret, tuple):
                text = ret
                attaches = None
            else:
                text, attaches = ret
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
