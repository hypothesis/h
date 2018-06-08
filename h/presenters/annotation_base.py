# -*- coding: utf-8 -*-

"""
A base presenter for common properties needed when rendering annotations.
"""

from __future__ import unicode_literals

from h.util.datetime import utc_iso8601


class AnnotationBasePresenter(object):
    def __init__(self, annotation_resource):
        self.annotation_resource = annotation_resource
        self.annotation = annotation_resource.annotation

    @property
    def created(self):
        if self.annotation.created:
            return utc_iso8601(self.annotation.created)

    @property
    def updated(self):
        if self.annotation.updated:
            return utc_iso8601(self.annotation.updated)

    @property
    def links(self):
        """A dictionary of named hypermedia links for this annotation."""
        return self.annotation_resource.links

    @property
    def text(self):
        if self.annotation.text:
            return self.annotation.text
        else:
            return ""

    @property
    def tags(self):
        if self.annotation.tags:
            return self.annotation.tags
        else:
            return []

    @property
    def target(self):
        target = {"source": self.annotation.target_uri}
        if self.annotation.target_selectors:
            target["selector"] = self.annotation.target_selectors

        return [target]
