# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from annotator import annotation
from annotator import document

from h._compat import text_type


class Annotation(annotation.Annotation):
    @property
    def uri(self):
        """Return this annotation's URI or an empty string.

        The uri is escaped and safe to be rendered.

        The uri is a Markup object so it won't be double-escaped.

        """
        uri_ = self.get("uri")
        if uri_:
            # Convert non-string URIs into strings.
            # If the URI is already a unicode string this will do nothing.
            # We're assuming that URI cannot be a byte string.
            return text_type(uri_)
        else:
            return ""

    @property
    def parent(self):
        """
        Return the thread parent of this annotation, if it exists.
        """
        if 'references' not in self:
            return None
        if not isinstance(self['references'], list):
            return None
        if not self['references']:
            return None
        return Annotation.fetch(self['references'][-1])

    @property
    def target_links(self):
        """A list of the URLs to this annotation's targets."""
        links = []
        targets = self.get("target")
        if isinstance(targets, list):
            for target in targets:
                if not isinstance(target, dict):
                    continue
                source = target.get("source")
                if source is None:
                    continue
                links.append(source)
        return links

    @property
    def document(self):
        return self.get("document", {})


class Document(document.Document):
    __analysis__ = {}

