import pyramid.renderers

json_sorted_factory = pyramid.renderers.JSON(sort_keys=True)


class SVGRenderer:
    """
    A renderer for SVG image files.

    A view callable can use this renderer and just return a string of SVG
    (u"<svg> ... </svg>") for the body of the response::

        @view_config(renderer="svg", ...)
        def my_svg_image_view(request):
            ...
            return u"<svg> ... </svg>"

    The response will be rendered as an SVG image response with the correct
    Content-Type etc so that browsers will render the image.

    """

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        response = system["request"].response
        response.content_type = "image/svg+xml"

        # Add a Vary: Accept-Encoding header.
        # This prevents caches from serving a cached, compressed version of the
        # file to user agents that don't support compression, or vice-versa.
        if response.vary:
            if "Accept-Encoding" not in response.vary:
                response.vary = response.vary + ("Accept-Encoding",)
        else:
            response.vary = ("Accept-Encoding",)

        return value


def includeme(config):  # pragma: no cover
    config.add_renderer(name="json_sorted", factory=json_sorted_factory)
    config.add_renderer(name="svg", factory=SVGRenderer)
