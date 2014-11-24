from . import interfaces


# Because pyramid can't accept functools.partial objects as arguments to
# Configurator.add_directive, we have to implement our own closure-based
# version. Ugh.
def partial(func, qh):
    def _func(*args, **kwargs):
        return func(qh, *args, **kwargs)
    return _func


def _get_queue_reader(qh, config_or_request, *args, **kwargs):
    return qh.get_reader(config_or_request.registry.settings, *args, **kwargs)


def _get_queue_writer(qh, config_or_request, *args, **kwargs):
    return qh.get_writer(config_or_request.registry.settings, *args, **kwargs)


def includeme(config):
    queue_helper_ctor = config.registry.getUtility(interfaces.IQueueHelper)
    queue_helper = queue_helper_ctor()

    get_reader = partial(_get_queue_reader, queue_helper)
    get_writer = partial(_get_queue_writer, queue_helper)
    config.add_directive('get_queue_reader', get_reader)
    config.add_directive('get_queue_writer', get_writer)
    config.add_request_method(get_reader, name='get_queue_reader')
    config.add_request_method(get_writer, name='get_queue_writer')
