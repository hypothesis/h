# -*- coding: utf-8 -*-
import datetime

import colander
import deform
import horus.views
from horus.lib import FlashMessage
from horus.resources import UserFactory
from pyramid import httpexceptions, security
from pyramid.view import view_config, view_defaults

from h.auth.local import schemas
from h.models import _
from h.stats import get_client as stats


def ajax_form(request, result):
    flash = pop_flash(request)

    if isinstance(result, httpexceptions.HTTPRedirection):
        request.response.headers.extend(result.headers)
        result = {'status': 'okay'}
    elif isinstance(result, httpexceptions.HTTPError):
        request.response.status_code = result.code
        result = {'status': 'failure', 'reason': str(result)}
    else:
        errors = result.pop('errors', [])
        if errors:
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


def pop_flash(request):
    session = request.session

    queues = {
        name[3:]: [msg for msg in session.pop_flash(name[3:])]
        for name in session.keys()
        if name.startswith('_f_')
    }

    # Deal with bag.web.pyramid.flash_msg style mesages
    for msg in queues.pop('', []):
        q = getattr(msg, 'kind', '')
        msg = getattr(msg, 'plain', msg)
        queues.setdefault(q, []).append(msg)

    return queues


def model(request):
    session = {k: v for k, v in request.session.items() if k[0] != '_'}
    session['csrf'] = request.session.get_csrf_token()
    return session


def remember(request, user):
    if user is not None:
        userid = 'acct:{}@{}'.format(user.username, request.domain)
        headers = security.remember(request, userid)
        request.response.headerlist.extend(headers)


def set_csrf_token(request, response):
    csrft = request.session.get_csrf_token()
    if request.cookies.get('XSRF-TOKEN') != csrft:
        response.set_cookie('XSRF-TOKEN', csrft)


def ensure_csrf_token(view_fn):
    def wrapper(context, request):
        request.add_response_callback(set_csrf_token)
        return view_fn(context, request)

    return wrapper


def view_auth_defaults(fn, *args, **kwargs):
    kwargs.setdefault('accept', 'text/html')
    kwargs.setdefault('decorator', ensure_csrf_token)
    kwargs.setdefault('layout', 'auth')
    kwargs.setdefault('renderer', 'h:templates/auth.pt')
    return view_defaults(*args, **kwargs)(fn)


# TODO: change to something other than /app
@view_config(accept='application/json',  name='app', renderer='json')
def session(request):
    request.add_response_callback(set_csrf_token)
    return dict(status='okay', flash=pop_flash(request), model=model(request))


@view_config(accept='application/json', renderer='json',
             context='pyramid.exceptions.BadCSRFToken')
def bad_csrf_token(context, request):
    request.response.status_code = 403
    reason = _('Session is invalid. Please try again.')
    return {
        'status': 'failure',
        'reason': reason,
        'model': model(request),
    }


class AsyncFormViewMapper(object):
    def __init__(self, **kw):
        self.attr = kw['attr']

    def __call__(self, view):
        def wrapper(context, request):
            request.add_response_callback(set_csrf_token)
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
            result['model'] = model(request)
            result.pop('form', None)
            return result
        return wrapper


@view_auth_defaults
@view_config(attr='login', route_name='login')
@view_config(attr='logout', route_name='logout')
class AuthController(horus.views.AuthController):
    def check_credentials(self, username, password):
        allow_email_auth = self.settings.get('horus.allow_email_auth', False)

        user = self.User.get_by_username(self.request, username)

        if allow_email_auth and not user:
            user = self.User.get_by_email(self.request, username)

        if not user:
            raise httpexceptions.HTTPBadRequest({
                'errors': [{
                    'username': _('User does not exist.'),
                }],
            })

        if not self.User.validate_user(user, password):
            raise httpexceptions.HTTPBadRequest({
                'errors': [{
                    'password': _('Incorrect password. Please try again.'),
                }],
            })

        if not self.allow_inactive_login and self.require_activation \
                and not user.is_activated:
            reason = _('Your account is not active, please check your e-mail.')
            raise httpexceptions.HTTPBadRequest({'reason': reason})

        return user

    def login(self):
        request = self.request
        try:
            result = super(AuthController, self).login()
        except httpexceptions.HTTPBadRequest as e:
            return e.detail
        else:
            if request.user is not None:
                stats(request).get_counter('auth.local.login').increment()
                request.user.last_login_date = datetime.datetime.utcnow()
                self.db.add(request.user)
            remember(request, request.user)
            return result

    def logout(self):
        stats(self.request).get_counter('auth.local.logout').increment()
        return super(AuthController, self).logout()


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='login', request_param='__formid__=login')
@view_config(attr='logout', request_param='__formid__=logout')
class AsyncAuthController(AuthController):
    __view_mapper__ = AsyncFormViewMapper


@view_auth_defaults
@view_config(attr='forgot_password', route_name='forgot_password')
@view_config(attr='reset_password', route_name='reset_password')
class ForgotPasswordController(horus.views.ForgotPasswordController):
    def reset_password(self):
        request = self.request
        result = super(ForgotPasswordController, self).reset_password()
        stats(request).get_counter('auth.local.reset_password').increment()
        remember(request, request.user)
        return result


@view_defaults(accept='application/json', name='app', renderer='json')
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
    def register(self):
        request = self.request
        result = super(RegisterController, self).register()
        stats(request).get_counter('auth.local.register').increment()
        remember(request, request.user)
        return result


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='register', request_param='__formid__=register')
@view_config(attr='activate', request_param='__formid__=activate')
class AsyncRegisterController(RegisterController):
    __view_mapper__ = AsyncFormViewMapper


@view_auth_defaults
@view_config(attr='edit_profile', route_name='edit_profile')
@view_config(attr='disable_user', route_name='disable_user')
class ProfileController(horus.views.ProfileController):
    def edit_profile(self):
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
            request.context = user
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


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='edit_profile', request_param='__formid__=edit_profile')
@view_config(attr='disable_user', request_param='__formid__=disable_user')
class AsyncProfileController(ProfileController):
    __view_mapper__ = AsyncFormViewMapper


def includeme(config):
    registry = config.registry
    settings = registry.settings

    authz_endpoint = settings.get('auth.local.authorize', '/oauth/authorize')
    config.add_route('auth.local.authorize', authz_endpoint)

    token_endpoint = settings.get('auth.local.token', '/oauth/token')
    config.add_route('auth.local.token', token_endpoint)
    config.add_route('disable_user', '/disable/{user_id}',
                     factory=UserFactory,
                     traverse="/{user_id}")

    config.include('horus')
    config.scan(__name__)
