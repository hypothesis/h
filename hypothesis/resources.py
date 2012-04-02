from fanstatic import Library, Resource, get_library_registry

#from js.annotator import library as annotator
from js.jquery import library as jquery
from js.lesscss import LessResource

hypothesis = Library('hypothesis', 'resources')
site_styles = Resource(hypothesis, 'stylesheets/site.less')

def includeme(config):
    # Set up fanstatic to serve static assets
    fanstatic_settings = {
        'fanstatic.bottom': True,
        'fanstatic.publisher_signature': 'assets',
    }
    config.add_settings(**fanstatic_settings)
    config.include('pyramid_fanstatic')

    # Add the asset libraries to the fanstatic registry
    registry = get_library_registry()
    #registry.add(annotator)
    registry.add(jquery)
    registry.add(hypothesis)

    # Set up the routes
    config.add_route('home', '/')
    config.add_route('token', '/token')
    config.add_route('api', '/api/*subpath')

    config.add_static_view('assets/images', 'hypothesis:resources/images/')
    config.add_static_view('assets/graphics', 'hypothesis:resources/graphics/')
