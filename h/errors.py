from pyramid.view import view_config


@view_config(context=Exception, renderer='h:templates/5xx.html')
def error(context, request):
    """Display an error message and if necessary handle it otherwise."""
    if hasattr(request.registry, 'handle_exception'):
        request.registry.handle_exception()
    return {}


def includeme(config):
    config.scan(__name__)
