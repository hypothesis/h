import logging

from pyramid.httpexceptions import HTTPInternalServerError

from h.util.view import json_view

log = logging.getLogger(__name__)


@json_view(route_name="status", http_cache=0)
def status(request):
    try:
        request.db.execute("SELECT 1")
    except Exception as err:
        log.exception(err)
        raise HTTPInternalServerError("Database connection failed") from err
    return {"status": "okay"}
