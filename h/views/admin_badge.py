# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config
from sqlalchemy.exc import IntegrityError

from h import models
from h.i18n import TranslationString as _  # noqa: N813


@view_config(route_name='admin_badge',
             request_method='GET',
             renderer='h:templates/admin/badge.html.jinja2',
             permission='admin_badge')
def badge_index(request):
    return {"uris": request.db.query(models.Blocklist).all()}


@view_config(route_name='admin_badge',
             request_method='POST',
             request_param='add',
             permission='admin_badge',
             require_csrf=True)
def badge_add(request):
    uri = request.params['add']
    item = models.Blocklist(uri=uri)
    request.db.add(item)

    # There's a uniqueness constraint on `uri`, so we flush the session,
    # catching any IntegrityError and responding appropriately.
    try:
        request.db.flush()
    except IntegrityError:
        request.db.rollback()
        msg = _("{uri} is already blocked.").format(uri=uri)
        request.session.flash(msg, 'error')

    index = request.route_path('admin_badge')
    return httpexceptions.HTTPSeeOther(location=index)


@view_config(route_name='admin_badge',
             request_method='POST',
             request_param='remove',
             permission='admin_badge',
             require_csrf=True)
def badge_remove(request):
    uri = request.params['remove']
    request.db.query(models.Blocklist).filter_by(uri=uri).delete()

    index = request.route_path('admin_badge')
    return httpexceptions.HTTPSeeOther(location=index)
