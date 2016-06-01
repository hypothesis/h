# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid import httpexceptions as exc

from h import models
from h import paginator


@view_config(route_name='admin_cohorts',
             request_method='GET',
             renderer='h:templates/admin/cohorts.html.jinja2',
             permission='admin_features')
@paginator.paginate
def cohorts_index(context, request):
    return models.FeatureCohort.query.order_by(models.FeatureCohort.created.desc())


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
    request.db.flush()
    url = request.route_url('admin_cohorts')
    return exc.HTTPSeeOther(url)


def includeme(config):
    config.scan(__name__)
