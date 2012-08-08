from functools import partial

from apex import logout
from apex.models import AuthID, AuthUser

from colander import Schema, SchemaNode

from deform import Form, Field
from deform.widget import MappingWidget

from pyramid.httpexceptions import HTTPBadRequest, HTTPRedirection, HTTPSeeOther
from pyramid.renderers import render
from pyramid.security import forget, remember
from pyramid.view import view_config

from . schemas import (login_validator, register_validator,
                       LoginSchema, RegisterSchema, PersonaSchema)
from . views import FormView

@view_config(name='app')
class app(FormView):
    @property
    def auth(self):
        request = self.request
        action = request.params.get('action', 'login')

        if action == 'login':
            form = login
        elif action == 'register':
            form = register
        else:
            raise HTTPBadRequest()

        return form(
            request,
            action="?action=%s" % action,
            bootstrap_form_style='form-vertical',
            formid='auth',
        )

    @property
    def persona(self):
        request = self.request

        # logout request
        if request.params.get('persona', None) == '-1':
            request.add_response_callback(
                lambda req, res: logout(req).merge_cookies(res)
            )
            request.user = None

        return persona(
            request,
            bootstrap_form_style='form-horizontal',
            readonly=bool(not request.user),
            formid='persona',
        )

    def __init__(self, request):
        self.request = request

    def __call__(self):
        self.requirements = []
        result = {
            'css_links': [],
            'js_links': [],
            'form': {},
        }
        for name in ['auth', 'persona']:
            view = getattr(self, name)
            form = view()
            if isinstance(form, dict):
                for links in ['css_links', 'js_links']:
                    for l in form.pop(links, []):
                        if l not in result[links]:
                            result[links].append(l)
                result['form'][name] = form['form']
            else:
                return form

        return result

@view_config(route_name='forgot')
class forgot(FormView):
    pass

@view_config(route_name='login')
class login(FormView):
    schema = LoginSchema(validator=login_validator)
    buttons = ('log in',)
    ajax_options = """{
      success: authSuccess,
      target: null,
      type: 'POST'
    }"""

    @property
    def _came_from(self):
        formid = self.request.params.get('__formid__')
        app = self.request.route_url('app', _query=(('__formid__', formid),))
        return self.request.params.get('came_from', app)

    def log_in_success(self, form):
        user = AuthUser.get_by_login(form['username'])
        headers = remember(self.request, user.auth_id)
        return HTTPSeeOther(headers=headers, location=self._came_from)

@view_config(route_name='register')
class register(FormView):
    schema = RegisterSchema(validator=register_validator)
    buttons = ('sign up',)
    form_class = partial(Form,
                         bootstrap_form_style='form-vertical',
                         formid='auth')
    ajax_options = """{
      success: authSuccess,
      target: null,
      type: 'POST'
    }"""

    @property
    def _came_from(self):
        formid = self.request.params.get('__formid__')
        app = self.request.route_url('app', _query=(('__formid__', formid),))
        return self.request.params.get('came_from', app)

    def sign_up_success(self, form):
        db = self.request.db
        id = AuthID()
        db.add(id)
        user = AuthUser(login=form['username'],
                        password=form['password'],
                        email=form['email'])
        id.users.append(user)
        db.add(user)
        db.flush()
        headers = remember(self.request, user.auth_id)
        return HTTPSeeOther(headers=headers, location=self._came_from)

class persona(FormView):
    schema = PersonaSchema()
    ajax_options = """{
      success: authSuccess,
      target: null,
      type: 'POST'
    }"""

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')
    config.include('velruse.app')

    config.add_view(app, renderer='templates/app.pt', route_name='app')
    config.add_view(app, renderer='json', route_name='app', xhr=True)

    config.add_view(lambda r: {}, name='appcache.mf',
                    renderer='templates/appcache.pt')

    config.scan(__name__)

