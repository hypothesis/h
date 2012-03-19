from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from .. assets import site_styles
from .. models.auth import LoginForm, RegisterForm

import json

@view_config(route_name='home', renderer='home.jinja2')
def home_view(request):
    site_styles.need()

    if request.user is None:
        form = LoginForm().render(
            action='/auth/login',
            submit_text='Log In')
        return {'form': form}
    else:
        return {}
