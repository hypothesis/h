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
    config.add_view(home, route_name='home', renderer='home.jinja2')

    config.add_static_view('assets/annotator', 'resources/annotator')
    config.add_static_view('assets/css', 'resources/css')
    config.add_static_view('assets/js', 'resources/js')
    config.add_static_view('assets/images', 'resources/images')
