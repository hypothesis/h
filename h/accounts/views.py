# -*- coding: utf-8 -*-

import datetime
import json

import colander
import deform
import jinja2
from pyramid import httpexceptions
from pyramid.exceptions import BadCSRFToken
from pyramid.view import view_config, view_defaults
from pyramid.security import forget, remember
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from h import i18n
from h import models
from h import session
from h import util
from h import accounts
from h.accounts import schemas
from h.accounts.models import User
from h.accounts.models import Activation
from h.accounts.events import ActivationEvent
from h.accounts.events import PasswordResetEvent
from h.accounts.events import LogoutEvent
from h.accounts.events import LoginEvent
from h.accounts.events import RegistrationEvent
from h.views import json_view

_ = i18n.TranslationString


# A little helper to ensure that session data is returned in every ajax
# response payload.
def ajax_payload(request, data):
    payload = {'flash': session.pop_flash(request),
               'model': session.model(request)}
    payload.update(data)
    return payload


@json_view(context=BadCSRFToken)
def bad_csrf_token(context, request):
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


@view_config(route_name='login', attr='login', request_method='POST',
             renderer='h:templates/accounts/login.html.jinja2')
@view_config(route_name='login', attr='login_form', request_method='GET',
             renderer='h:templates/accounts/login.html.jinja2')
@view_config(route_name='logout', attr='logout', request_method='GET')
class AuthController(object):
    def __init__(self, request):
        form_footer = ('<a href="{path}">'.format(
                           path=request.route_path('forgot_password')) +
                       _('Forgot your password?') +
                       '</a>')

        self.request = request
        self.schema = schemas.LoginSchema().bind(request=self.request)
        self.form = deform.Form(self.schema,
                                buttons=(_('Sign in'),),
                                footer=form_footer)

        self.login_redirect = self.request.params.get(
            'next',
            self.request.route_url('stream'))
        self.logout_redirect = self.request.route_url('index')

    def login(self):
        """
        Check the submitted credentials and log the user in if appropriate.
        """
        self._redirect_if_logged_in()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {'form': self.form.render()}

        user = appstruct['user']
        headers = self._login(user)
        return httpexceptions.HTTPFound(location=self.login_redirect,
                                        headers=headers)

    def login_form(self):
        """
        Render the empty login form.
        """
        self._redirect_if_logged_in()

        return {'form': self.form.render()}

    def logout(self):
        """
        Unconditionally log the user out.
        """
        headers = self._logout()
        return httpexceptions.HTTPFound(location=self.logout_redirect,
                                        headers=headers)

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(location=self.login_redirect)

    def _login(self, user):
        user.last_login_date = datetime.datetime.utcnow()
        self.request.registry.notify(LoginEvent(self.request, user))
        userid = util.userid_from_username(user.username, self.request)
        headers = remember(self.request, userid)
        return headers

    def _logout(self):
        if self.request.authenticated_userid is not None:
            self.request.registry.notify(LogoutEvent(self.request))
            self.request.session.invalidate()
        headers = forget(self.request)
        return headers


@view_defaults(route_name='session',
               accept='application/json',
               renderer='json')
@view_config(attr='login', request_param='__formid__=login')
@view_config(attr='logout', request_param='__formid__=logout')
class AjaxAuthController(AuthController):
    def login(self):
        try:
            json_body = self.request.json_body
        except ValueError as err:
            raise accounts.JSONError(
                _('Could not parse request body as JSON: {message}'.format(
                    message=err.message)))

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

    def logout(self):
        headers = self._logout()
        self.request.response.headers.extend(headers)
        return ajax_payload(self.request, {'status': 'okay'})


@view_defaults(route_name='forgot_password',
               renderer='h:templates/accounts/forgot_password.html.jinja2')
@view_config(attr='forgot_password_form', request_method='GET')
@view_config(attr='forgot_password', request_method='POST')
class ForgotPasswordController(object):

    """Controller for handling forgotten password forms."""

    def __init__(self, request):
        self.request = request
        self.schema = schemas.ForgotPasswordSchema().bind(request=self.request)
        self.form = deform.Form(self.schema, buttons=(_('Request reset'),))

    def forgot_password(self):
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
            self.request.route_path('reset_password'))

    def forgot_password_form(self):
        """Render the forgot password form."""
        self._redirect_if_logged_in()

        return {'form': self.form.render()}

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_path('index'))

    def _send_forgot_password_email(self, user):
        serializer = self.request.registry.password_reset_serializer
        code = serializer.dumps(user.username)

        link = reset_password_link(self.request, code)
        message = reset_password_email(user, code, link)
        mailer = get_mailer(self.request)
        mailer.send(message)


@view_defaults(route_name='reset_password',
               renderer='h:templates/accounts/reset_password.html.jinja2')
@view_config(attr='reset_password_form', request_method='GET')
@view_config(route_name='reset_password_with_code',
             attr='reset_password_with_code_form', request_method='GET')
@view_config(attr='reset_password', request_method='POST')
class ResetPasswordController(object):

    """Controller for handling password reset forms."""

    def __init__(self, request):
        self.request = request
        self.schema = schemas.ResetPasswordSchema().bind(request=self.request)
        self.form = deform.Form(
            schema=self.schema,
            action=self.request.route_path('reset_password'),
            buttons=(_('Save'),))

    def reset_password(self):
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

    def reset_password_form(self):
        """Render the reset password form."""
        return {'form': self.form.render(), 'has_code': False}

    def reset_password_with_code_form(self):
        """Render the reset password form with a prefilled code."""
        code = self.request.matchdict['code']

        # If valid, we inject the supplied it into the form as a hidden field.
        # Otherwise, we 404.
        try:
            user = schemas.ResetCode().deserialize(None, code)
        except colander.Invalid:
            raise httpexceptions.HTTPNotFound()
        else:
            # N.B. the form field for the reset code is called 'user'. See the
            # comment in `schemas.ResetPasswordSchema` for details.
            self.form.set_appstruct({'user': user})
            self.form.set_widgets({'user': deform.widget.HiddenWidget()})

        return {'form': self.form.render(), 'has_code': True}

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_path('index'))

    def _reset_password(self, user, password):
        user.password = password

        self.request.session.flash(jinja2.Markup(_(
            'Your password has been reset! '
            'You can now <a href="{url}">login</a> using the new password you '
            'provided.').format(url=self.request.route_url('login'))),
            'success')
        self.request.registry.notify(PasswordResetEvent(self.request, user))


@view_config(route_name='register', attr='register_form', request_method='GET',
             renderer='h:templates/accounts/register.html.jinja2')
@view_config(route_name='register', attr='register', request_method='POST',
             renderer='h:templates/accounts/register.html.jinja2')
@view_config(attr='activate', route_name='activate', request_method='GET')
class RegisterController(object):
    def __init__(self, request):
        tos_link = ('<a href="/terms-of-service">' +
                    _('Terms of Service') +
                    '</a>')
        cg_link = ('<a href="/community-guidelines">' +
                   _('Community Guidelines') +
                   '</a>')
        form_footer = _('You are agreeing to be bound by '
                        'our {tos_link} and {cg_link}.').format(tos_link=tos_link,
                                                                cg_link=cg_link)

        self.request = request
        self.schema = schemas.RegisterSchema().bind(request=self.request)
        self.form = deform.Form(self.schema,
                                buttons=(_('Sign up'),),
                                footer=form_footer)

    def register(self):
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

        self._register(username=appstruct['username'],
                       email=appstruct['email'],
                       password=appstruct['password'])

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))

    def register_form(self):
        """
        Render the empty registration form.
        """
        self._redirect_if_logged_in()

        return {'form': self.form.render()}

    def activate(self):
        """
        Handle a request for a user activation link.

        Checks if the activation code passed is valid, and (as a safety check)
        that it is an activation for the passed user id. If all is well,
        activate the user and redirect them to the stream.
        """
        code = self.request.matchdict.get('code')
        id_ = self.request.matchdict.get('id')

        if code is None or id_ is None:
            return httpexceptions.HTTPNotFound()

        try:
            id_ = int(id_)
        except ValueError:
            return httpexceptions.HTTPNotFound()

        activation = Activation.get_by_code(code)
        if activation is None:
            return httpexceptions.HTTPNotFound()

        user = User.get_by_activation(activation)
        if user is None or user.id != id_:
            return httpexceptions.HTTPNotFound()

        # Activate the user (by deleting the activation)
        self.request.db.delete(activation)

        self.request.session.flash(jinja2.Markup(_(
            'Your account has been activated! '
            'You can now <a href="{url}">login</a> using the password you '
            'provided.').format(url=self.request.route_url('login'))),
            'success')
        self.request.registry.notify(ActivationEvent(self.request, user))

        return httpexceptions.HTTPFound(
            location=self.request.route_url('index'))

    def _redirect_if_logged_in(self):
        if self.request.authenticated_userid is not None:
            raise httpexceptions.HTTPFound(self.request.route_url('stream'))

    def _register(self, username, email, password):
        user = User(username=username, email=email, password=password)
        self.request.db.add(user)

        # Create a new activation for the user
        activation = Activation()
        self.request.db.add(activation)
        user.activation = activation

        # Flush the session to ensure that the user can be created and the
        # activation is successfully wired up
        self.request.db.flush()

        # Send the activation email
        message = activation_email(self.request, user)
        mailer = get_mailer(self.request)
        mailer.send(message)

        self.request.session.flash(jinja2.Markup(_(
            'Thank you for creating an account! '
            "We've sent you an email with an activation link, "
            'before you can sign in <strong>please check your email and open '
            'the link to activate your account</strong>.')), 'success')
        self.request.registry.notify(RegistrationEvent(self.request, user))


@view_defaults(route_name='profile',
               renderer='h:templates/accounts/profile.html.jinja2')
@view_config(attr='profile_form', request_method='GET')
@view_config(attr='profile', request_method='POST')
class ProfileController(object):
    def __init__(self, request):
        self.request = request

        email_schema = schemas.EmailChangeSchema().bind(request=request)
        password_schema = schemas.PasswordChangeSchema().bind(request=request)

        self.forms = {
            'email': deform.Form(email_schema,
                                 buttons=(_('Change email address'),),
                                 formid='email'),
            'password': deform.Form(password_schema,
                                    buttons=(_('Change password'),),
                                    formid='password'),
        }

    def profile_form(self):
        """Show the user's profile."""
        if self.request.authenticated_user is None:
            raise httpexceptions.HTTPNotFound()

        return {'email': self.request.authenticated_user.email,
                'email_form': self.forms['email'].render(),
                'password_form': self.forms['password'].render()}

    def profile(self):
        """Handle POST payload from profile update form."""
        if self.request.authenticated_user is None:
            raise httpexceptions.HTTPNotFound()

        formid = self.request.POST.get('__formid__')
        if formid is None or formid not in self.forms:
            raise httpexceptions.HTTPBadRequest()

        try:
            if formid == 'email':
                self._handle_email_form()
            elif formid == 'password':
                self._handle_password_form()
        except deform.ValidationFailure:
            return {'email': self.request.authenticated_user.email,
                    'email_form': self.forms['email'].render(),
                    'password_form': self.forms['password'].render()}

        self.request.session.flash(_("Success. We've saved your changes."),
                                   'success')
        return httpexceptions.HTTPFound(
            location=self.request.route_url('profile'))

    def _handle_email_form(self):
        appstruct = self.forms['email'].validate(self.request.POST.items())
        self.request.authenticated_user.email = appstruct['email']

    def _handle_password_form(self):
        appstruct = self.forms['password'].validate(self.request.POST.items())
        self.request.authenticated_user.password = appstruct['new_password']


@view_defaults(route_name='profile_notifications',
               renderer='h:templates/accounts/notifications.html.jinja2')
@view_config(attr='notifications_form', request_method='GET')
@view_config(attr='notifications', request_method='POST')
class NotificationsController(object):
    def __init__(self, request):
        self.request = request
        self.schema = schemas.NotificationsSchema().bind(request=self.request)
        self.form = deform.Form(self.schema,
                                buttons=(_('Save changes'),))

    def notifications_form(self):
        """Render the notifications form."""
        if self.request.authenticated_userid is None:
            raise httpexceptions.HTTPNotFound()

        self.form.set_appstruct({
            'notifications': set(n.type
                                 for n in self._user_notifications()
                                 if n.active)
        })
        return {'form': self.form.render()}

    def notifications(self):
        """Process notifications POST data."""
        if self.request.authenticated_userid is None:
            raise httpexceptions.HTTPNotFound()

        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return {'form': self.form.render()}

        for n in self._user_notifications():
            n.active = n.type in appstruct['notifications']

        self.request.session.flash(_("Success. We've saved your changes."),
                                   'success')
        return httpexceptions.HTTPFound(
            location=self.request.route_url('profile_notifications'))

    def _user_notifications(self):
        """Fetch the notifications/subscriptions for the logged-in user."""
        return models.Subscriptions.get_subscriptions_for_uri(
            self.request.authenticated_userid)


def activation_email(request, user):
    """
    Generate an 'activate your account' email for the specified user.

    :rtype: pyramid_mailer.message.Message
    """
    link = request.route_url('activate', id=user.id, code=user.activation.code)

    emailtext = ("Please validate your email and activate your account by "
                 "visiting: {link}")
    body = emailtext.format(link=link)
    msg = Message(subject=_("Please activate your account"),
                  recipients=[user.email],
                  body=body)
    return msg


def reset_password_email(user, reset_code, reset_link):
    """
    Generate a 'reset your password' email for the specified user.

    :rtype: pyramid_mailer.message.Message
    """
    emailtext = ("Hello, {username}!\n\n"
                 "Someone requested resetting your password. If it was "
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
    msg = Message(subject=_("Reset your password"),
                  recipients=[user.email],
                  body=body)
    return msg


def reset_password_link(request, reset_code):
    """Transform an activation code into a password reset link."""
    return request.route_url('reset_password_with_code', code=reset_code)


def includeme(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')
    config.add_route('activate', '/activate/{id}/{code}')
    config.add_route('forgot_password', '/forgot_password')
    config.add_route('reset_password', '/reset_password')
    config.add_route('reset_password_with_code', '/reset_password/{code}')
    config.add_route('profile', '/profile')
    config.add_route('profile_notifications', '/profile/notifications')
    config.scan(__name__)
