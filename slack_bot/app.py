# coding=utf-8
from flask import Flask, request
from flask import render_template

from flask_slackbot import SlackBot


app = Flask(__name__)
app.config['SLACK_TOKEN'] = 'jLGMzrZn3P1lS2sD848KpPuN'
app.config['SLACK_CALLBACK'] = '/slack_callback'
app.debug = True
slackbot = SlackBot(app)


def fn(kwargs):
    return {'text': '!' + kwargs['text']}

def fn2(line):
    return line.startswith('!')


slackbot.set_handler(fn)
slackbot.filter_outgoing(fn2)


if __name__ == '__main__':
    app.run()
