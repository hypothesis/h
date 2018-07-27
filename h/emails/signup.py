# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.renderers import render

from h.i18n import TranslationString as _  # noqa: N813


def generate(request, id, email, activation_code):
    """
    Generate an email for a user signup.

    :param request: the current request
    :type request: pyramid.request.Request
    :param id: the new user's primary key ID
    :type id: int
    :param email: the new user's email address
    :type email: text
    :param activation_code: the activation code
    :type activation_code: text

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """
    context = {
        'activate_link': request.route_url('activate',
                                           id=id,
                                           code=activation_code),
    }

    subject = _('Please activate your account')

    text = render('h:templates/emails/signup.txt.jinja2',
                  context,
                  request=request)
    html = render('h:templates/emails/signup.html.jinja2',
                  context,
                  request=request)

    return [email], subject, text, html
