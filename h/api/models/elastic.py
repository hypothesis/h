# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from dateutil import parser as dateparser
import re

from annotator import annotation
from annotator import document
from pyramid import security

from h.api import uri
from h.api._compat import text_type


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
    def target_uri_normalized(self):
        target_uri = self.target_uri
        if target_uri:
            return uri.normalize(target_uri)

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
            return Document(self['document'],
                            claimant=self.target_uri,
                            created=self.created,
                            updated=self.updated)

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

    def __init__(self, *args, **kwargs):
        self.claimant = kwargs.pop('claimant', None)
        self.created = kwargs.pop('created', None)
        self.updated = kwargs.pop('updated', None)

        super(Document, self).__init__(*args, **kwargs)

    @property
    def title(self):
        value = self.get('title')
        if isinstance(value, list):
            try:
                return value[0]
            except IndexError:
                return None

        return value

    @property
    def meta(self):
        items = {k: v for k, v in self.iteritems() if k != 'link'}
        meta = []
        self._transform_meta(meta, items)
        return meta

    @property
    def document_uris(self):
        return [DocumentURI(link) for link in self._transform_links()]

    def _transform_meta(self, meta, data, path_prefix=None):
        if path_prefix is None:
            path_prefix = []

        for key, value in data.iteritems():
            keypath = path_prefix[:]
            keypath.append(key)

            if isinstance(value, dict):
                self._transform_meta(meta, value, path_prefix=keypath)
            else:
                if not isinstance(value, list):
                    value = [value]

                m = DocumentMeta({'type': '.'.join(keypath),
                                  'value': value,
                                  'claimant': self.claimant,
                                  'created': self.created,
                                  'updated': self.updated})
                meta.append(m)

    def _transform_links(self):
        transformed = []
        links = self.get('link', [])

        # add self-claim uri when claimant is not missing
        if self.claimant:
            transformed.append({'claimant': self.claimant,
                                'uri': self.claimant,
                                'type': 'self-claim',
                                'created': self.created,
                                'updated': self.updated})

        # When document link is just a string, transform it to a link object with
        # an href, so it gets further processed as either a self-claim or another
        # claim.
        if isinstance(links, basestring):
            links = [{"href": links}]

        for link in links:
            # disregard self-claim urls as they have already been added
            if link.keys() == ['href'] and link['href'] == self.claimant:
                continue

            # disregard doi links as these are being added separately from the
            # highwire and dc metadata later on.
            if link.keys() == ['href'] and link['href'].startswith('doi:'):
                continue

            uri_ = link['href']
            type = None

            # highwire pdf (href, type=application/pdf)
            if set(link.keys()) == set(['href', 'type']) and len(link.keys()) == 2:
                type = 'highwire-pdf'

            if type is None and link.get('rel') is not None:
                type = 'rel-{}'.format(link['rel'])

            content_type = None
            if link.get('type'):
                content_type = link['type']

            transformed.append({'claimant': self.claimant,
                                'uri': uri_,
                                'type': type,
                                'content_type': content_type,
                                'created': self.created,
                                'updated': self.updated})

        # Add highwire doi link based on metadata
        hwdoivalues = self.get('highwire', {}).get('doi', [])
        for doi in hwdoivalues:
            if not doi.startswith('doi:'):
                doi = "doi:{}".format(doi)

            transformed.append({'claimant': self.claimant,
                                'uri': doi,
                                'type': 'highwire-doi',
                                'created': self.created,
                                'updated': self.updated})

        # Add dc doi link based on metadata
        dcdoivalues = self.get('dc', {}).get('identifier', [])
        for doi in dcdoivalues:
            if not doi.startswith('doi:'):
                doi = "doi:{}".format(doi)

            transformed.append({'claimant': self.claimant,
                                'uri': doi,
                                'type': 'dc-doi',
                                'created': self.created,
                                'updated': self.updated})

        return transformed


class DocumentMeta(dict):
    @property
    def created(self):
        return self.get('created')

    @property
    def updated(self):
        return self.get('updated')

    @property
    def claimant(self):
        return self.get('claimant')

    @property
    def claimant_normalized(self):
        claimant = self.claimant
        if claimant:
            return uri.normalize(claimant)

    @property
    def type(self):
        return self.get('type')

    @property
    def value(self):
        return self.get('value')

    @property
    def normalized_type(self):
        """
        Normalized version of the type string

        This should only be used in the Postgres migration script.
        """
        value = self.type
        if value:
            value = value.lower().replace(':', '.')
            value = re.sub(r'\.{2,}', '.', value)
            value = re.sub(r'^og\.', 'facebook.', value)

        return value


class DocumentURI(dict):
    @property
    def created(self):
        return self.get('created')

    @property
    def updated(self):
        return self.get('updated')

    @property
    def claimant(self):
        return self.get('claimant')

    @property
    def claimant_normalized(self):
        claimant = self.claimant
        if claimant:
            return uri.normalize(claimant)

    @property
    def uri(self):
        return self.get('uri')

    @property
    def uri_normalized(self):
        uri_ = self.uri
        if uri_:
            return uri.normalize(uri_)

    @property
    def type(self):
        return self.get('type')

    @property
    def content_type(self):
        return self.get('content_type')
