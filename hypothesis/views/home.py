from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.view import view_config

from .. resources import site_styles
from .. forms.auth import LoginForm, RegisterForm

@view_config(route_name='home', renderer='home.jinja2')
def home_view(request):
    site_styles.need()

    if request.user is None:
        action = request.params.get('action', 'login')
        if action == 'login':
            form = LoginForm().render(submit_text='Sign In', action=action)
        elif action == 'register':
            form = RegisterForm().render(submit_text='Register', action=action)
        return {
            'action': action,
            'form': form
        }
    else:
        return {}
