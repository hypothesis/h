# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h import paginator
from h.i18n import TranslationString as _  # noqa: N813


@view_config(route_name='admin_features',
             request_method='GET',
             renderer='h:templates/admin/features.html.jinja2',
             permission='admin_features')
def features_index(request):

    features = sorted(models.Feature.all(request.db), key=lambda f: f.name)

    return {
        "features": features,
        "cohorts": request.db.query(models.FeatureCohort).all(),
    }


@view_config(route_name='admin_features',
             request_method='POST',
             permission='admin_features',
             require_csrf=True)
def features_save(request):
    for feat in models.Feature.all(request.db):
        for attr in ['everyone', 'admins', 'staff']:
            val = request.POST.get('{0}[{1}]'.format(feat.name, attr))
            if val == 'on':
                setattr(feat, attr, True)
            else:
                setattr(feat, attr, False)
        for cohort in request.db.query(models.FeatureCohort).all():
            val = request.POST.get('{0}[cohorts][{1}]'.format(feat.name, cohort.name))
            if val == 'on':
                if cohort not in feat.cohorts:
                    feat.cohorts.append(cohort)
            else:
                if cohort in feat.cohorts:
                    feat.cohorts.remove(cohort)

    request.session.flash(_("Changes saved."), "success")
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_features'))


@view_config(route_name='admin_cohorts',
             request_method='GET',
             renderer='h:templates/admin/cohorts.html.jinja2',
             permission='admin_features')
@paginator.paginate_query
def cohorts_index(context, request):
    query = request.db.query(models.FeatureCohort)
    return query.order_by(models.FeatureCohort.name)


@view_config(route_name='admin_cohorts',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/cohorts.html.jinja2',
             permission='admin_features',
             require_csrf=True)
def cohorts_add(request):
    """Create a new feature cohort."""
    cohort_name = request.params['add']
    cohort = models.FeatureCohort(name=cohort_name)
    request.db.add(cohort)

    url = request.route_url('admin_cohorts')
    return httpexceptions.HTTPSeeOther(url)


@view_config(route_name='admin_cohorts_edit',
             request_method='GET',
             renderer='h:templates/admin/edit_cohort.html.jinja2',
             permission='admin_features')
def cohorts_edit(context, request):
    id = request.matchdict['id']
    cohort = request.db.query(models.FeatureCohort).get(id)
    return {
        'cohort': cohort,
        'members': cohort.members,
        'default_authority': request.authority
    }


@view_config(route_name='admin_cohorts_edit',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/edit_cohort.html.jinja2',
             permission='admin_features',
             require_csrf=True)
def cohorts_edit_add(request):
    member_name = request.params['add'].strip()
    member_authority = request.params['authority'].strip()
    cohort_id = request.matchdict['id']

    member = models.User.get_by_username(request.db, member_name, member_authority)
    if member is None:
        request.session.flash(
            _("User {member_name} with authority {authority} doesn't exist.".format(
                member_name=member_name, authority=member_authority)),
            "error")
    else:
        cohort = request.db.query(models.FeatureCohort).get(cohort_id)
        cohort.members.append(member)

    url = request.route_url('admin_cohorts_edit', id=cohort_id)
    return httpexceptions.HTTPSeeOther(url)


@view_config(route_name='admin_cohorts_edit',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/edit_cohort.html.jinja2',
             permission='admin_features',
             require_csrf=True)
def cohorts_edit_remove(request):
    member_userid = request.params['remove']
    cohort_id = request.matchdict['id']

    cohort = request.db.query(models.FeatureCohort).get(cohort_id)
    member = request.db.query(models.User).filter_by(userid=member_userid).first()
    try:
        cohort.members.remove(member)
    except ValueError:
        request.session.flash(
            _("User {member_userid} doesn't exist.".format(member_userid=member_userid)),
            "error")

    url = request.route_url('admin_cohorts_edit', id=cohort_id)
    return httpexceptions.HTTPSeeOther(url)
