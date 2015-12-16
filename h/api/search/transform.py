# -*- coding: utf-8 -*-

"""Functions for transforming data for or from the search index."""

from h._compat import string_types
from h.api import nipsa
from h.api import uri
from h.api import groups
from h.api import models


def prepare(annotation):
    """
    Prepare the given annotation for indexing.

    Scan the passed annotation for any target URIs or document metadata URIs
    and add normalized versions of these to the document.
    """
    groups.set_group_if_reply(annotation)
    groups.insert_group_if_none(annotation)
    groups.set_permissions(annotation)

    # FIXME: Remove this in a month or so, when all our clients have been
    # updated. -N 2015-09-25
    _transform_old_style_comments(annotation)

    # FIXME: When this becomes simply part of a search indexing operation, this
    # should probably not mutate its argument.
    _normalize_annotation_target_uris(annotation)

    if 'user' in annotation and nipsa.has_nipsa(annotation['user']):
        annotation['nipsa'] = True


def _normalize_annotation_target_uris(annotation):
    if 'target' not in annotation:
        return
    if not isinstance(annotation['target'], list):
        return
    for target in annotation['target']:
        if not isinstance(target, dict):
            continue
        if 'source' not in target:
            continue
        if not isinstance(target['source'], string_types):
            continue
        target['scope'] = [uri.normalize(target['source'])]


def _transform_old_style_comments(annotation):
    """
    Transform an old-style, targetless "comment" into one with a target.

    If this annotation has a URI, but no targets and no references, then it's
    an "old-style" comment or "page note". Detect this for old clients and
    rewrite the annotation target property.
    """
    def isempty(container, field):
        val = container.get(field)
        return val is None or val == []

    has_uri = annotation.get('uri') is not None
    has_no_targets = isempty(annotation, 'target')
    has_no_references = isempty(annotation, 'references')

    if has_uri and has_no_targets and has_no_references:
        annotation['target'] = [{'source': annotation.get('uri')}]
