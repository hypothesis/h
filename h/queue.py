# -*- coding: utf-8 -*-
from pyramid.settings import aslist

import json
import gnsq


class NamespacedNsqd(object):
    def __init__(self, namespace, *args, **kwargs):
        self.client = gnsq.Nsqd(*args, **kwargs)
        self.namespace = namespace

    def publish(self, topic, data):
        topic = resolve_topic(topic, namespace=self.namespace)
        if not isinstance(data, str):
            data = json.dumps(data)
        return self.client.publish(topic, data)


def get_reader(request, topic, channel):
    """
    Get a :py:class:`gnsq.Reader` instance configured to connect to the
    nsqd reader addresses specified in settings. The reader will read from
    the specified topic and channel.

    The caller is responsible for adding appropriate `on_message` hooks and
    starting the reader.
    """
    settings = request.registry.settings

    sentry = getattr(request, 'sentry', None)
    topic = resolve_topic(topic, settings=settings)
    addrs = aslist(settings.get('nsq.reader.addresses', 'localhost:4150'))
    reader = gnsq.Reader(topic, channel, nsqd_tcp_addresses=addrs)

    if sentry is not None:
        extra = {'topic': topic}

        def _capture_exception(message, error):
            if message is not None:
                extra['message'] = message.body
            sentry.captureException(exc_info=True, extra=extra)

        def _capture_error(error):
            sentry.captureException(exc_info=True, extra=extra)

        def _capture_message(message):
            if message is not None:
                extra['message'] = message.body
            sentry.captureMessage(extra=extra)

        reader.on_exception.connect(_capture_exception, weak=False)
        reader.on_giving_up.connect(_capture_message, weak=False)
        reader.on_error.connect(_capture_error, weak=False)

    return reader


def get_writer(request):
    """
    Get a :py:class:`gnsq.Nsqd` instance configured to connect to the nsqd
    writer address configured in settings. The writer communicates over the
    nsq HTTP API and does not hold a connection open to the nsq instance.
    """
    settings = request.registry.settings
    ns = settings.get('nsq.namespace')
    addr = settings.get('nsq.writer.address', 'localhost:4151')
    hostname, port = addr.split(':', 1)
    nsqd = NamespacedNsqd(ns, hostname, http_port=port)
    return nsqd


def resolve_topic(topic, namespace=None, settings=None):
    """
    Return a resolved name for the requested topic.

    This uses the passed `namespace` to resolve the topic name, or,
    alternatively, a pyramid settings object.
    """
    if namespace is not None and settings is not None:
        raise ValueError('you must provide only one of namespace or settings')

    if settings is not None:
        ns = settings.get('nsq.namespace')
    else:
        ns = namespace

    if ns is not None:
        return '{0}-{1}'.format(ns, topic)

    return topic


def includeme(config):
    config.add_request_method(get_reader, name='get_queue_reader')
    config.add_request_method(get_writer, name='get_queue_writer')
