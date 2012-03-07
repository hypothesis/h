import pyramid_jinja2

def includeme(config):
    # Set up jinja2 templating
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('hypothesis:templates')

    # Scan this package for modules that define views
    config.scan(__name__)
