# -*- coding: utf-8 -*-
"""
:mod:`h.claim.invite` is a utility to invite users to claim accounts
and is exposed as the command-line utility hypothesis-invite.
"""
import argparse
import logging
import os
import sys
import time

import mandrill
from pyramid import paster
from pyramid.request import Request
import transaction

from h.accounts import models
from h.claim.util import generate_claim_url

log = logging.getLogger('h.claim.invite')


def get_env(config_uri):
    """Return a preconfigured paste environment object."""
    env = paster.bootstrap(config_uri)
    return env

parser = argparse.ArgumentParser(
    'hypothesis-invite',
    description='Send invitation emails to users.'
)
parser.add_argument('config_uri', help='paster configuration URI')
parser.add_argument(
    '--base',
    help='base URL',
    default='http://localhost:5000',
    metavar='URL'
)
parser.add_argument(
    '-n',
    '--dry-run',
    help='dry run (log but do not send email)',
    action='store_true',
)
parser.add_argument(
    '-l',
    '--limit',
    type=int,
    metavar='N',
    help='maximum users to invite',
)
parser.add_argument(
    '-k',
    '--key',
    metavar='KEY',
    help='Mandrill API key (defaults to MANDRILL_APIKEY variable)',
    default=os.environ.get('MANDRILL_APIKEY'),
)


def get_users(session, limit=None):
    return (
        session
        .query(models.User)
        .filter(
            models.User.password == u'',
            models.User.status.op('&')(0b1000) == 0  # noqa
        )
        .limit(limit)
        .all()
    )


def get_merge_vars(request, users):
    for user in users:
        userid = 'acct:{}@{}'.format(user.username, request.domain)
        claim = generate_claim_url(request, userid)
        recipient = user.email
        merge_vars = [
            {
                'name': 'USERNAME',
                'content': user.username,
            },
            {
                'name': 'CLAIM_URL',
                'content': claim,
            },
        ]
        yield {
            'rcpt': recipient,
            'vars': merge_vars
        }


def get_recipients(users):
    for user in users:
        yield {
            'email': user.email,
            'name': user.username,
        }


def send_invitations(request, api_key, users):
    log.info('Collecting merge vars and recipients.')
    merge_vars = list(get_merge_vars(request, users))
    recipients = list(get_recipients(users))
    message = {
        'merge_vars': merge_vars,
        'to': recipients,
        'google_analytics_domains': [request.domain],
        'google_analytics_campaign': 'invite',
    }

    try:
        results = mandrill.Mandrill(api_key).messages.send_template(
            template_content=[],
            template_name='activation-email-to-reserved-usernames',
            message=message,
        )
    except mandrill.Error:
        log.exception('Error sending invitations.')
        sys.exit(1)

    return group_users_by_result(users, results)


def mark_invited(session, users):
    for user in users:
        user.invited = True
        session.add(user)
    transaction.commit()


def group_users_by_result(users, results):
    users_by_email = {user.email: user for user in users}

    success = []
    error = []
    for row in results:
        user = users_by_email[row['email']]
        if row['status'] in ['queued', 'sent']:
            success.append(user)
        else:
            error.append(user)

    return success, error


def main():
    args = parser.parse_args()

    request = Request.blank('', base_url=args.base)
    env = paster.bootstrap(args.config_uri, request=request)
    request.root = env['root']

    paster.setup_logging(args.config_uri)
    if not args.dry_run:
        if args.key is None:
            print 'No Mandrill API key specified.'
            parser.print_help()
            sys.exit(1)

        # Provide an opportunity to bail out.
        log.warning('Changes will be made and mail will be sent.')
        log.info('Waiting five seconds.')
        time.sleep(5)

    log.info('Collecting reserved users.')
    users = get_users(request.db, limit=args.limit)

    if args.dry_run:
        log.info('Skipping actions ignored by dry run.')
        success, error = users, []
    else:
        log.info('Sending invitations to %d users.', len(users))
        success, error = send_invitations(request, args.key, users)

        log.info('Marking users as invited.')
        mark_invited(request.db, success)

        log.info('%d succeeded / %d failed', len(success), len(error))

    sys.exit(0)


if __name__ == '__main__':
    main()
