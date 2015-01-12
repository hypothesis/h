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
    settings = config.registry.settings

    if any(key.startswith('nsq.') for key in settings.keys()):
        config.include('h.queue.nsq')
    else:
        config.include('h.queue.local')

    config.add_request_method(get_queue_reader, name='get_queue_reader')
    config.add_request_method(get_queue_writer, name='get_queue_writer')
