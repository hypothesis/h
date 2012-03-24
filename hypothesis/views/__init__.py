import pyramid_jinja2

def includeme(config):
    # Set up jinja2 templating
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')

    # Set up the api component
    config.include('hypothesis.views.api')

    # Scan this package for modules that define views
    config.scan(__name__)
