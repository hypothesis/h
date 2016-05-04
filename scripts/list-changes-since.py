#!/usr/bin/env python

import argparse
import re
import requests
import subprocess
import textwrap
from subprocess import PIPE

GITHUB_API_URL = 'https://api.github.com'


class CompletedProcess(object):
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr


# Replace with subprocess.run() when we move to Python 3
def run(args, **kw):
    proc = subprocess.Popen(args, **kw)
    (stdout, stderr) = proc.communicate()
    return CompletedProcess(stdout, stderr)


class PRInfo(object):
    def __init__(self, id, title):
        self.id = id
        self.title = title


def get_last_tag():
    tags = run(['git','tag','--list','--sort=-taggerdate'],
        stdout=PIPE)
    return tags.stdout.decode().splitlines()[0]


def get_prs_closed_since(version):
    git_list_result = run(['git','log','--oneline','{}..master'.format(version)],
        stdout=PIPE)
    prs = []
    for message in git_list_result.stdout.split(b'\n'):
        match = re.match('.*Merge pull request #([0-9]+)', str(message))
        if match:
            prs.append(int(match.group(1)))
    return prs


def get_pr_info(auth_token, repo, id):
    pr_url = '{}/repos/{}/pulls/{}'.format(GITHUB_API_URL, repo, id)
    headers = {}
    if auth_token:
        headers['Authorization'] = 'token {}'.format(auth_token)
    res = requests.get(pr_url, headers=headers)
    if res.status_code != 200:
        raise Exception('GitHub request failed:', res.json()['message'])
    data = res.json()

    return PRInfo(id, title=data['title'].strip())


def format_list(items):
    def format_item(item, col_width):
        formatted = ''
        for line in iter(textwrap.wrap(item, col_width - 2)):
            if len(formatted) == 0:
                formatted = formatted + '- ' + line
            else:
                formatted = formatted + '\n  ' + line
        return formatted

    return '\n\n'.join([format_item(item, 80) for item in items])


def main():
    parser = argparse.ArgumentParser(description=
"""
Generates a list of changes since a given tag was created in the format used by
the CHANGES file.

Change descriptions are taken from pull request titles.

If no tag is specified, the most recently created tag is used.

This tool does not require authentication but the GitHub API has a relatively
low rate limit for unauthenticated requests, so you will probably want to use
an OAuth token. See
https://help.github.com/articles/creating-an-access-token-for-command-line-use/
"""
)
    parser.add_argument('--tag')
    parser.add_argument('--repo', default='hypothesis/h')
    parser.add_argument('--token')
    args = parser.parse_args()
    tag = args.tag or get_last_tag()

    closed_prs = get_prs_closed_since(tag)
    pr_details = [get_pr_info(args.token, args.repo, id) for id in closed_prs]

    def item_label(pr):
        return '{} (#{}).'.format(pr.title, pr.id)

    print('Changes since {} {}:\n'.format(args.repo, tag))
    print("""
****
Please edit the output below before including it in CHANGES.

Only include entries which have a reasonable chance of being interesting to a
downstream consumer of this package, and use language which does not assume
detailed knowledge of package internals where possible.
****
""")
    print(format_list([item_label(pr) for pr in pr_details]))


if __name__ == '__main__':
    main()
