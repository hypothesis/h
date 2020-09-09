"""Routes registered when the kill switch is enabled."""
from pyramid.response import Response
from pyramid.view import notfound_view_config


@notfound_view_config()
def not_found(_exc, _request):
    """Handle any request we get with the shortest possible response."""
    return Response(status="429 Offline", headerlist=[])


def includeme(config):
    config.scan(__name__)
