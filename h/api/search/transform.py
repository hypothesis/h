# -*- coding: utf-8 -*-

"""Functions for transforming data for or from the search index."""

import copy

from h.api import nipsa
from h.api import uri


def prepare(annotation):
    """
    Prepare the given annotation for indexing.

    Scan the passed annotation for any target URIs or document metadata URIs
    and add normalized versions of these to the document.
    """
    # FIXME: When this becomes simply part of a search indexing operation, this
    # should probably not mutate its argument.
    _normalize_annotation_target_uris(annotation)

    if 'user' in annotation and nipsa.has_nipsa(annotation['user']):
        annotation['nipsa'] = True


def render(annotation):
    """
    Render an annotation retrieved from search for public display.

    Receives data direct from the search index and reformats it for rendering
    or display in the public API.
    """
    data = copy.deepcopy(annotation)
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
        if not isinstance(target['source'], basestring):
            continue
        target['scope'] = [uri.normalize(target['source'])]
