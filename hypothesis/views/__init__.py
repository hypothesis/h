def includeme(config):
    config.scan(__name__)
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')
