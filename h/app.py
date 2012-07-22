from functools import partial

from apex import logout
from apex.models import AuthID, AuthUser

from deform import Form

from pyramid.httpexceptions import HTTPRedirection, HTTPSeeOther
from pyramid.security import forget, remember

from pyramid_webassets import IWebAssetsEnvironment

from . schemas import (login_validator, register_validator,
                       LoginSchema, RegisterSchema, PersonaSchema)
from . views import FormView

class app(FormView):
    def __init__(self, request):
        self.request = request

    @property
    def auth(self):
        request = self.request

        # log out request
        if request.POST.get('persona', None) == '-1':
            request.response.merge_cookies(logout(request))
            request.session.invalidate()
            request.user = None

        form_style = request.user and 'form-horizontal' or 'form-vertical'
        return (request.user and persona or login)(
            request,
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

class login(FormView):
    schema = LoginSchema(validator=login_validator)
    buttons = ('log in',)
    ajax_options = """{
      success: loginSuccess,
      type: 'POST'
    }"""

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
    ajax_options = """{
      success: personaSuccess,
      type: 'POST'
    }"""

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')
    config.include('velruse.app')

    config.add_view(app, renderer='templates/app.pt', route_name='app')
    config.add_view(app, renderer='string', route_name='app',
                    attr='partial', xhr=True)

    config.add_view(lambda r: {}, name='appcache.mf',
                    renderer='templates/appcache.pt')

    config.add_view(
        lambda r: Response(
            body=render('h:templates/embed.pt', embed(r), request=r),
            cache_control='must-revalidate',
            content_type='application/javascript',
            charset='utf-8'),
        route_name='embed')

    config.add_view(login, route_name='login')
    config.add_view(logout, route_name='logout')
    config.add_view(register, route_name='register')
    config.add_view(lambda r: {}, route_name='forgot')

