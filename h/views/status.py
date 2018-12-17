# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from pyramid.httpexceptions import HTTPInternalServerError

from h.util.view import json_view


log = logging.getLogger(__name__)


@json_view(route_name="status")
def status(request):
    try:
        request.db.execute("SELECT 1")
    except Exception as exc:
        log.exception(exc)
        raise HTTPInternalServerError("Database connection failed")
    return {"status": "okay"}
