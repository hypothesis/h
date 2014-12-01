from . import interfaces


def get_queue_helper(request):
    return request.registry.getUtility(interfaces.IQueueHelper)


def get_queue_reader(request, *args, **kwargs):
    qh = get_queue_helper(request)
    return qh.get_reader(*args, **kwargs)


def get_queue_writer(request, *args, **kwargs):
    qh = get_queue_helper(request)
    return qh.get_writer(*args, **kwargs)


def includeme(config):
    config.add_request_method(get_queue_reader, name='get_queue_reader')
    config.add_request_method(get_queue_writer, name='get_queue_writer')
