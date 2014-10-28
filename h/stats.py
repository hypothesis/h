import statsd

__all__ = ['get_client']


def get_client(request):
    settings = request.registry.settings
    conn = statsd.Connection(host=settings.get('statsd.host'),
                             port=settings.get('statsd.port'))
    return statsd.Client(__package__, connection=conn)
