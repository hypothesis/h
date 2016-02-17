# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from annotator import annotation
from annotator import document
from pyramid import security

from h._compat import text_type
from h.api import auth


class Annotation(annotation.Annotation):
    @property
    def id(self):
        return self.get('id')

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
    def parent_id(self):
        """
        Return the id of the thread parent of this annotation, if it exists.
        """
        if 'references' not in self:
            return None
        if not isinstance(self['references'], list):
            return None
        if not self['references']:
            return None
        return self['references'][-1]

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

    def __acl__(self):
        """
        Return a Pyramid ACL for this annotation.

        We calculate the ACL dynamically from the value of the `permissions`
        attribute of the annotation data.
        """
        acl = []

        # Convert annotator-store roles to pyramid principals
        for action, roles in self.get('permissions', {}).items():
            principals = auth.translate_annotation_principals(roles)

            for principal in principals:
                rule = (security.Allow, principal, action)
                acl.append(rule)

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(security.DENY_ALL)

        return acl


class Document(document.Document):
    __analysis__ = {}
