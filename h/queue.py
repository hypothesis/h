from nsq import client, reader
from pyramid.settings import aslist


def get_reader(request, topic, channel):
    """
    Get a :py:class:`nsq.Reader` instance configured to connect to the
    nsqd reader addresses specified in settings. The reader will read from
    the specified topic and channel, optionally prefixing the topic with a
    namespace.
    """
    ns = request.registry.settings.get('nsq.namespace')
    addrs = aslist(request.registry.settings.get('nsq.reader.addresses',
                                                 'localhost:4150'))

    if ns is not None:
        topic = '{0}-{1}'.format(ns, topic)

    return reader.Reader(topic, channel, nsqd_tcp_addresses=addrs)


def get_writer(request):
    """
    Get a :py:class:`nsq.client.Client` instance configured to connect to the
    nsqd address configured in settings, optionally prefixing topics with a
    namespace.
    """
    ns = request.registry.settings.get('nsq.namespace')
    addrs = aslist(request.registry.settings.get('nsq.writer.address',
                                                 'localhost:4150'))

    writer = client.Client(nsqd_tcp_addresses=addrs)

    if ns is not None:
        def pub(topic, msg):
            topic = '{0}-{1}'.format(ns, topic)
            client.Client.pub(writer, topic, msg)

        def mpub(topic, msg):
            topic = '{0}-{1}'.format(ns, topic)
            client.Client.mpub(writer, topic, msg)

        writer.pub = pub
        writer.mpub = mpub

    return writer


def includeme(config):
    config.add_request_method(get_reader, name='get_queue_reader')
    config.add_request_method(get_writer, name='get_queue_writer')
