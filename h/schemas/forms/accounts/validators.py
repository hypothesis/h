# -*- coding: utf-8 -*-
"""Custom Colander validators for user-facing accounts forms."""

from __future__ import unicode_literals

import colander

from h import i18n
from h import models

_ = i18n.TranslationString


def unique_email(node, value):
    '''Colander validator that ensures no user with this email exists.'''
    request = node.bindings['request']
    user = models.User.get_by_email(request.db, value, request.default_authority)
    if user and user.userid != request.authenticated_userid:
        msg = _("Sorry, an account with this email address already exists.")
        raise colander.Invalid(node, msg)
