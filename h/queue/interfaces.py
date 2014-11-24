from zope.interface import Interface


class IQueueHelper(Interface):
    def get_reader(settings, topic, channel):  # noqa
        """
        Get a queue reader in order to retrieve topic from the specified topic
        and channel.
        """

    def get_writer(settings):  # noqa
        """
        Get a queue writer in order to push work onto a queue.
        """
