from apex import login

def home(request):
    context = {'title': 'hypothes.is'}
    if request.user is None:
        if request.POST:
            return login(request)
        result = login(request)
        result.update(context)
        context = result
    return context

def includeme(config):
    config.include('pyramid_jinja2')
    config.add_jinja2_extension('jinja2.ext.do')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')
    config.add_view(home, route_name='home', renderer='home.jinja2')
