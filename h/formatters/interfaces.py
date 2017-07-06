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
    """

    def format(annotation_resource):  # noqa: N805
        """
        Presents additional annotation data that will be served to API clients.

        :param annotation_resource: The annotation that needs presenting.
        :type annotation_resource: h.resources.AnnotationResource

        :returns: A formatted dictionary.
        :rtype: dict
        """
