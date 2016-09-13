"""
Functions for parsing document claims data from the client.

Functions for parsing the document claims (document metadata claims and URI
equivalence claims) that the client POSTS in the JSON "document" sub-object in
annotation create and update requests.

The data is parsed into a format suitable for storage in our database model,
and returned.

"""
from __future__ import unicode_literals


def document_uris_from_data(document_data, claimant):
    """
    Return one or more document URI dicts for the given document data.

    Returns one document uri dict for each document equivalence claim in
    document_data.

    Each dict can be used to init a DocumentURI object directly:

        document_uri = DocumentURI(**document_uri_dict)

    Always returns at least one "self-claim" document URI whose URI is the
    claimant URI itself.

    :param document_data: the "document" sub-object that was POSTed to the API
        as part of a new or updated annotation
    :type document_data: dict

    :param claimant: the URI that the browser was at when this annotation was
        created (the top-level "uri" field of the annotation)
    :type claimant: unicode

    :returns: a list of one or more document URI dicts
    :rtype: list of dicts

    """
    document_uris = document_uris_from_links(document_data.get('link', []),
                                             claimant)

    document_uris.extend(
        document_uris_from_highwire_pdf(document_data.get('highwire', {}),
                                        claimant)
    )

    document_uris.extend(
        document_uris_from_highwire_doi(document_data.get('highwire', {}),
                                        claimant)
    )

    document_uris.extend(
        document_uris_from_dc(document_data.get('dc', {}),
                              claimant)
    )

    document_uris.append(document_uri_self_claim(claimant))

    return document_uris


def document_metas_from_data(document_data, claimant):
    """
    Return a list of document meta dicts for the given document data.

    Returns one document meta dict for each document metadata claim in
    document_data.

    Each dict can be used to init a DocumentMeta object directly:

        document_meta = DocumentMeta(**document_meta_dict)

    :param document_data: the "document" sub-object that the client POSTed to
        the API as part of a new or updated annotation
    :type document_data: dict

    :param claimant: the URI that the browser was at when this annotation was
        created (the top-level "uri" field of the annotation)
    :type claimant: unicode

    :returns: a list of zero or more document meta dicts
    :rtype: list of dicts

    """
    def transform_meta_(document_meta_dicts, items, path_prefix=None):
        """Fill document_meta_dicts with document meta dicts for the items."""
        if path_prefix is None:
            path_prefix = []

        for key, value in items.iteritems():
            keypath = path_prefix[:]
            keypath.append(key)

            if isinstance(value, dict):
                transform_meta_(document_meta_dicts,
                                value,
                                path_prefix=keypath)
            else:
                if not isinstance(value, list):
                    value = [value]

                value = [v.strip() for v in value]

                document_meta_dicts.append({
                    'type': '.'.join(keypath),
                    'value': value,
                    'claimant': claimant,
                })

    items = {k: v for k, v in document_data.iteritems() if k != 'link'}
    document_meta_dicts = []
    transform_meta_(document_meta_dicts, items)
    return document_meta_dicts


def document_uris_from_links(link_dicts, claimant):
    """
    Return document URI dicts for the given document.link data.

    Process a document.link list of dicts that the client submitted as part of
    an annotation create or update request and return document URI dicts for
    all of the document equivalence claims that it makes.

    """
    document_uris = []
    for link in link_dicts:

        # Disregard self-claim URLs as they're added separately later.
        if link.keys() == ['href'] and link['href'] == claimant:
            continue

        # Disregard doi links as these are being added separately from the
        # highwire and dc metadata later on.
        if link.keys() == ['href'] and link['href'].startswith('doi:'):
            continue

        # Disregard Highwire PDF links as these are being added separately from
        # the highwire metadata later on.
        if set(link.keys()) == set(['href', 'type']):
            if link['type'] == 'application/pdf':
                continue

        uri_ = link['href']

        # Handle rel="..." links.
        if 'rel' in link:
            type_ = 'rel-{}'.format(link['rel'])
        else:
            type_ = ''

        # The "type" item in link dicts becomes content_type in DocumentURIs.
        content_type = link.get('type', '')

        document_uris.append({
            'claimant': claimant,
            'uri': uri_,
            'type': type_,
            'content_type': content_type,
        })

    return document_uris


def document_uris_from_highwire_pdf(highwire_dict, claimant):
    """
    Return PDF document URI dicts for the given 'highwire' document metadata.

    Process a document.highwire dict that the client submitted as part of an
    annotation create or update request and return document URI dicts for all
    of the PDF document equivalence claims that it makes.

    """
    document_uris = []
    hwpdfvalues = highwire_dict.get('pdf_url', [])
    for pdf in hwpdfvalues:
        document_uris.append({'claimant': claimant,
                              'uri': pdf,
                              'type': 'highwire-pdf',
                              'content_type': 'application/pdf'})
    return document_uris


def document_uris_from_highwire_doi(highwire_dict, claimant):
    """
    Return DOI document URI dicts for the given 'highwire' document metadata.

    Process a document.highwire dict that the client submitted as part of an
    annotation create or update request and return document URI dicts for all
    of the 'doi:' document equivalence claims that it makes.

    """
    document_uris = []
    hwdoivalues = highwire_dict.get('doi', [])
    for doi in hwdoivalues:
        if not doi.startswith('doi:'):
            doi = "doi:{}".format(doi)

        document_uris.append({'claimant': claimant,
                              'uri': doi,
                              'type': 'highwire-doi',
                              'content_type': ''})
    return document_uris


def document_uris_from_dc(dc_dict, claimant):
    """
    Return document URI dicts for the given 'dc' document metadata.

    Process a document.dc dict that the client submitted as part of an
    annotation create or update request and return document URI dicts for all
    of the document equivalence claims that it makes.

    """
    document_uris = []
    dcdoivalues = dc_dict.get('identifier', [])
    for doi in dcdoivalues:
        if not doi.startswith('doi:'):
            doi = "doi:{}".format(doi)

        document_uris.append({'claimant': claimant,
                              'uri': doi,
                              'type': 'dc-doi',
                              'content_type': ''})

    return document_uris


def document_uri_self_claim(claimant):
    """Return a "self-claim" document URI dict for the given claimant."""
    return {
        'claimant': claimant,
        'uri': claimant,
        'type': u'self-claim',
        'content_type': '',
    }
