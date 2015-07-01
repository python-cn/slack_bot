# coding=utf-8
from flask import current_app

description = """
帮助信息，触发条件: "help [私聊]". 比如:
* help
"""


def format_desc(plugin, prefix='  '):
    name = plugin.__name__.split('.')[-1]
    desc = getattr(plugin, 'description', '').strip()
    # 为每行内容增加前缀
    desc = ('\n' + prefix).join(desc.split('\n'))
    return '{name}:\n{prefix}{desc}'.format(
        name=name, prefix=prefix, desc=desc
    )


def test(data):
    return 'help' in data['message']


def handle(data):
    app = current_app
    plugin_modules = app.plugin_modules if app else []
    docs = []
    for plugin in plugin_modules:
        docs.append(format_desc(plugin))
    return '\n'.join(docs)
