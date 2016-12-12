# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Group
from h.models.group import WriteableBy


def annotation_group_write_permitted(request, groupid):
    if groupid == '__world__':
        principal = 'authority:%s' % request.auth_domain
        return (principal in request.effective_principals)

    group = _fetch_group(request.db, groupid)

    if group is None or group.writeable_by is None:
        return False

    if group.writeable_by == WriteableBy.authority:
        principal = 'authority:%s' % group.authority
        return (principal in request.effective_principals)

    if group.writeable_by == WriteableBy.members:
        principal = 'group:%s' % groupid
        return (principal in request.effective_principals)

    return False


def _fetch_group(session, groupid):
    # Ideally this will be moved into the GroupService with a caching layer,
    # similar to the UserService.fetch
    return session.query(Group).filter_by(pubid=groupid).one_or_none()
