# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid import session
from pyramid.view import view_config

from h import models
from h import paginator
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


@view_config(route_name='admin_cohorts',
             request_method='GET',
             renderer='h:templates/admin/cohorts.html.jinja2',
             permission='admin_features')
@paginator.paginate
def cohorts_index(context, request):
    query = request.db.query(models.FeatureCohort)
    return query.order_by(models.FeatureCohort.name)


@view_config(route_name='admin_cohorts',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/cohorts.html.jinja2',
             permission='admin_features')
def cohorts_add(request):
    """Create a new feature cohort."""
    cohort_name = request.params['add']
    cohort = models.FeatureCohort(name=cohort_name)
    request.db.add(cohort)

    url = request.route_url('admin_cohorts')
    return httpexceptions.HTTPSeeOther(url)


@view_config(route_name='admin_edit_cohort',
             request_method='GET',
             renderer='h:templates/admin/edit_cohort.html.jinja2',
             permission='admin_features')
def cohorts_edit(context, request):
    id = request.matchdict['id']
    cohort = request.db.query(models.FeatureCohort).get(id)
    return {'cohort': cohort, 'members': cohort.members}


@view_config(route_name='admin_edit_cohort',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/edit_cohort.html.jinja2',
             permission='admin_features')
def cohorts_edit_add(request):
    member_name = request.params['add']
    cohort_id = request.matchdict['id']

    member = models.User.get_by_username(member_name)
    if member is None:
        request.session.flash(
            _("User {member_name} doesn't exist.".format(member_name=member_name)),
            "error")
    else:
        cohort = request.db.query(models.FeatureCohort).get(cohort_id)
        cohort.members.append(member)

    url = request.route_url('admin_edit_cohort', id=cohort_id)
    return httpexceptions.HTTPSeeOther(url)


@view_config(route_name='admin_edit_cohort',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/edit_cohort.html.jinja2',
             permission='admin_features')
def cohorts_edit_remove(request):
    member_name = request.params['remove']
    cohort_id = request.matchdict['id']

    cohort = request.db.query(models.FeatureCohort).get(cohort_id)
    member = request.db.query(models.User).filter_by(uid=member_name).first()
    cohort.members.remove(member)

    url = request.route_url('admin_edit_cohort', id=cohort_id)
    return httpexceptions.HTTPSeeOther(url)


def includeme(config):
    config.scan(__name__)
