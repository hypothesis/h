# -*- coding: utf-8 -*-
"""
A module that configures the application for debugging.

This module should *only* be included in the application in development
environments.
"""
from __future__ import print_function

import sys
import textwrap

from pyramid_mailer.interfaces import IMailer

CONSOLE_WIDTH = 70


class DebugMailer(object):
    """
    Debug mailer for use in development.
    """

    def _send(self, message, fail_silently=False):
        if not message.sender:
            message.sender = 'Default sender'

        mail_message = message.to_message()

        _print("=" * CONSOLE_WIDTH)
        _print("DEBUG: sending email...\n")

        for key, val in sorted(mail_message.items()):
            _print("    %s: %s" % (key, val))
        _print("")

        for part in mail_message.walk():
            if part.get_content_type() != 'text/plain':
                continue
            content = part.get_payload(decode=True)
            _print('\n'.join(textwrap.wrap(content,
                                           width=CONSOLE_WIDTH,
                                           initial_indent='    ',
                                           subsequent_indent='    ')))

        _print("=" * CONSOLE_WIDTH)

    send = _send
    send_immediately = _send
    send_to_queue = _send
    send_sendmail = _send
    send_immediately_sendmail = _send


def _print(text):
    print(text, file=sys.stderr)


def includeme(config):
    mailer = DebugMailer()
    config.registry.registerUtility(mailer, IMailer)
