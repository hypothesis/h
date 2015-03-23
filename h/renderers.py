from . import atom_feed


class AnnotationsAtomRendererFactory(object):

    """A Pyramid renderer that renders list of annotations as Atom feeds.

    Usage:

        @view_config(renderer='annotations_atom')
        def my_view(request):
            ...
            return dict(
                # A list of annotation dicts, these will be used as the Atom
                # feed entries.
                annotations=annotations,

                # The URL where the Atom feed will be hosted.
                atom_url="http://hypothes.is/stream.atom",

                # The URL for the HTML page the feed is a feed of (optional).
                html_url=html_url,

                # The title of the feed (optional).
                title=title,

                # The subtitle for the feed (optional).
                subtitle=subtitle)

    """

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        system["request"].response.content_type = "application/atom+xml"
        return atom_feed.render_annotations(request=system["request"], **value)


def includeme(config):
    config.add_renderer(
        name="annotations_atom",
        factory="h.renderers.AnnotationsAtomRendererFactory")
