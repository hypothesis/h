# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import deform
import jinja2
from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults

from h import i18n
from h.accounts import schemas

_ = i18n.TranslationString


def _login_redirect_url(request):
    return request.route_url('activity.user_search',
                             username=request.user.username)


@view_defaults(route_name='signup',
               renderer='h:templates/accounts/signup.html.jinja2')
class SignupController(object):

    def __init__(self, request):
        tos_link = ('<a class="link" href="/terms-of-service">' +
                    _('Terms of Service') +
                    '</a>')
        cg_link = ('<a class="link" href="/community-guidelines">' +
                   _('Community Guidelines') +
                   '</a>')
        form_footer = _(
            'You are agreeing to our {tos_link} and '
            '{cg_link}.').format(tos_link=tos_link, cg_link=cg_link)

        self.request = request
        self.schema = schemas.RegisterSchema().bind(request=self.request)
        self.form = request.create_form(self.schema,
                                        buttons=(deform.Button(title=_('Sign up'),
                                                               css_class='js-signup-btn'),),
                                        css_class='js-signup-form',
                                        footer=form_footer)

    @view_config(request_method='GET')
    def get(self):
        """Render the empty registration form."""
        self._redirect_if_logged_in()

        return {'form': self.form.render()}

    @view_config(request_method='POST')
    def post(self):
        """
        Handle submission of the new user registration form.

        Validates the form data, creates a new activation for the user, sends
        the activation mail, and then redirects the user to the index.
        """
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {'form': self.form.render()}

        signup_service = self.request.find_service(name='user_signup')
        signup_service.signup(username=appstruct['username'],
                              email=appstruct['email'],
                              password=appstruct['password'])

        self.request.session.flash(jinja2.Markup(_(
            "Please check your email and open the link to activate your "
            "account.")), 'success')

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(_login_redirect_url(self.request))
