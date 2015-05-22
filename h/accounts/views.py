# -*- coding: utf-8 -*-
import json

import colander
import deform
import horus.events
import horus.views
from horus.lib import FlashMessage
from horus.resources import UserFactory
from horus.interfaces import IForgotPasswordForm
from horus.interfaces import IForgotPasswordSchema
from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults
from pyramid.url import route_url
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from h import session
from h.models import _
from h.notification.models import Subscriptions
from h.resources import Application
import h.accounts.models

from . import schemas
from .events import LoginEvent, LogoutEvent


def ajax_form(request, result):
    flash = session.pop_flash(request)

    if isinstance(result, httpexceptions.HTTPRedirection):
        request.response.headers.extend(result.headers)
        result = {'status': 'okay'}
    elif isinstance(result, httpexceptions.HTTPError):
        request.response.status_code = result.code
        result = {'status': 'failure', 'reason': str(result)}
    else:
        errors = result.pop('errors', None)
        if errors is not None:
            status_code = result.pop('code', 400)
            request.response.status_code = status_code
            result['status'] = 'failure'

            result.setdefault('errors', {})
            for e in errors:
                if isinstance(e, colander.Invalid):
                    result['errors'].update(e.asdict())
                elif isinstance(e, dict):
                    result['errors'].update(e)

        reasons = flash.pop('error', [])
        if reasons:
            assert(len(reasons) == 1)
            request.response.status_code = 400
            result['status'] = 'failure'
            result['reason'] = reasons[0]

    result['flash'] = flash

    return result


def view_auth_defaults(fn, *args, **kwargs):
    kwargs.setdefault('accept', 'text/html')
    kwargs.setdefault('layout', 'auth')
    kwargs.setdefault('renderer', 'h:templates/auth.html')
    return view_defaults(*args, **kwargs)(fn)


@view_config(accept='application/json', renderer='json',
             context='pyramid.exceptions.BadCSRFToken')
def bad_csrf_token(context, request):
    request.response.status_code = 403
    reason = _('Session is invalid. Please try again.')
    return {
        'status': 'failure',
        'reason': reason,
        'model': session.model(request),
    }


class AsyncFormViewMapper(object):
    def __init__(self, **kw):
        self.attr = kw['attr']

    def __call__(self, view):
        def wrapper(context, request):
            if request.method == 'POST':
                data = request.json_body
                data.update(request.params)
                request.content_type = 'application/x-www-form-urlencoded'
                request.POST.clear()
                request.POST.update(data)
            inst = view(request)
            meth = getattr(inst, self.attr)
            result = meth()
            result = ajax_form(request, result)
            model = result.setdefault('model', {})
            model.update(session.model(request))

            # Add the user's email into the model. This is needed so that the
            # edit profile forms can show the value of the user's current
            # email.
            if 'email' not in model and request.authenticated_userid:
                model['email'] = h.accounts.models.User.get_by_id(
                    request, request.authenticated_userid).email

            result.pop('form', None)
            return result
        return wrapper


@view_auth_defaults
@view_config(attr='login', route_name='login')
@view_config(attr='logout', route_name='logout')
class AuthController(horus.views.AuthController):
    def login(self):
        if self.request.authenticated_userid is not None:
            return httpexceptions.HTTPFound(location=self.login_redirect_view)

        try:
            user = self.form.validate(self.request.POST.items())['user']
        except deform.ValidationFailure as e:
            return {
                'status': 'failure',
                'errors': e.error.children,
                'reason': e.error.msg,
            }

        self.request.registry.notify(LoginEvent(self.request, user))

        return {'status': 'okay'}

    def logout(self):
        self.request.registry.notify(LogoutEvent(self.request))
        return super(AuthController, self).logout()


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(attr='login', request_param='__formid__=login')
@view_config(attr='logout', request_param='__formid__=logout')
class AsyncAuthController(AuthController):
    __view_mapper__ = AsyncFormViewMapper


@view_auth_defaults
@view_config(attr='forgot_password', route_name='forgot_password')
@view_config(attr='reset_password', route_name='reset_password')
class ForgotPasswordController(horus.views.ForgotPasswordController):
    def forgot_password(self):
        req = self.request
        schema = req.registry.getUtility(IForgotPasswordSchema)
        schema = schema().bind(request=req)

        form = req.registry.getUtility(IForgotPasswordForm)
        form = form(schema)

        if req.method == 'GET':
            if req.user:
                return httpexceptions.HTTPFound(
                    location=self.forgot_password_redirect_view)
            else:
                return {'form': form.render()}

        controls = req.POST.items()
        try:
            captured = form.validate(controls)
        except deform.ValidationFailure as e:
            return {'form': e.render(), 'errors': e.error.children}

        user = self.User.get_by_email(req, captured['email'])
        activation = self.Activation()
        self.db.add(activation)
        user.activation = activation

        mailer = get_mailer(req)
        username = getattr(user, 'short_name', '') or \
            getattr(user, 'full_name', '') or \
            getattr(user, 'username', '') or user.email
        emailtext = ("Hello, {username}!\n\n"
                     "Someone requested resetting your password. If it was "
                     "you, reset your password by using this reset code:\n\n"
                     "{code}\n\n"
                     "Alternatively, you can reset your password by "
                     "clicking on this link:\n\n"
                     "{link}\n\n"
                     "If you don't want to change your password, please "
                     "ignore this email message.\n\n"
                     "Regards,\n"
                     "The Hypothesis Team\n")
        body = emailtext.format(
            code=user.activation.code,
            link=route_url('reset_password', req, code=user.activation.code),
            username=username)
        subject = self.Str.reset_password_email_subject
        message = Message(
            subject=subject,
            recipients=[user.email],
            body=body)
        mailer.send(message)
        FlashMessage(
            self.request,
            self.Str.reset_password_email_sent,
            kind='success')
        return httpexceptions.HTTPFound(
            location=self.reset_password_redirect_view)


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(
    attr='forgot_password',
    request_param='__formid__=forgot_password'
)
@view_config(
    attr='reset_password',
    request_param='__formid__=reset_password'
)
class AsyncForgotPasswordController(ForgotPasswordController):
    __view_mapper__ = AsyncFormViewMapper

    def reset_password(self):
        request = self.request
        request.matchdict = request.POST
        return super(AsyncForgotPasswordController, self).reset_password()


@view_auth_defaults
@view_config(attr='register', route_name='register')
@view_config(attr='activate', route_name='activate')
class RegisterController(horus.views.RegisterController):
    pass


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(attr='register', request_param='__formid__=register')
@view_config(attr='activate', request_param='__formid__=activate')
class AsyncRegisterController(RegisterController):
    __view_mapper__ = AsyncFormViewMapper


def _emails_must_match_validator(form, value):
    """Raise colander.Invalid if "email" and "emailAgain" don't match."""
    if value.get("email") != value.get("emailAgain"):
        exc = colander.Invalid(form, "The emails must match")
        exc["emailAgain"] = "The emails must match."
        raise exc


class _InvalidEditProfileRequestError(Exception):

    """Raised if validating an edit user profile request fails."""

    def __init__(self, errors):
        super(_InvalidEditProfileRequestError, self).__init__()
        self.errors = errors


def _validate_edit_profile_request(request):
    """Validate the given request using the EditProfileSchema.

    :returns: if the request is valid returns a Deform "appstruct" with keys
        ``"username"``, ``"pwd"`` and ``"email"``
    :rtype: dict

    :raises _InvalidEditProfileRequestError: if the request is invalid

    """
    schema = schemas.EditProfileSchema(
        validator=_emails_must_match_validator).bind(request=request)
    form = deform.Form(schema)
    try:
        return form.validate(request.POST.items())
    except deform.ValidationFailure as err:
        raise _InvalidEditProfileRequestError(errors=err.error.children)


@view_auth_defaults
@view_config(attr='edit_profile', route_name='edit_profile')
@view_config(attr='disable_user', route_name='disable_user')
@view_config(attr='profile', route_name='profile')
class ProfileController(horus.views.ProfileController):
    def edit_profile(self):
        try:
            appstruct = _validate_edit_profile_request(self.request)
        except _InvalidEditProfileRequestError as err:
            return dict(errors=err.errors)

        username = appstruct['username']
        pwd = appstruct['pwd']
        subscriptions = appstruct['subscriptions']

        if subscriptions:
            # Update the subscriptions table
            subs = json.loads(subscriptions)
            if username == subs['uri']:
                s = Subscriptions.get_by_id(self.request, subs['id'])
                if s:
                    s.active = subs['active']
                    self.db.add(s)
                    return {}
                else:
                    return dict(
                        errors=[
                            {'subscriptions': _('Non existing subscription')}
                        ],
                        code=404
                    )
            else:
                return dict(
                    errors=[{'username': _('Invalid username')}], code=400
                )

        # Password check
        user = self.User.get_user(self.request, username, pwd)
        if user:
            self.request.context = user
            return super(ProfileController, self).edit_profile()
        else:
            return dict(errors=[{'pwd': _('Invalid password')}], code=401)

    def disable_user(self):
        request = self.request
        schema = schemas.EditProfileSchema().bind(request=request)
        form = deform.Form(schema)

        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return dict(errors=e.error.children)

        username = appstruct['username']
        pwd = appstruct['pwd']

        # Password check
        user = self.User.get_user(request, username, pwd)
        if user:
            # TODO: maybe have an explicit disabled flag in the status
            user.password = self.User.generate_random_password()
            self.db.add(user)
            FlashMessage(self.request, _('Account disabled.'), kind='success')
            return {}
        else:
            return dict(errors=[{'pwd': _('Invalid password')}], code=401)

    def profile(self):
        request = self.request
        userid = request.authenticated_userid
        model = {}
        if userid:
            model["email"] = self.User.get_by_id(request, userid).email
        if request.registry.feature('notification'):
            model['subscriptions'] = Subscriptions.get_subscriptions_for_uri(
                request,
                userid
            )
        return {'model': model}

    def unsubscribe(self):
        request = self.request
        subscription_id = request.GET['subscription_id']
        subscription = Subscriptions.get_by_id(request, subscription_id)
        if subscription:
            subscription.active = False
            self.db.add(subscription)
            return {}
        return {}


@view_defaults(accept='application/json', context=Application, renderer='json')
@view_config(attr='edit_profile', request_param='__formid__=edit_profile')
@view_config(attr='disable_user', request_param='__formid__=disable_user')
@view_config(attr='profile', request_param='__formid__=profile')
@view_config(attr='unsubscribe', request_param='__formid__=unsubscribe')
class AsyncProfileController(ProfileController):
    __view_mapper__ = AsyncFormViewMapper


def includeme(config):
    config.add_route('disable_user', '/disable/{userid}',
                     factory=UserFactory,
                     traverse="/{userid}")

    config.include('horus')
    config.scan(__name__)
