import gnsq
from zope.interface import implementer

from . import interfaces


@implementer(interfaces.IQueueHelper)
class NSQHelper(object):
    def __init__(self, settings):
        self.settings = settings

    def get_reader(self, topic, channel):
        """
        Get a :py:class:`gnsq.Reader` instance configured to connect to the
        nsqd reader addresses specified in settings. The reader will read from
        the specified topic and channel.

        The caller is responsible for adding appropriate `on_message` hooks and
        starting the reader.
        """
        setting = self.settings.get('nsq.reader.addresses', 'localhost:4150')
        addrs = [line for line in setting.splitlines() if line]
        reader = gnsq.Reader(topic, channel, nsqd_tcp_addresses=addrs)
        return reader

    def get_writer(self):
        """
        Get a :py:class:`gnsq.Nsqd` instance configured to connect to the nsqd
        writer address configured in settings. The writer communicates over the
        nsq HTTP API and does not hold a connection open to the nsq instance.
        """
        setting = self.settings.get('nsq.writer.address', 'localhost:4151')
        hostname, port = setting.split(':', 1)
        nsqd = gnsq.Nsqd(hostname, http_port=port)
        return nsqd


def includeme(config):
    registry = config.registry
    settings = registry.settings

    if not registry.queryUtility(interfaces.IQueueHelper):
        qh = NSQHelper(settings)
        registry.registerUtility(qh, interfaces.IQueueHelper)
