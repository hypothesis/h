# -*- coding: utf-8 -*-

from h.api import models as api_models

__all__ = (
    'Annotation',
    'Document',
    'Client',
)


Annotation = api_models.Annotation
Document = api_models.Document


class Client(object):

    """A basic implementation of :class:`h.interfaces.IClient`."""

    def __init__(self, request, client_id):
        self.client_id = client_id
        self.client_secret = None
