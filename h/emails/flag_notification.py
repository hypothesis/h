# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.renderers import render

from h.i18n import TranslationString as _  # noqa: N813


def generate(request, email, incontext_link):
    """
    Generate an email to notify the group admin when a group member flags an annotation.

    :param request: the current request
    :type request: pyramid.request.Request
    :param email: the group admin's email address
    :type email: text
    :param incontext_link: the direct link to the flagged annotation
    :type incontext_link: text

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """
    context = {
        'incontext_link': incontext_link,
    }

    subject = _('An annotation has been flagged')

    text = render('h:templates/emails/flag_notification.txt.jinja2',
                  context,
                  request=request)
    html = render('h:templates/emails/flag_notification.html.jinja2',
                  context,
                  request=request)

    return [email], subject, text, html
