# -*- coding: utf-8 -*-
import colander
import deform
import horus.views
from horus.lib import FlashMessage
from horus.resources import UserFactory
from pyramid import httpexceptions, security
from pyramid.view import view_config, view_defaults

from h.auth.local import forms, models, schemas
from h.models import _


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
    csrf_token = request.session.get_csrf_token()
    session = {k: v for k, v in request.session.items() if k[0] != '_'}
    session['csrf_token'] = csrf_token  # bw compat
    session['certificate'] = csrf_token
    if request.cookies.get('XSRF-TOKEN') != csrf_token:
        request.response.set_cookie('XSRF-TOKEN', csrf_token)
    return session


def remember(request, user):
    if user is not None:
        userid = 'acct:{}@{}'.format(user.username, request.domain)
        headers = security.remember(request, userid)
        request.response.headerlist.extend(headers)


# TODO: change to something other than /app
@view_config(accept='application/json',  name='app', renderer='json')
def session(request):
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


@view_defaults(accept='text/html', renderer='h:templates/auth.pt')
@view_config(attr='login', route_name='login')
@view_config(attr='logout', route_name='logout')
class AuthController(horus.views.AuthController):
    def login(self):
        request = self.request
        result = super(AuthController, self).login()
        remember(request, request.user)
        return result


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='login', request_param='__formid__=login')
@view_config(attr='logout', request_param='__formid__=logout')
class AsyncAuthController(AuthController):
    __view_mapper__ = AsyncFormViewMapper


@view_defaults(accept='text/html', renderer='h:templates/auth.pt')
@view_config(attr='forgot_password', route_name='forgot_password')
@view_config(attr='reset_password', route_name='reset_password')
class ForgotPasswordController(horus.views.ForgotPasswordController):
    def reset_password(self):
        request = self.request
        result = super(ForgotPasswordController, self).reset_password()
        remember(request, request.user)
        return result


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='forgot_password', request_param='__formid__=forgot')
class AsyncForgotPasswordController(ForgotPasswordController):
    __view_mapper__ = AsyncFormViewMapper


@view_defaults(accept='text/html', renderer='h:templates/auth.pt')
@view_config(attr='register', route_name='register')
@view_config(attr='activate', route_name='activate')
class RegisterController(horus.views.RegisterController):
    def register(self):
        request = self.request
        result = super(RegisterController, self).register()
        remember(request, request.user)
        return result


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='register', request_param='__formid__=register')
@view_config(attr='activate', request_param='__formid__=activate')
class AsyncRegisterController(RegisterController):
    __view_mapper__ = AsyncFormViewMapper

    def activate(self):
        """Activate a user and set a password given an activation code.

        This view is different from the activation view in horus because it
        does not require the user id to be passed. It trusts the activation
        code and updates the password.
        """
        request = self.request
        Str = self.Str

        schema = schemas.ActivateSchema.bind(request=request)
        form = forms.ActivateForm(schema)
        appstruct = None

        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return dict(errors=e.error.children)

        code = appstruct['code']
        activation = models.Activation.get_by_code(request, code)

        user = None
        if activation:
            user = self.User.get_by_activation(request, activation)

        if user is None:
            return dict(errors=[{'activation_code': _('This activation code is not valid.')}])

        user.password = appstruct['password']
        self.db.delete(activation)
        self.db.add(user)

        FlashMessage(request, Str.reset_password_done, kind='success')
        remember(request, user)
        return {}


@view_defaults(accept='text/html', renderer='h:templates/account.html')
@view_config(attr='edit_profile', route_name='edit_profile')
@view_config(attr='disable_user', route_name='disable_user')
class ProfileController(horus.views.ProfileController):
    def edit_profile(self):
        request = self.request
        schema = schemas.EditProfileSchema.bind(schemas.EditProfileSchema(),
                                                request=request)
        form = forms.EditProfileForm(schema)

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
            return dict(errors=[{'pwd':_('Invalid password')}], code=401)

    def disable_user(self):
        request = self.request
        schema = schemas.EditProfileSchema.bind(schemas.EditProfileSchema(),
                                                request=request)
        form = forms.EditProfileForm(schema)

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
            FlashMessage(self.request, _('User disabled'), kind='success')
            return {}
        else:
            return dict(errors=[{'pwd':_('Invalid password')}], code=401)


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
