#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests


ISSUE_API = "https://api.github.com/repos/{org}/{repo}/issues"
REPO_API = "https://api.github.com/orgs/{org}/repos"


def test(data, bot):
    return 'issue' in data['message']


def handler(data, bot, *args, **kwarg):
    org_name = kwarg['org_name']
    repos = requests.get(REPO_API.format(org=org_name)).json()
    rv = ''
    for repo in repos:
        repo_name = repo['name']
        issues_count = repo['open_issues_count']
        if issues_count != 0:
            issues = requests.get(ISSUE_API.format(org=org_name,
                                                   repo=repo_name)).json()
            rv += '*{repo_name}\n'.format(repo_name=repo_name)
            for idx, issue in enumerate(issues):
                rv += 'Bug {}:'.format(idx+1)
                rv += issue['title'].encode('utf-8') + '\n'
                rv += issue['url'].encode('utf-8') + '\n'
                rv += '\n'

    return rv if rv else 'no issue'


if __name__ == '__main__':
    print handler(None, None, kv=None, org_name='python-cn')