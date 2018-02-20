# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.group_json import GroupJSONPresenter, GroupsJSONPresenter


class GroupJSONPresentationService(object):
    def __init__(self, session, request_authority, route_url):
        self._session = session
        self._request_authority = request_authority
        self._route_url = route_url

    def present(self, group):
        presenter = GroupJSONPresenter(group, self.get_links)
        return presenter.asdict()

    def present_all(self, groups):
        presenter = GroupsJSONPresenter(groups, self.get_links)
        return presenter.asdicts()

    def get_links(self, group):
        links = {}
        if group.authority == self._request_authority:
            links['group'] = self._route_url('group_read',
                                             pubid=group.pubid,
                                             slug=group.slug)
        return links


def group_json_presentation_service_factory(context, request):
    return GroupJSONPresentationService(session=request.db,
                                        request_authority=request.authority,
                                        route_url=request.route_url)
