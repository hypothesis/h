from pyramid.settings import aslist
import gnsq


def get_reader(request, topic, channel):
    """
    Get a :py:class:`gnsq.Reader` instance configured to connect to the
    nsqd reader addresses specified in settings. The reader will read from
    the specified topic and channel.

    The caller is responsible for adding appropriate `on_message` hooks and
    starting the reader.
    """
    addrs = aslist(request.registry.settings.get('nsq.reader.addresses',
                                                 'localhost:4150'))
    topic = _topic_name(request, topic)
    reader = gnsq.Reader(topic, channel, nsqd_tcp_addresses=addrs)
    return reader


def get_writer(request):
    """
    Get a :py:class:`gnsq.Nsqd` instance configured to connect to the nsqd
    writer address configured in settings. The writer communicates over the
    nsq HTTP API and does not hold a connection open to the nsq instance.
    """
    setting = request.registry.settings.get('nsq.writer.address',
                                            'localhost:4151')
    hostname, port = setting.split(':', 1)
    nsqd = gnsq.Nsqd(hostname, http_port=port)
    return nsqd


def _topic_name(request, name):
    ns = request.registry.settings.get('nsq.namespace')
    if ns is None:
        return name
    return '{0}-{1}'.format(ns, name)


def includeme(config):
    config.add_request_method(get_reader, name='get_queue_reader')
    config.add_request_method(get_writer, name='get_queue_writer')
