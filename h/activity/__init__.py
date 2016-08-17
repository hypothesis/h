# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.activity.views')

    config.add_route('activity.search', '/search')
    config.add_route('activity.group_search', '/groups/{pubid}/search')
    config.add_route('activity.user_search', '/users/{username}/search')
