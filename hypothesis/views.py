from functools import partial
import json
import re

from apex.models import AuthID, AuthUser

from colander import deferred, Invalid, Length, Schema, SchemaNode, String
from deform.form import Form
from deform.widget import FormWidget, PasswordWidget, SelectWidget

from pyramid.httpexceptions import HTTPRedirection, HTTPSeeOther
from pyramid.renderers import get_renderer
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import render_view_to_response

from pyramid_deform import FormView

def login_validator(node, kw):
    valid = False
    if 'username' in kw:
        valid = AuthUser.check_password(
            login=kw['username'],
            password=kw['password']
        )
    if not valid:
        raise Invalid(
            node,
            "User or passord incorrect"
        )

def users(request):
    if not request.user:
        return []
    return [
        (user.id, '%s@%s' % (
            user.login,
            re.sub('^local$', request.host, user.provider)))
        for user in request.user.users
    ]

class LoginSchema(Schema):
    username = SchemaNode(
        String(),
        validator=Length(min=4, max=25),
    )
    password = SchemaNode(
        String(),
        widget=PasswordWidget(),
    )

class UserSelectSchema(Schema):
    accounts = SchemaNode(
        String(),
        widget=deferred(
            lambda node, kw: SelectWidget(values=users(kw['request']))
        ),
    )

class AuthSchema(Schema):
    login = LoginSchema(
        title='Sign in',
        validator=login_validator
    )
    user = UserSelectSchema()

    @staticmethod
    def after_bind(node, kw):
        if kw['request'].user:
            del node['login']
        else:
            del node['user']

class NgFormView(FormView):
    use_ajax = True

    def __init__(self, request, **kwargs):
        super(NgFormView, self).__init__(request)
        self.form_class = partial(self.form_class, **kwargs)

    def failure(self, e):
        if self.request.is_xhr:
            return super(NgFormView, self).failure(e)
        raise HTTPSeeOther(location=self.request.url)

    def show(self, form):
        if self.request.method == 'POST':
            if self.request.is_xhr:
                formid = self.request.params.get('__formid__')
                new_request = self.request.copy_get()
                new_request.user = self.request.user
                new_request.registry = self.request.registry
                context = getattr(self.request, 'context', None)
                response = render_view_to_response(context, new_request, formid)
                response.headers.update(self.request.response.headers)
                return response
            else:
                raise HTTPSeeOther(headers=self.request.response.headers,
                                   location=self.request.url)
        else:
            return super(NgFormView, self).show(form)

class AuthView(NgFormView):
    schema = AuthSchema(after_bind=AuthSchema.after_bind)
    use_ajax = False

    @property
    def buttons(self):
        if self.request.user:
            return ('sign out',)
        else:
            return ('sign in',)

    def sign_in_success(self, form):
        user = AuthUser.get_by_login(form['login']['username'])
        headers = {}
        if user:
            headers = remember(self.request, user.auth_id)
            # TODO: Investigate why request.set_property doesn't seem to work
            self.request.user = AuthID.get_by_id(user.auth_id)
        self.request.response.headers.extend(headers)

    def sign_out_success(self, form):
        headers = forget(self.request)
        self.request.response.headers.extend(headers)
        self.request.user = None

class home(object):
    def __init__(self, request):
        self.request = request

    @property
    def auth(self):
        return AuthView(
            self.request,
            bootstrap_form_style='form-vertical',
            formid='auth')

    @property
    def partial(self):
        return getattr(self, self.request.params['__formid__'])

    def __call__(self):
        return {
            'auth': self.auth()
        }

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')

    config.add_view(home, renderer='templates/home.pt')
    config.add_view(home, attr='partial', renderer='templates/form.pt', xhr=True)
    config.add_view(home, name='auth', attr='auth', renderer='templates/form.pt')

    config.add_static_view('assets/annotator', 'annotator')
    config.add_static_view('assets/css', 'css')
    config.add_static_view('assets/js', 'js')
    config.add_static_view('assets/images', 'images')
