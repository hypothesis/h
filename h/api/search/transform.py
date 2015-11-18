# -*- coding: utf-8 -*-

"""Functions for transforming data for or from the search index."""

import copy

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

    _copy_parent_scopes_into_replies(annotation)

    if 'user' in annotation and nipsa.has_nipsa(annotation['user']):
        annotation['nipsa'] = True


def render(annotation):
    """
    Render an annotation retrieved from search for public display.

    Receives data direct from the search index and reformats it for rendering
    or display in the public API.
    """
    data = copy.deepcopy(dict(annotation))
    return data


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


def _copy_parent_scopes_into_replies(annotation):
    """If this annotation is a reply then copy its parents scopes into it.

    If the given annotation is a reply then we find the thread root
    annotation and copy its targets into the reply, _but_ we only
    copy the 'scope' key from each target and not the rest of the dict.
    """
    references = annotation.get('references')

    if not references:
        return  # This annotation is not a reply.

    parent = models.Annotation.fetch(references[0])

    if not parent:
        return  # Nothing can be done.

    targets = parent.get('target', [])
    if not isinstance(targets, list):
        return

    # Deliberately overwrite any existing target in the reply annotation.
    annotation['target'] = [{'scope': target['scope']} for target in targets
                            if isinstance(target, dict) and 'scope' in target]
