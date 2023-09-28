from pyramid import renderers

from h.feeds import atom, rss


def render_atom(  # pylint:disable=too-many-arguments
    request, annotations, atom_url, html_url, title, subtitle
):
    """
    Return a rendered Atom feed of the given annotations.

    :param annotations: The list of annotations to render as the feed's entries
    :type annotations: list of dicts

    :param atom_url: The URL that this Atom feed will be served at
    :type atom_url: string

    :param html_url: The URL of the HTML page that this Atom feed is a feed of
    :type html_url: string

    :param title: The title of this Atom feed
    :type title: unicode

    :param subtitle: The subtitle of this Atom feed
    :type subtitle: unicode

    :rtype: pyramid.response.Response

    """

    def annotation_url(annotation):  # pragma: no cover
        """Return the HTML permalink URL for the given annotation."""
        return request.route_url("annotation", id=annotation.id)

    def annotation_api_url(annotation):  # pragma: no cover
        """Return the JSON API URL for the given annotation."""
        return request.route_url("api.annotation", id=annotation.id)

    feed = atom.feed_from_annotations(
        annotations=annotations,
        atom_url=atom_url,
        annotation_url=annotation_url,
        annotation_api_url=annotation_api_url,
        html_url=html_url,
        title=title,
        subtitle=subtitle,
    )

    response = renderers.render_to_response(
        "h:templates/atom.xml.jinja2", {"feed": feed}, request=request
    )
    response.content_type = "application/atom+xml"
    return response


def render_rss(  # pylint:disable=too-many-arguments
    request, annotations, rss_url, html_url, title, description
):
    """
    Return a rendered RSS feed of the given annotations.

    :param annotations: The list of annotations to render as the feed's items
    :type annotations: list of dicts

    :param rss_url: The URL that this RSS feed will be served at
    :type rss_url: string

    :param html_url: The URL of the HTML page that this RSS feed is a feed of
    :type html_url: string

    :param title: The title of this RSS feed
    :type title: unicode

    :param description: The description of this RSS feed
    :type description: unicode

    :rtype: pyramid.response.Response

    """

    def annotation_url(annotation):  # pragma: no cover
        """Return the HTML permalink URL for the given annotation."""
        return request.route_url("annotation", id=annotation.id)

    feed = rss.feed_from_annotations(
        annotations=annotations,
        annotation_url=annotation_url,
        rss_url=rss_url,
        html_url=html_url,
        title=title,
        description=description,
    )

    response = renderers.render_to_response(
        "h:templates/rss.xml.jinja2", {"feed": feed}, request=request
    )
    response.content_type = "application/rss+xml"
    return response
