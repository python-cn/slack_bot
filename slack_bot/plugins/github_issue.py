#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import current_app as app
import requests

description = """
当前 github 组织下所有未关闭的 issues && PR。触发条件: "issue [私聊]"。比如:
* issue
"""

ISSUE_API = "https://api.github.com/repos/{org}/{repo}/issues"
REPO_API = "https://api.github.com/orgs/{org}/repos"


def test(data):
    return 'issue' in data['message']


def handle(data):
    org_name = app.config.get('ORG_NAME', 'python-cn')
    repos = requests.get(REPO_API.format(org=org_name)).json()
    rv = ''
    for repo in repos:
        repo_name = repo['name']
        issues_count = repo['open_issues_count']
        if issues_count != 0:
            issues = requests.get(ISSUE_API.format(org=org_name,
                                                   repo=repo_name)).json()
            rv += '*{repo_name}\n'.format(repo_name=repo_name)
            for issue in issues:
                rv += 'Issue {}:'.format(issue['number'])
                rv += issue['title'].encode('utf-8') + '\n'
                rv += issue['html_url'].encode('utf-8') + '\n'
                rv += '\n'

    return rv if rv else 'no issue'


if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.config['org_name'] = 'python-cn'
    print handle(None)
