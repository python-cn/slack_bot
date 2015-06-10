# coding=utf-8
from flask import Flask

from flask_slackbot import SlackBot

import settings
import plugins
from ext import redis_store


plugin_modules = []
for plugin_name in plugins.__all__:
    __import__('slack_bot.plugins.%s' % plugin_name)
    plugin_modules.append(getattr(plugins, plugin_name))


def callback(kwargs):
    s = kwargs['text']
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    data = {'message': s}
    bot = None
    for plugin_module in plugin_modules:
        if plugin_module.test(data, bot):
            return {'text': '!' + plugin_module.handle(data, bot, kv=None)}

    return {'text': '!呵呵'}


def _filter(line):
    return line.startswith('!')


def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    app.debug = True
    redis_store.init_app(app)
    slackbot = SlackBot(app)
    slackbot.set_handler(callback)
    slackbot.filter_outgoing(_filter)
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
