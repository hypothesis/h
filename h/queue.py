# -*- coding: utf-8 -*-
from pyramid.settings import aslist
import gnsq


class NamespacedNsqd(object):
    def __init__(self, namespace, *args, **kwargs):
        self.client = gnsq.Nsqd(*args, **kwargs)
        self.namespace = namespace

    def publish(self, topic, data):
        if self.namespace is not None:
            topic = '{0}-{1}'.format(self.namespace, topic)
        return self.client.publish(topic, data)


def get_reader(request, topic, channel):
    """
    Get a :py:class:`gnsq.Reader` instance configured to connect to the
    nsqd reader addresses specified in settings. The reader will read from
    the specified topic and channel.

    The caller is responsible for adding appropriate `on_message` hooks and
    starting the reader.
    """
    ns = request.registry.settings.get('nsq.namespace')
    addrs = aslist(request.registry.settings.get('nsq.reader.addresses',
                                                 'localhost:4150'))
    if ns is not None:
        topic = '{0}-{1}'.format(ns, topic)
    reader = gnsq.Reader(topic, channel, nsqd_tcp_addresses=addrs)
    return reader


def get_writer(request):
    """
    Get a :py:class:`gnsq.Nsqd` instance configured to connect to the nsqd
    writer address configured in settings. The writer communicates over the
    nsq HTTP API and does not hold a connection open to the nsq instance.
    """
    ns = request.registry.settings.get('nsq.namespace')
    addr = request.registry.settings.get('nsq.writer.address',
                                         'localhost:4151')
    hostname, port = addr.split(':', 1)
    nsqd = NamespacedNsqd(ns, hostname, http_port=port)
    return nsqd


def includeme(config):
    config.add_request_method(get_reader, name='get_queue_reader')
    config.add_request_method(get_writer, name='get_queue_writer')
