# -*- coding: utf-8 -*-
from zope.interface import Attribute, Interface


class IClientFactory(Interface):

    """An interface representing a factory which accepts a client identifier
    and returns an IClient object."""

    def __call__(client_id):  # noqa pylint: disable=arguments-differ
        """ Return an IClient object."""


class IClient(Interface):

    """An interface representing an OAuth client."""

    client_id = Attribute(
        """
        A unique identifier for this client.

        The identifier should be a URL-safe base64 encoded string.
        """
    )

    client_secret = Attribute(
        """
        A signing secret for client authentication.

        The secret should be a URL-safe base64 encoded string.
        """
    )
