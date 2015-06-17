# coding=utf-8
from functools import partial
import os

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

    slackbot = SlackBot(app)
    _callback = partial(callback, app=app)
    slackbot.set_handler(_callback)
    slackbot.filter_outgoing(_filter)

    return app


def callback(kwargs, app):
    s = kwargs['text']
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    private = True if 'private' in s or '私聊' in s else False
    data = {'message': s.replace('私聊', '', 1)}
    bot = None
    for plugin_module in plugin_modules:
        if plugin_module.test(data, bot):
            rv = plugin_module.handle(data, bot, cache=cache, app=app)
            return {'text': '!' + rv, 'private': private}

    return {'text': '!呵呵'}


def _filter(line):
    return line.startswith('!')


if __name__ == '__main__':
    app = create_app()
    app.debug = True
    app.run()
