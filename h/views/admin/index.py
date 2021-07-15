import platform

from pyramid.view import view_config

from h import __version__
from h.security.permissions import Permission


@view_config(
    route_name="admin.index",
    request_method="GET",
    renderer="h:templates/admin/index.html.jinja2",
    permission=Permission.ADMINPAGE_INDEX,
)
def index(_):
    return {
        "release_info": {
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "version": __version__,
        }
    }
