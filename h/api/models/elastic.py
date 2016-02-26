# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from dateutil import parser as dateparser

from annotator import annotation
from annotator import document
from pyramid import security

from h._compat import text_type


class Annotation(annotation.Annotation):
    @property
    def id(self):
        return self.get('id')

    @property
    def created(self):
        if not self.get('created'):
            return None

        try:
            dt = dateparser.parse(self['created'])
            return dt.replace(tzinfo=None)
        except ValueError:
            pass

    @property
    def updated(self):
        if not self.get('updated'):
            return None

        try:
            dt = dateparser.parse(self.get('updated'))
            return dt.replace(tzinfo=None)
        except ValueError:
            pass

    @property
    def target_uri(self):
        uri_ = self.uri
        if uri_:
            return uri_

        target_links = self.target_links
        if target_links:
            return target_links[0]

    @property
    def text(self):
        text = self.get('text', None)
        if text:
            return text

    @property
    def tags(self):
        tags = self.get('tags', None)
        if isinstance(tags, basestring):
            return [tags]
        elif tags:
            return tags

        return []

    @property
    def userid(self):
        return self.get('user')

    @property
    def groupid(self):
        return self.get('group')

    @property
    def shared(self):
        perms = self.get('permissions', {})
        gperm = 'group:{}'.format(self.groupid)

        # Extract a (deduplicated) copy of the read perms field...
        read_perms = list(set(perms.get('read', [])))

        # We explicitly fix up some known weird scenarios with the permissions
        # field. The idea here is to cover the ones we've investigated and know
        # about, but throw a Skip if we see something we don't recognise. Then if
        # necessary we can make a decision on it and add a rule to handle it here.
        #
        # 1. Missing 'read' permissions field. Fix: set the permissions to private.
        if not read_perms:
            read_perms = [self.userid]

        # 2. 'read' permissions field is [None]. Fix: as in 1).
        elif read_perms == [None]:
            read_perms = [self.userid]

        # 3. Group 'read' permissions that don't match the annotation group. I
        #    believe this is a result of a bug where the focused group was
        #    incorrectly restored from localStorage.
        #
        #    CHECK THIS ONE: example annotation ids:
        #
        #    - AVHVDy7M8sFu_DXLVTfR (Jon)
        #    - AVH0xnzy8sFu_DXLVU8L (Jeremy)
        #    - AVHvR_bC8sFu_DXLVUl2 (Jeremy)
        #
        #    Fix: set the permissions to be the correct permissions for the group
        #    the annotation is actually in...
        elif (len(read_perms) == 1 and
              read_perms[0].startswith('group:') and
              read_perms != [gperm]):
            read_perms = [gperm]

        # 4. Read permissions includes 'group:__world__' but also other principals.
        #
        #    This is equivalent to including only 'group:__world__'.
        elif len(read_perms) > 1 and self.groupid == '__world__' and gperm in read_perms:
            read_perms = [gperm]

        if (read_perms != [gperm] and read_perms != [self.userid]):
            # attempt to fix data when client auth state is out of sync by
            # by overriding the permissions with the user of the annotation.
            if read_perms[0].startswith('acct:'):
                return False

        # And, now, we ignore everything other than the read permissions. If
        # they're a group permission the annotation is considered "shared,"
        # otherwise not.
        if read_perms == [gperm]:
            return True

        return False

    @property
    def references(self):
        references = self.get('references')
        if not isinstance(references, list):
            return None

        # Some of the values in the references fields aren't IDs (i.e. they're
        # not base64-encoded UUIDs or base64-encoded flake IDs. Instead,
        # they're base64-encoded random numbers between 0 and 1, in ASCII...
        #
        # So, we filter out things that couldn't possibly be valid IDs.
        return [r for r in references if len(r) in [20, 22]]

    @property
    def target_selectors(self):
        targets = self.get('target', [])
        if targets and isinstance(targets[0], dict):
            return targets[0].get('selector', [])

        return []

    @property
    def extra(self):
        nonextra_keys = ['id', 'created', 'updated', 'user', 'group', 'uri',
                         'text', 'tags', 'target', 'references', 'permissions',
                         'document']
        extra = {k: v for k, v in self.iteritems() if k not in nonextra_keys}
        if extra:
            return extra

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
        if self.get('document') and isinstance(self['document'], dict):
            return Document(self['document'])

    def __acl__(self):
        """
        Return a Pyramid ACL for this annotation.

        We calculate the ACL dynamically from the value of the `permissions`
        attribute of the annotation data.
        """
        acl = []

        # Convert annotator-store roles to pyramid principals
        for action, roles in self.get('permissions', {}).items():
            for r in roles:
                if r.startswith('system.'):
                    continue
                if r == 'group:__world__':
                    p = security.Everyone
                else:
                    p = r
                rule = (security.Allow, p, action)
                acl.append(rule)

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(security.DENY_ALL)

        return acl


class Document(document.Document):
    __analysis__ = {}
