import logging

from pyramid.httpexceptions import HTTPInternalServerError
from sentry_sdk import capture_message
from sqlalchemy import text

from h.util.view import json_view

log = logging.getLogger(__name__)


@json_view(route_name="status", http_cache=0)
def status(request):
    try:
        request.db.execute(text("SELECT 1"))
    except Exception as err:
        log.exception(err)
        raise HTTPInternalServerError("Database connection failed") from err

    if "replica" in request.params:
        try:
            request.db_replica.execute(text("SELECT 1"))
        except Exception as err:
            log.exception(err)
            raise HTTPInternalServerError("Replica database connection failed") from err

    if "sentry" in request.params:
        capture_message("Test message from h's status view")

    return {"status": "okay"}
