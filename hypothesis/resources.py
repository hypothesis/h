from fanstatic import Library, Resource, get_library_registry, NEEDED

from pyramid.path import DottedNameResolver

library = Library('hypothesis', 'resources')
site_styles = Resource(library, 'stylesheets/site.less')

def fanstatic_need_property(request):
    """A pyramid request property for fanstatic resource inclusions

    Views and templates may use this function wherever the pyramid request object
    is available to require that fanstatic inject links to assets required by
    the request.

    """
    resolver = DottedNameResolver()
    need = request.environ[NEEDED].need
    return (
        lambda resource: need(resolver.maybe_resolve(resource))
    )

def includeme(config):
    # Set up the routes
    config.add_route('home', '/')
    config.add_route('token', '/api/token')
    config.add_route('api', '/api/*subpath')

    # Set up fanstatic
    config.include('pyramid_fanstatic')
    config.set_request_property(fanstatic_need_property, name='need', reify=True)

    # Set up other static views
    config.add_static_view('images', 'resources/images')
