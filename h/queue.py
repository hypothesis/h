import gnsq


def get_reader(settings, topic, channel):
    """
    Get a :py:class:`gnsq.Reader` instance configured to connect to the nsqd
    reader addresses specified in settings. The reader will read from the
    specified topic and channel.

    The caller is responsible for adding appropriate `on_message` hooks and
    starting the reader.
    """
    setting = settings.get('nsq.reader.addresses', 'localhost:4150')
    addrs = [line for line in setting.splitlines() if line]
    reader = gnsq.Reader(topic, channel, nsqd_tcp_addresses=addrs)
    return reader


def get_writer(settings):
    """
    Get a :py:class:`gnsq.Nsqd` instance configured to connect to the nsqd
    writer address configured in settings. The writer communicates over the nsq
    HTTP API and does not hold a connection open to the nsq instance.
    """
    setting = settings.get('nsq.writer.address', 'localhost:4151')
    hostname, port = setting.split(':', 1)
    nsqd = gnsq.Nsqd(hostname, http_port=port)
    return nsqd


def _get_queue_reader(config_or_request, *args, **kwargs):
    return get_reader(config_or_request.registry.settings, *args, **kwargs)


def _get_queue_writer(config_or_request, *args, **kwargs):
    return get_writer(config_or_request.registry.settings, *args, **kwargs)


def includeme(config):
    config.add_directive('get_queue_reader', _get_queue_reader)
    config.add_directive('get_queue_writer', _get_queue_writer)
    config.add_request_method(_get_queue_reader, name='get_queue_reader')
    config.add_request_method(_get_queue_writer, name='get_queue_writer')
