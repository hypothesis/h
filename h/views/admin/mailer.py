# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from h.emails import test
from h.tasks import mailer


@view_config(
    route_name="admin.mailer",
    request_method="GET",
    renderer="h:templates/admin/mailer.html.jinja2",
    permission="admin_mailer",
)
def mailer_index(request):
    """Show the mailer test tools."""
    return {"taskid": request.params.get("taskid")}


@view_config(
    route_name="admin.mailer_test",
    request_method="POST",
    permission="admin_mailer",
    require_csrf=True,
)
def mailer_test(request):
    """Send a test email."""
    if "recipient" not in request.params:
        index = request.route_path("admin.mailer")
        return HTTPSeeOther(location=index)

    mail = test.generate(request, request.params["recipient"])
    result = mailer.send.delay(*mail)
    index = request.route_path("admin.mailer", _query={"taskid": result.task_id})
    return HTTPSeeOther(location=index)
