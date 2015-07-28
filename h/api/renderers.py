# -*- coding: utf-8 -*-

"""Functions for presenting/rendering data in the API."""

import copy


def render_annotation(data):
    """
    Render an annotation retrieved from search for public display.

    Receives data direct from the search index and reformats it for rendering
    or display in the public API. At the moment all this does is remove
    normalised URI fields.
    """
    data = copy.deepcopy(data)

    _filter_target_normalised_uris(data)
    _filter_document_normalised_uris(data)

    return data


def _filter_target_normalised_uris(data):
    """Remove 'source_normalised' keys from targets, where present."""

    if 'target' not in data:
        return
    if not isinstance(data['target'], list):
        return
    for target in data['target']:
        if not isinstance(data, dict):
            continue
        if not 'source_normalised' in target:
            continue
        del target['source_normalised']


def _filter_document_normalised_uris(data):
    """Remove 'href_normalised' keys from targets, where present."""

    if 'document' not in data:
        return
    if not isinstance(data['document'], dict):
        return
    if 'link' not in data['document']:
        return
    if not isinstance(data['document']['link'], list):
        return
    for linkobj in data['document']['link']:
        if not isinstance(linkobj, dict):
            continue
        if not 'href_normalised' in linkobj:
            continue
        del linkobj['href_normalised']
