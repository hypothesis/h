"""
Annotation storage API.

This module provides the core API with access to basic persistence functions
for storing and retrieving annotations. Data passed to these functions is
assumed to be validated.
"""

from pyramid import i18n

from h import models
from h.util.uri import normalize as normalize_uri

_ = i18n.TranslationStringFactory(__package__)


def expand_uri(session, uri, normalized=False):
    """
    Return all URIs which refer to the same underlying document as `uri`.

    This function determines whether we already have "document" records for the
    passed URI, and if so returns the set of all URIs which we currently
    believe refer to the same document.

    :param session: Database session
    :param uri: URI associated with the document
    :param normalized: Return normalized URIs instead of the raw value

    :returns: a list of equivalent URIs
    """

    normalized_uri = normalize_uri(uri)

    document_id = (
        session.query(models.DocumentURI.document_id)
        .filter(models.DocumentURI.uri_normalized == normalized_uri)
        .limit(1)
        .scalar_subquery()
    )

    type_uris = list(
        session.query(
            # Using the specific fields we want prevents object creation
            # which significantly speeds this method up (knocks ~40% off)
            models.DocumentURI.type,
            models.DocumentURI.uri,
            models.DocumentURI.uri_normalized,
        ).filter(models.DocumentURI.document_id == document_id)
    )

    if not type_uris:
        return [normalized_uri if normalized else uri]

    # We check if the match was a "canonical" link. If so, all annotations
    # created on that page are guaranteed to have that as their target.source
    # field, so we don't need to expand to other URIs and risk false positives.
    for doc_type, plain_uri, _ in type_uris:
        if doc_type == "rel-canonical" and plain_uri == uri:
            return [normalized_uri if normalized else uri]

    if normalized:
        return [uri_normalized for _, _, uri_normalized in type_uris]

    return [plain_uri for _, plain_uri, _ in type_uris]
