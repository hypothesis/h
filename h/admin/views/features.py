# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid import session
from pyramid.view import view_config

from h import models
from h.i18n import TranslationString as _


@view_config(route_name='admin_features',
             request_method='GET',
             renderer='h:templates/admin/features.html.jinja2',
             permission='admin_features')
def features_index(_):
    return {"features": models.Feature.all()}


@view_config(route_name='admin_features',
             request_method='POST',
             permission='admin_features')
def features_save(request):
    session.check_csrf_token(request)
    for feat in models.Feature.all():
        for attr in ['everyone', 'admins', 'staff']:
            val = request.POST.get('{0}[{1}]'.format(feat.name, attr))
            if val == 'on':
                setattr(feat, attr, True)
            else:
                setattr(feat, attr, False)
    request.session.flash(_("Changes saved."), "success")
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_features'))


def includeme(config):
    config.scan(__name__)
