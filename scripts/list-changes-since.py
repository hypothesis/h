#!/usr/bin/env python

from __future__ import unicode_literals
import argparse
import dateutil.parser
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


def get_tag_date(tag):
    tag_date_result = run(['git', 'tag', '--list', tag, '--format=%(taggerdate)'],
        stdout=PIPE)
    tag_date_str = tag_date_result.stdout.decode().strip()
    return dateutil.parser.parse(tag_date_str)


def github_request(auth_token, repo, path, **kwargs):
    """
    Make a GitHub API request and return an iterator over items in the response.

    `github_request` follows `next` links in paged responses automatically.
    """
    params = kwargs
    url = '{}/repos/{}/{}'.format(GITHUB_API_URL, repo, path)
    headers = {}
    if auth_token:
        headers['Authorization'] = 'token {}'.format(auth_token)

    while url:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            raise Exception('GitHub request failed:', res.text)

        page = res.json()
        if isinstance(page, list):
            for item in page:
                yield item
            try:
                url = res.links['next']['url']
            except KeyError:
                url = None
            params = None
        else:
            yield page
            break


def get_prs_merged_since(auth_token, repo, tag):
    """
    Return all pull requests merged since `tag` was created.

    Pull requests are sorted in ascending order of merge date.
    """
    tag_date = get_tag_date(tag)
    prs = []

    def merge_date(pr):
        if pr.get('merged_at'):
            return dateutil.parser.parse(pr['merged_at'])
        else:
            return None

    # The GitHub API does not provide a `since` parameter to retrieve PRs
    # closed since a given date, so instead we iterate over PRs in descending
    # order of last update and stop when we reach a PR that was last updated
    # before the given tag was created.
    for closed_pr in github_request(auth_token, repo, 'pulls', state='closed',
                                    sort='updated', direction='desc'):
        pr_date = dateutil.parser.parse(closed_pr['updated_at'])
        if pr_date < tag_date:
            break
        merged_at = merge_date(closed_pr)
        if merged_at and merged_at > tag_date:
            prs += [closed_pr]

    return sorted(prs, key=merge_date)


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

    pr_details = []
    for pr in get_prs_merged_since(args.token, args.repo, tag):
        pr_details += [PRInfo(pr['number'], title=pr['title'].strip())]

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
