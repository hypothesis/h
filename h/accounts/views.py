# -*- coding: utf-8 -*-

import datetime

import colander
import deform
import jinja2
from pyramid import httpexceptions
from pyramid import security
from pyramid.exceptions import BadCSRFToken
from pyramid.view import view_config, view_defaults

from h import accounts
from h import form
from h import i18n
from h import mailer
from h import models
from h import session
from h.accounts import schemas
from h.accounts.events import ActivationEvent
from h.accounts.events import PasswordResetEvent
from h.accounts.events import LogoutEvent
from h.accounts.events import LoginEvent
from h.util.view import json_view
from h._compat import urlparse

_ = i18n.TranslationString


# A little helper to ensure that session data is returned in every ajax
# response payload.
def ajax_payload(request, data):
    payload = {'flash': session.pop_flash(request),
               'model': session.model(request)}
    payload.update(data)
    return payload


@view_config(context=BadCSRFToken,
             accept='text/html',
             renderer='h:templates/accounts/session_invalid.html.jinja2')
def bad_csrf_token_html(context, request):
    request.response.status_code = 403

    next_path = '/'
    referer = urlparse.urlparse(request.referer or '')
    if referer.hostname == request.domain:
        next_path = referer.path

    login_path = request.route_path('login', _query={'next': next_path})
    return {'login_path': login_path}


@json_view(context=BadCSRFToken)
def bad_csrf_token_json(context, request):
    request.response.status_code = 403
    reason = _('Session is invalid. Please try again.')
    return {
        'status': 'failure',
        'reason': reason,
        'model': session.model(request),
    }


@json_view(context=accounts.JSONError)
def error_json(error, request):
    request.response.status_code = 400
    return {
        'status': 'failure',
        'reason': error.message
    }


@json_view(context=deform.ValidationFailure)
def error_validation(error, request):
    request.response.status_code = 400
    return ajax_payload(
        request,
        {'status': 'failure', 'errors': error.error.asdict()})


@view_defaults(route_name='login',
               renderer='h:templates/accounts/login.html.jinja2')
class AuthController(object):

    def __init__(self, request):
        form_footer = '<a class="link" href="{href}">{text}</a>'.format(
            href=request.route_path('forgot_password'),
            text=_('Forgot your password?'))

        self.request = request
        self.schema = schemas.LoginSchema().bind(request=self.request)
        self.form = request.create_form(self.schema,
                                        buttons=(_('Log in'),),
                                        footer=form_footer)

        self.login_redirect = self.request.params.get(
            'next',
            self.request.route_url('stream'))
        self.logout_redirect = self.request.route_url('index')

    @view_config(request_method='GET')
    def get(self):
        """Render the login page, including the login form."""
        self._redirect_if_logged_in()

        return {'form': self.form.render()}

    @view_config(request_method='POST')
    def post(self):
        """Log the user in and redirect them."""
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {'form': self.form.render()}

        user = appstruct['user']
        headers = self._login(user)
        return httpexceptions.HTTPFound(location=self.login_redirect,
                                        headers=headers)

    @view_config(route_name='logout',
                 renderer=None,
                 request_method='GET')
    def logout(self):
        """Log the user out."""
        headers = self._logout()
        return httpexceptions.HTTPFound(location=self.logout_redirect,
                                        headers=headers)

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(location=self.login_redirect)

    def _login(self, user):
        user.last_login_date = datetime.datetime.utcnow()
        self.request.registry.notify(LoginEvent(self.request, user))
        headers = security.remember(self.request, user.userid)
        return headers

    def _logout(self):
        if self.request.authenticated_userid is not None:
            self.request.registry.notify(LogoutEvent(self.request))
            self.request.session.invalidate()
        headers = security.forget(self.request)
        return headers


@view_defaults(route_name='session',
               accept='application/json',
               renderer='json')
class AjaxAuthController(AuthController):

    def __init__(self, request):
        self.request = request
        self.schema = schemas.LoginSchema().bind(request=self.request)
        self.form = request.create_form(self.schema)

    @view_config(request_param='__formid__=login')
    def login(self):
        try:
            json_body = self.request.json_body
        except ValueError as exc:
            raise accounts.JSONError(
                _('Could not parse request body as JSON: {message}'.format(
                    message=exc.message)))

        if not isinstance(json_body, dict):
            raise accounts.JSONError(
                _('Request JSON body must have a top-level object'))

        # Transform non-string usernames and password into strings.
        # Deform crashes otherwise.
        json_body['username'] = unicode(json_body.get('username') or '')
        json_body['password'] = unicode(json_body.get('password') or '')

        appstruct = self.form.validate(json_body.items())

        user = appstruct['user']
        headers = self._login(user)
        self.request.response.headers.extend(headers)

        return ajax_payload(self.request, {'status': 'okay'})

    @view_config(request_param='__formid__=logout')
    def logout(self):
        headers = self._logout()
        self.request.response.headers.extend(headers)
        return ajax_payload(self.request, {'status': 'okay'})


@view_defaults(route_name='forgot_password',
               renderer='h:templates/accounts/forgot_password.html.jinja2')
class ForgotPasswordController(object):

    """Controller for handling forgotten password forms."""

    def __init__(self, request):
        self.request = request
        self.schema = schemas.ForgotPasswordSchema().bind(request=self.request)
        self.form = request.create_form(self.schema, buttons=(_('Reset'),))

    @view_config(request_method='GET')
    def get(self):
        """Render the forgot password page, including the form."""
        self._redirect_if_logged_in()

        return {'form': self.form.render()}

    @view_config(request_method='POST')
    def post(self):
        """
        Handle submission of the forgot password form.

        Validates that the email is one we know about, and then generates a new
        activation for the associated user, and dispatches a "reset your
        password" email which contains a token and/or link to the reset
        password form.
        """
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {'form': self.form.render()}

        user = appstruct['user']
        self._send_forgot_password_email(user)

        return httpexceptions.HTTPFound(
            self.request.route_path('account_reset'))

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_path('index'))

    def _send_forgot_password_email(self, user):
        serializer = self.request.registry.password_reset_serializer
        code = serializer.dumps(user.username)

        link = account_reset_link(self.request, code)
        message = account_reset_email(user, code, link)
        mailer.send.delay(**message)


@view_defaults(route_name='account_reset',
               renderer='h:templates/accounts/reset.html.jinja2')
class ResetController(object):

    """Controller for handling password reset forms."""

    def __init__(self, request):
        self.request = request
        self.schema = schemas.ResetPasswordSchema().bind(request=self.request)
        self.form = request.create_form(
            schema=self.schema,
            action=self.request.route_path('account_reset'),
            buttons=(_('Save'),))

    @view_config(request_method='GET')
    def get(self):
        """Render the reset password form."""
        return {'form': self.form.render(), 'has_code': False}

    @view_config(route_name='account_reset_with_code',
                 request_method='GET')
    def get_with_prefilled_code(self):
        """Render the reset password form with a prefilled code."""
        code = self.request.matchdict['code']

        # If valid, we inject the supplied it into the form as a hidden field.
        # Otherwise, we 404.
        try:
            user = schemas.ResetCode().deserialize(self.schema, code)
        except colander.Invalid:
            raise httpexceptions.HTTPNotFound()
        else:
            # N.B. the form field for the reset code is called 'user'. See the
            # comment in `schemas.ResetPasswordSchema` for details.
            self.form.set_appstruct({'user': user})
            self.form.set_widgets({'user': deform.widget.HiddenWidget()})

        return {'form': self.form.render(), 'has_code': True}

    @view_config(request_method='POST')
    def post(self):
        """
        Handle submission of the reset password form.

        This function checks that the activation code (i.e. reset token)
        provided by the form is valid, retrieves the user associated with the
        activation code, and resets their password.
        """
        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            # If the code is valid, hide the field.
            if not self.form['user'].error:
                self.form.set_widgets({'user': deform.widget.HiddenWidget()})
            return {'form': self.form.render()}

        self._reset_password(appstruct['user'], appstruct['password'])

        return httpexceptions.HTTPFound(
            location=self.request.route_path('index'))

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_path('index'))

    def _reset_password(self, user, password):
        user.password = password

        self.request.session.flash(jinja2.Markup(_(
            'Your password has been reset. '
            'You can now <a href="{url}">login</a> with your new '
            'password.').format(url=self.request.route_url('login'))),
            'success')
        self.request.registry.notify(PasswordResetEvent(self.request, user))


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
            raise httpexceptions.HTTPFound(self.request.route_url('stream'))


@view_defaults(route_name='activate')
class ActivateController(object):

    def __init__(self, request):
        self.request = request

    @view_config(request_method='GET')
    def get_when_not_logged_in(self):
        """
        Handle a request for a user activation link.

        Checks if the activation code passed is valid, and (as a safety check)
        that it is an activation for the passed user id. If all is well,
        activate the user and redirect them to the stream.
        """
        code = self.request.matchdict.get('code')
        id_ = self.request.matchdict.get('id')

        try:
            id_ = int(id_)
        except ValueError:
            raise httpexceptions.HTTPNotFound()

        activation = models.Activation.get_by_code(self.request.db, code)
        if activation is None:
            self.request.session.flash(jinja2.Markup(_(
                "We didn't recognize that activation link. "
                "Have you already activated your account? "
                'If so, try <a href="{url}">logging in</a> using the username '
                'and password that you provided.').format(
                    url=self.request.route_url('login'))),
                'error')
            return httpexceptions.HTTPFound(
                location=self.request.route_url('index'))

        user = models.User.get_by_activation(self.request.db, activation)
        if user is None or user.id != id_:
            raise httpexceptions.HTTPNotFound()

        user.activate()

        self.request.session.flash(jinja2.Markup(_(
            'Your account has been activated! '
            'You can now <a href="{url}">log in</a> using the password you '
            'provided.').format(url=self.request.route_url('login'))),
            'success')

        self.request.registry.notify(ActivationEvent(self.request, user))

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))

    @view_config(request_method='GET',
                 effective_principals=security.Authenticated)
    def get_when_logged_in(self):
        """Handle an activation link request while already logged in."""
        id_ = self.request.matchdict.get('id')

        try:
            id_ = int(id_)
        except ValueError:
            raise httpexceptions.HTTPNotFound()

        if id_ == self.request.authenticated_user.id:
            # The user is already logged in to the account (so the account
            # must already be activated).
            self.request.session.flash(jinja2.Markup(_(
                "Your account has been activated and you're logged in.")),
                'success')
        else:
            self.request.session.flash(jinja2.Markup(_(
                "You're already logged in to a different account. "
                '<a href="{url}">Log out</a> and open the activation link '
                'again.').format(
                    url=self.request.route_url('logout'))),
                'error')

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))


@view_defaults(route_name='account',
               renderer='h:templates/accounts/account.html.jinja2',
               effective_principals=security.Authenticated)
class AccountController(object):

    def __init__(self, request):
        self.request = request

        if request.feature('activity_pages'):
            email_schema = schemas.EmailChangeSchema().bind(request=request)
        else:
            email_schema = schemas.LegacyEmailChangeSchema().bind(request=request)

        password_schema = schemas.PasswordChangeSchema().bind(request=request)

        self.forms = {
            'email': request.create_form(email_schema,
                                         buttons=(_('Change email address'),),
                                         formid='email'),
            'password': request.create_form(password_schema,
                                            buttons=(_('Change password'),),
                                            formid='password'),
        }

    @view_config(request_method='GET')
    def get(self):
        """Show the user's account."""
        return self._template_data()

    @view_config(request_method='POST',
                 request_param='__formid__=email')
    def post_email_form(self):
        """Called by Pyramid when the change email form is submitted."""
        return form.handle_form_submission(
            self.request,
            self.forms['email'],
            on_success=self.update_email_address,
            on_failure=self._template_data)

    @view_config(request_method='POST',
                 request_param='__formid__=password')
    def post_password_form(self):
        """Called by Pyramid when the change password form is submitted."""
        return form.handle_form_submission(
            self.request,
            self.forms['password'],
            on_success=self.update_password,
            on_failure=self._template_data)

    def update_email_address(self, appstruct):
        self.request.authenticated_user.email = appstruct['email']

    def update_password(self, appstruct):
        self.request.authenticated_user.password = appstruct['new_password']

    def _template_data(self):
        """Return the data needed to render accounts.html.jinja2."""
        email = self.request.authenticated_user.email
        password_form = self.forms['password'].render()

        if self.request.feature('activity_pages'):
            email_form = self.forms['email'].render({'email': email})
        else:
            email_form = self.forms['email'].render()

        return {'email': email,
                'email_form': email_form,
                'password_form': password_form}


@view_defaults(route_name='account_profile',
               renderer='h:templates/accounts/profile.html.jinja2',
               effective_principals=security.Authenticated)
class EditProfileController(object):

    def __init__(self, request):
        self.request = request
        self.schema = schemas.EditProfileSchema().bind(request=self.request)
        self.form = request.create_form(self.schema,
                                        buttons=(_('Save'),),
                                        use_inline_editing=True)

    @view_config(request_method='GET')
    def get(self):
        """Render the 'Edit Profile' form"""
        user = self.request.authenticated_user
        self.form.set_appstruct({
            'display_name': user.display_name or '',
            'description': user.description or '',
            'location': user.location or '',
            'link': user.uri or '',
            'orcid': user.orcid or '',
        })
        return self._template_data()

    @view_config(request_method='POST')
    def post(self):
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self._update_user,
            on_failure=self._template_data)

    def _template_data(self):
        return {'form': self.form.render()}

    def _update_user(self, appstruct):
        user = self.request.authenticated_user
        user.display_name = appstruct['display_name']
        user.description = appstruct['description']
        user.location = appstruct['location']
        user.uri = appstruct['link']
        user.orcid = appstruct['orcid']


@view_defaults(route_name='account_notifications',
               renderer='h:templates/accounts/notifications.html.jinja2',
               effective_principals=security.Authenticated)
class NotificationsController(object):

    def __init__(self, request):
        self.request = request
        self.schema = schemas.NotificationsSchema().bind(request=self.request)
        self.form = request.create_form(self.schema,
                                        buttons=(_('Save'),),
                                        use_inline_editing=True)

    @view_config(request_method='GET')
    def get(self):
        """Render the notifications form."""
        self.form.set_appstruct({
            'notifications': set(n.type
                                 for n in self._user_notifications()
                                 if n.active)
        })
        return self._template_data()

    @view_config(request_method='POST')
    def post(self):
        """Process notifications POST data."""
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self._update_notifications,
            on_failure=self._template_data)

    def _update_notifications(self, appstruct):
        for n in self._user_notifications():
            n.active = n.type in appstruct['notifications']

    def _template_data(self):
        return {'form': self.form.render()}

    def _user_notifications(self):
        """Fetch the notifications/subscriptions for the logged-in user."""
        return models.Subscriptions.get_subscriptions_for_uri(
            self.request.db,
            self.request.authenticated_userid)


@view_defaults(route_name='account_developer',
               renderer='h:templates/accounts/developer.html.jinja2',
               effective_principals=security.Authenticated)
class DeveloperController(object):

    def __init__(self, request):
        self.request = request

    @view_config(request_method='GET')
    def get(self):
        """Render the developer page, including the form."""
        token = models.Token.get_by_userid(self.request.db,
                                           self.request.authenticated_userid)
        if token:
            return {'token': token.value}
        else:
            return {}

    @view_config(request_method='POST')
    def post(self):
        """(Re-)generate the user's API token."""
        token = models.Token.get_by_userid(self.request.db,
                                           self.request.authenticated_userid)

        if token:
            # The user already has an API token, regenerate it.
            token.regenerate()
        else:
            # The user doesn't have an API token yet, generate one for them.
            token = models.Token(self.request.authenticated_userid)
            self.request.db.add(token)

        return {'token': token.value}


def account_reset_email(user, reset_code, reset_link):
    """Return the data for a 'reset your password' email for the given user.

    :rtype: dict

    """
    emailtext = ("Hello, {username}!\n\n"
                 "Someone has requested to reset your password. If it was "
                 "you, reset your password by using this reset code:\n\n"
                 "{code}\n\n"
                 "Alternatively, you can reset your password by "
                 "clicking on this link:\n\n"
                 "{link}\n\n"
                 "Regards,\n"
                 "The Hypothesis Team\n")
    body = emailtext.format(code=reset_code,
                            link=reset_link,
                            username=user.username)
    return {
        "recipients": [user.email],
        "subject": _("Reset your password"),
        "body": body
    }


def account_reset_link(request, reset_code):
    """Transform an activation code into an account reset link."""
    return request.route_url('account_reset_with_code', code=reset_code)


# TODO: This can be removed after October 2016, which will be >1 year from the
#       date that the last account claim emails were sent out. At this point,
#       if we have not done so already, we should remove all unclaimed
#       usernames from the accounts tables.
@view_config(route_name='claim_account_legacy',
             request_method='GET',
             renderer='h:templates/accounts/claim_account_legacy.html.jinja2')
def claim_account_legacy(request):
    """Render a page explaining that claim links are no longer valid."""
    return {}


@view_config(route_name='dismiss_sidebar_tutorial',
             request_method='POST',
             renderer='json')
def dismiss_sidebar_tutorial(request):
    if request.authenticated_userid is None:
        raise accounts.JSONError()
    else:
        request.authenticated_user.sidebar_tutorial_dismissed = True
        return ajax_payload(request, {'status': 'okay'})


def includeme(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('signup', '/signup')
    config.add_route('activate', '/activate/{id}/{code}')
    config.add_route('forgot_password', '/forgot-password')
    config.add_route('account_reset', '/account/reset')
    config.add_route('account_reset_with_code', '/account/reset/{code}')
    config.add_route('account', '/account/settings')
    config.add_route('account_profile', '/account/profile')
    config.add_route(
        'account_notifications', '/account/settings/notifications')
    config.add_route('account_developer', '/account/developer')
    config.add_route('claim_account_legacy', '/claim_account/{token}')
    config.add_route('dismiss_sidebar_tutorial',
                     '/app/dismiss_sidebar_tutorial')
    config.scan(__name__)
