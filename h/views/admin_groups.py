# -*- coding: utf-8 -*-

from pyramid.view import view_config

from h import models
from h import paginator


@view_config(route_name='admin_groups',
             request_method='GET',
             renderer='h:templates/admin/groups.html.jinja2',
             permission='admin_groups')
@paginator.paginate_query
def groups_index(context, request):
    return request.db.query(models.Group).order_by(models.Group.created.desc())


@view_config(route_name='admin_groups_csv',
             request_method='GET',
             renderer='csv',
             permission='admin_groups')
def groups_index_csv(request):
    groups = request.db.query(models.Group)

    header = ['Group name', 'Group URL', 'Creator username',
              'Creator email', 'Number of members']
    rows = []
    for group in groups:
        creator_name = None
        creator_email = None
        if group.creator:
            creator_name = group.creator.username
            creator_email = group.creator.email

        rows.append([
             request.route_url('group_read',
                               pubid=group.pubid,
                               slug=group.slug),
             creator_name,
             creator_email,
             len(group.members)])

    filename = 'groups.csv'
    request.response.content_disposition = 'attachment;filename=' + filename

    return {'header': header, 'rows': rows}
