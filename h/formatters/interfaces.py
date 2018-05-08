# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import Interface


class IAnnotationFormatter(Interface):
    """
    Interface for annotation formatters.

    Annotation formatters are ways to add data to the annotation JSON payload
    without putting everything in the annotation presenter, thus allowing better
    decoupling of code.

    The main method is ``format(annotation_resource)`` which is expected to
    return a dictionary representation based on the passed-in annotation. If
    the formatter depends on other data it should be able to load it on-demand
    for the given annotation.

    Since we are rendering lists of potentially hundreds of annotations in one
    request, formatters need to be able to optimize the fetching of additional
    data (e.g. from the database). Which is why this interface defines the
    ``preload(ids)`` method.
    Each formatter implementation is expected to handle a cache internally which
    is being preloaded with said method.
    """

    def preload(ids):  # noqa: N805
        """
        Batch load data based on annotation ids.

        :param ids: List of annotation ids based on which data should be preloaded.
        :type ids: list of unicode
        """

    def format(annotation_context):  # noqa: N805
        """
        Presents additional annotation data that will be served to API clients.

        :param annotation_context: The annotation that needs presenting.
        :type annotation_context: :py:class`h.traversal.AnnotationContext`

        :returns: A formatted dictionary.
        :rtype: dict
        """
