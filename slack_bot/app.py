# coding=utf-8
from flask import Flask

from flask_slackbot import SlackBot

import settings
import plugins
from ext import redis_store, cache


plugin_modules = []
for plugin_name in plugins.__all__:
    __import__('slack_bot.plugins.%s' % plugin_name)
    plugin_modules.append(getattr(plugins, plugin_name))


def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    app.debug = True
    redis_store.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': app.config.get('CACHE_TYPE')})
    return app

app = create_app()


def callback(kwargs):
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


slackbot = SlackBot(app)
slackbot.set_handler(callback)
slackbot.filter_outgoing(_filter)

if __name__ == '__main__':
    app.run()
