#!/usr/bin/env python

from argparse import ArgumentParser

import requests


def main():
    parser = ArgumentParser(description=
        """Delete a release and associated files from Sentry""")
    parser.add_argument('--key', required=True)
    parser.add_argument('--org', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--release', required=True)
    args = parser.parse_args()

    sentry_release_url = '{}/api/0/projects/{}/{}/releases/{}/'.format(
        'https://app.getsentry.com',
        args.org,
        args.project,
        args.release
    )
    res = requests.delete(sentry_release_url, auth=(args.key,''))
    if res.status_code != 204:
        print('Deleting release failed: {}: {}'.format(res.status_code,
          res.text))


if __name__ == '__main__':
    main()
