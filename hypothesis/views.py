from pyramid.view import view_config

from . forms.auth import LoginForm, RegisterForm

@view_config(route_name='home', renderer='home.jinja2')
def home(request):
    action = request.params.get('action', request.user and 'logout' or 'login')
    form = None
    if request.user is None:
        if action == 'login':
            submit_text = 'Sign in'
            form = LoginForm().render(action=action, submit_text=submit_text)
        else:
            submit_text = 'Sign up'
            form = RegisterForm().render(action=action, submit_text=submit_text)
    return {
        'action': action,
        'form': form
    }

def includeme(config):
    config.scan(__name__)
    config.include('pyramid_jinja2')
    config.add_jinja2_extension('jinja2.ext.do')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')
