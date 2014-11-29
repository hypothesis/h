from zope.interface import Interface


class IQueueHelper(Interface):
    def __init__(self, settings):  # noqa
        """
        Initialize a queue helper from the provided settings.
        """

    def get_reader(self, settings, topic, channel):  # noqa
        """
        Get a queue reader in order to retrieve topic from the specified topic
        and channel.
        """

    def get_writer(self, settings):  # noqa
        """
        Get a queue writer in order to push work onto a queue.
        """
