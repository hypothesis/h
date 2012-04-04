from pyramid.view import view_config

from . forms.auth import LoginForm, RegisterForm

@view_config(route_name='home', renderer='home.jinja2')
def home(request):
    request.need('.resources:site_styles')

    action = request.params.get('action', request.user and 'logout' or 'login')
    form = '<a href="' + request.route_url('apex_logout') + '">' + \
           'Log out.' + '</a>'
    if request.user is None:
        if action == 'login':
            form = LoginForm().render(submit_text='Sign In', action=action)
        else:
            form = RegisterForm().render(submit_text='Register', action=action)
    return {
        'action': action,
        'form': form
    }

def includeme(config):
    config.scan(__name__)
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')
