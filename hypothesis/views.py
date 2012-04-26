from apex import login

def home(request):
    result = None
    if request.user is None:
        if request.POST:
            return login(request)
        result = login(request)
        del result['title']
    return result or {}

def includeme(config):
    config.include('pyramid_jinja2')

    # Set up webassets extension
    config.include('pyramid_webassets')
    assets_environment = config.get_webassets_env()
    config.add_jinja2_extension('webassets.ext.jinja2.AssetsExtension')
    config.get_jinja2_environment().assets_environment = assets_environment

    # Set up template search paths
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')

    # Set up views
    config.add_view(home, route_name='home', renderer='home.jinja2')
