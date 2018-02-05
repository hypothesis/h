# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.renderers import render

from h.i18n import TranslationString as _  # noqa: N813


def generate(request, user):
    """
    Generate an email for a user password reset request.

    :param request: the current request
    :type request: pyramid.request.Request
    :param user: the user to whom to send the reset code
    :type user: h.models.User

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """
    serializer = request.registry.password_reset_serializer
    code = serializer.dumps(user.username)
    context = {
        'username': user.username,
        'reset_code': code,
        'reset_link': request.route_url('account_reset_with_code', code=code)
    }

    subject = _('Reset your password')

    text = render('h:templates/emails/reset_password.txt.jinja2',
                  context,
                  request=request)
    html = render('h:templates/emails/reset_password.html.jinja2',
                  context,
                  request=request)

    return [user.email], subject, text, html
