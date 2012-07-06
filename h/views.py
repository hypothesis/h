from functools import partial
import json
import re

from apex import logout
from apex.models import AuthID, AuthUser

from colander import deferred, Invalid, Length, Schema, SchemaNode, String, Email
from deform.form import Form
from deform.widget import FormWidget, PasswordWidget, SelectWidget

from pyramid.httpexceptions import HTTPRedirection, HTTPSeeOther
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.security import forget, remember, NO_PERMISSION_REQUIRED
from pyramid.view import render_view_to_response

from pyramid_deform import CSRFSchema, FormView
from pyramid_webassets import IWebAssetsEnvironment

import api

# Deform validators
# =================

def login_validator(node, kw):
    """Validate a username and password."""
    valid = False
    if 'username' in kw:
        valid = AuthUser.check_password(
            login=kw['username'],
            password=kw['password']
        )
    if not valid:
        raise Invalid(
            node,
            "Please, try again."
        )

def register_validator(node, kw):
    """Validate a username and password."""
    valid = False
    if 'password' in kw:
        if kw['password'] != kw.get('password2', None):
            raise Invalid(node, "Passwords should match!")
    used = AuthUser.get_by_login(kw['username'])
    used = used or AuthUser.get_by_email(kw['email'])
    if used:
        raise Invalid(node, "That username or email is taken.")

# Form Schemas
# ============

class LoginSchema(CSRFSchema):
    username = SchemaNode(
        String(),
        validator=Length(min=4, max=25),
        placeholder="Username or Email"
    )
    password = SchemaNode(
        String(),
        widget=PasswordWidget(),
        placeholder="Password"
    )

class RegisterSchema(LoginSchema):
    password2 = SchemaNode(
        String(),
        title='Password',
        widget=PasswordWidget(),
    )
    email = SchemaNode(
        String(),
        validator=Email()
    )

class PersonaSchema(CSRFSchema):
    persona = SchemaNode(
        String(),
        widget=deferred(
            lambda node, kw: SelectWidget(
                values=api.users(kw['request']) + [(-1, 'Sign out')])
        ),
    )

class FormView(FormView):
    """Base class for form views that adds additional capabilities to forms.

    Primarily, this passes any keyword arguments received by the constructor
    to the form class. This addition allows customizing a form slightly at
    instantiation time, such as based on request parameters or session state.
    Perhaps this should be merged into pyramid_deform.

    Deform comes with AJAH support in the form of `use_ajax = True` on the
    form class but this attemps to go further. Using the form id, the page should
    post back its URL with XHR and, by defining a mapping of form ids to
    form views for from the original view handler, construct pages which are
    a composite of forms.

    I'm sure there are some well tread patterns around for this. For now it's
    a sketch of an idea and a harmless base class.

    """

    use_ajax = True
    ajax_options = json.dumps({
        'type': 'POST'
    })

    def __init__(self, request, **kwargs):
        super(FormView, self).__init__(request)
        self.form_class = partial(self.form_class, **kwargs)

    def __call__(self):
        result = super(FormView, self).__call__()
        if self.request.is_xhr:
            if isinstance(result, Response):
                raise result
            return result['form']
        else:
            return result

    @property
    def partial(self):
        return getattr(self, self.request.params['__formid__'])

# Forms
# =====

class login(FormView):
    schema = LoginSchema(validator=login_validator)
    buttons = ('log in',)

    def __call__(self):
        if self.request.user:
            return HTTPSeeOther(location=self._came_from)
        return super(login, self).__call__()

    @property
    def _came_from(self):
        formid = self.request.params.get('__formid__')
        app = self.request.route_url('app', _query=(('__formid__', formid),))
        return self.request.params.get('came_from', app)

    def log_in_success(self, form):
        user = AuthUser.get_by_login(form['username'])
        headers = remember(self.request, user.auth_id)
        return HTTPSeeOther(headers=headers, location=self._came_from)

class register(FormView):
    schema = RegisterSchema(validator=register_validator)
    buttons = ('register',)
    use_ajax = False
    form_class = partial(Form,
                         bootstrap_form_style='form-vertical',
                         formid='auth')

    def __call__(self):
        if self.request.user:
            return HTTPSeeOther(location=self.request.route_url('home'))
        return super(register, self).__call__()

    def register_success(self, form):
        session = self.request.db
        id = AuthID()
        session.add(id)
        user = AuthUser(login=form['username'],
                        password=form['password'],
                        email=form['email'])
        id.users.append(user)
        session.add(user)
        session.flush()
        headers = remember(self.request, user.auth_id)
        return HTTPSeeOther(headers=headers, location=self.request.route_url('home'))

class persona(FormView):
    schema = PersonaSchema()

# Views
# =====

class app(FormView):
    def __init__(self, request):
        self.request = request

    @property
    def auth(self):
        form_style = self.request.user and 'form-horizontal' or 'form-vertical'
        return auth(self.request)(
            self.request,
            action='app',
            bootstrap_form_style=form_style,
            formid='auth',
        )

    def __call__(self):
        request = self.request
        assets_env = self.request.registry.queryUtility(IWebAssetsEnvironment)
        form = self.auth()
        form['css_links'].extend(assets_env['app_css'].urls())
        return form

def auth(request):
    if request.user:
        return persona
    else:
        return login

def embed(request):
    assets_env = request.registry.queryUtility(IWebAssetsEnvironment)
    return {
        pkg: json.dumps(assets_env[pkg].urls())
        for pkg in ['easyXDM', 'injector', 'inject_css', 'jquery']
    }

class home(FormView):
    def __init__(self, request):
        self.request = request

    @property
    def auth(self):
        return auth(self.request)(
            self.request,
            action='app',
            bootstrap_form_style='form-vertical',
            formid='auth',
        )

    def __call__(self):
        request = self.request
        assets_env = request.registry.queryUtility(IWebAssetsEnvironment)
        code = render('h:templates/embed.pt', embed(request), request=request)
        form = self.auth()
        form.setdefault('css_links', []).extend(assets_env['site_css'].urls())
        form.setdefault('js_scripts', []).append(code)
        return form

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')
    config.include('velruse.app')

    config.add_view(app, renderer='templates/app.pt', route_name='app')
    config.add_view(app, renderer='string', route_name='app',
                    attr='partial', xhr=True)

    config.add_view(home, renderer='templates/home.pt')
    config.add_view(home, attr='partial', renderer='templates/form.pt', xhr=True)

    config.add_view(login, route_name='login')
    config.add_view(logout, route_name='logout')
    config.add_view(register, route_name='register')
    config.add_view(lambda r: {}, route_name='forgot')

    config.add_view(
        lambda r: Response(
            body=render('h:templates/embed.pt', embed(r), request=r),
            cache_control='must-revalidate',
            content_type='application/javascript',
            charset='utf-8'),
        route_name='embed')

    config.add_static_view('h/annotator', 'h:annotator')
    config.add_static_view('h/sass', 'h:sass')
    config.add_static_view('h/js', 'h:js')
    config.add_static_view('h/images', 'h:images')
