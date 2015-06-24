# coding=utf-8
import json
from pprint import pprint

from flask import current_app
from flask_script import Manager, Server

from slack_bot.app import create_app

manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config', required=False)
manager.add_command(
    'runserver', Server(use_debugger=True, use_reloader=True, host='0.0.0.0')
)


@manager.option('text')
def send(text):
    """Send text to slack callback url"""
    data = current_app.config['TEST_DATA']
    uri = current_app.config['SLACK_CALLBACK']
    client = current_app.test_client()

    data['text'] = text
    rv = client.post(uri, data=data)
    if rv.status_code == 200:
        body = rv.data
        if not body:
            print('Response body is empty!')
            return

        obj = json.loads(body)
        if not obj.get('attachments'):
            obj = obj['text']
            print(obj)
        else:
            pprint(obj)
    else:
        print('Error!\nstatus code: %s\nbody: %s' % (rv.status_code, rv.data))

if __name__ == '__main__':
    manager.run()
