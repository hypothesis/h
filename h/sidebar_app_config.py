def _websocketize(value):
    """Convert a HTTP(S) URL into a WS(S) URL."""
    if not (value.startswith('http://') or value.startswith('https://')):
        raise ValueError('cannot websocketize non-HTTP URL')
    return 'ws' + value[len('http'):]


def app_config(request):
    """Returns a dict of configuration info for the Hypothesis
       sidebar client application.
    """
    return {
        'apiUrl': request.route_url('api'),
        'websocketUrl': _websocketize(request.route_url('ws')),
    }
