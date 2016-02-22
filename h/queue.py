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


def get_reader(req, topic, channel):
    """
    Get a :py:class:`gnsq.Reader` instance configured to connect to the
    nsqd reader addresses specified in settings. The reader will read from
    the specified topic and channel.

    The caller is responsible for adding appropriate `on_message` hooks and
    starting the reader.
    """
    settings = req.registry.settings
    addrs = aslist(settings.get('nsq.reader.addresses', 'localhost:4150'))
    topic = resolve_topic(topic, settings=settings)
    reader = gnsq.Reader(topic, channel, nsqd_tcp_addresses=addrs)
    return reader


def get_writer(req):
    """
    Get a :py:class:`gnsq.Nsqd` instance configured to connect to the nsqd
    writer address configured in settings. The writer communicates over the
    nsq HTTP API and does not hold a connection open to the nsq instance.
    """
    settings = req.registry.settings
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
    config.add_request_method(
        lambda req, t, c: get_reader(req, t, c),
        name='get_queue_reader')
    config.add_request_method(
        lambda req: get_writer(req),
        name='get_queue_writer')
