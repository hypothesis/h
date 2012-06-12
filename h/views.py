from functools import partial
import json
import re

from apex.models import AuthID, AuthUser

from colander import deferred, Invalid, Length, Schema, SchemaNode, String
from deform.form import Form
from deform.widget import FormWidget, PasswordWidget, SelectWidget

from pyramid.httpexceptions import HTTPRedirection, HTTPSeeOther
from pyramid.renderers import get_renderer, render
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import render_view_to_response

from pyramid_deform import FormView
from pyramid_webassets import IWebAssetsEnvironment

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
            "Please, try again."
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

    def show(self, form):
        if self.request.method == 'POST' and self.request.is_xhr:
            formid = self.request.params.get('__formid__')
            new_request = self.request.copy_get()
            new_request.user = self.request.user
            new_request.registry = self.request.registry
            context = getattr(self.request, 'context', None)
            response = render_view_to_response(context, new_request, formid)
            response.headers.update(self.request.response.headers)
            return response
        else:
            return super(NgFormView, self).show(form)

class AuthView(NgFormView):
    schema = AuthSchema(after_bind=AuthSchema.after_bind)
    use_ajax = False

    @property
    def buttons(self):
        if self.request.user:
            return tuple()
        else:
            return ('sign in',)

    def sign_in_success(self, form):
        user = AuthUser.get_by_login(form['login']['username'])
        headers = {}
        if user:
            headers = remember(self.request, user.auth_id)
            # TODO: Investigate why request.set_property doesn't seem to work
            self.request.user = AuthID.get_by_id(user.auth_id)
        raise HTTPSeeOther(headers=headers, location=self.request.url)

def embed(request):
    environment = request.registry.queryUtility(IWebAssetsEnvironment)
    return render(
        'templates/embed.pt',
        {
            'jquery': json.dumps(
                map(lambda url: request.relative_url(url, True),
                    environment['jquery'].urls())),
            'd3': json.dumps(
                map(lambda url: request.relative_url(url, True),
                    environment['d3'].urls())),
            'underscore': json.dumps(
                map(lambda url: request.relative_url(url, True),
                    environment['underscore'].urls())),
            'hypothesis': json.dumps(
                map(lambda url: request.relative_url(url, True),
                    environment['annotator'].urls() +
                    environment['handlebars'].urls() +
                    environment['templates'].urls() +
                    environment['jwz'].urls() +
                    environment['app_js'].urls() +
                    environment['app_css'].urls()))
        },
        request=request)

class home(object):
    def __init__(self, request):
        self.request = request

    @property
    def auth(self):
        form_style = 'form-horizontal' if self.request.user else 'form-vertical'
        return AuthView(
            self.request,
            bootstrap_form_style=form_style,
            formid='auth')

    @property
    def partial(self):
        return getattr(self, self.request.params['__formid__'])

    def __call__(self):
        return {
            'auth': self.auth(),
            'embed': embed(self.request)
        }

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')

    config.add_view(home, renderer='templates/home.pt')
    config.add_view(home, attr='partial', renderer='templates/form.pt', xhr=True)
    config.add_view(home, name='auth', attr='auth', renderer='templates/form.pt')

    config.add_view(lambda r: Response(body=embed(r),
                                       content_type='application/javascript',
                                       charset='utf-8'),
                    route_name='embed')

    config.add_static_view('assets/annotator', 'annotator')
    config.add_static_view('assets/css', 'css')
    config.add_static_view('assets/js', 'js')
    config.add_static_view('assets/images', 'images')
