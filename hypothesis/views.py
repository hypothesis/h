from apex import login

def home(request):
    if request.user is None: return login(request)
    return {}

def includeme(config):
    config.include('pyramid_jinja2')
    config.add_jinja2_extension('jinja2.ext.do')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')
    config.add_view(home, route_name='home', renderer='home.jinja2')
