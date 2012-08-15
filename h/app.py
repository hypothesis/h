from functools import partial

from apex import logout
from apex.models import AuthID, AuthUser
from apex.views import get_came_from

from colander import Schema, SchemaNode

from deform import Button, Form, Field
from deform.widget import MappingWidget

from pyramid.httpexceptions import HTTPBadRequest, HTTPRedirection, HTTPSeeOther
from pyramid.renderers import render
from pyramid.security import forget, remember
from pyramid.view import view_config

from . schemas import (login_validator, register_validator,
                       LoginSchema, RegisterSchema, PersonaSchema)
from . views import FormView

@view_config(renderer='templates/app.pt', route_name='app')
@view_config(renderer='json', route_name='app', xhr=True)
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
            action="?action=%s&came_from=%s" % (
                action,
                request.current_route_path(),
            ),
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
            view.ajax_options = """{
              success: authSuccess,
              target: null,
              type: 'POST'
            }"""
            view.use_ajax = True
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

class forgot(FormView):
    pass

class login(FormView):
    schema = LoginSchema(validator=login_validator)
    buttons = (
        Button('log in', type='submit'),
        Button('forgot', title='Password help?'),
    )
    form_class = partial(Form,
                         bootstrap_form_style='form-vertical',
                         formid='auth')

    def log_in_success(self, form):
        request = self.request
        user = (
            AuthUser.get_by_login(form['username']) or
            AuthUser.get_by_email(form['username'])
        )
        headers = remember(request, user.auth_id)
        return HTTPSeeOther(headers=headers, location=get_came_from(request))

class register(FormView):
    schema = RegisterSchema(validator=register_validator)
    buttons = ('sign up',)
    form_class = partial(Form,
                         bootstrap_form_style='form-vertical',
                         formid='auth')

    def sign_up_success(self, form):
        request = self.request
        db = request.db
        id = AuthID()
        db.add(id)
        user = AuthUser(login=form['username'],
                        password=form['password'],
                        email=form['email'])
        id.users.append(user)
        db.add(user)
        db.flush()
        headers = remember(request, user.auth_id)
        return HTTPSeeOther(headers=headers, location=get_came_from(request))

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

    config.add_view(lambda r: {}, name='appcache.mf',
                    renderer='templates/appcache.pt')

    config.scan(__name__)
