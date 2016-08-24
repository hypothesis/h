# -*- coding: utf-8 -*-


def includeme(config):
    config.register_service_factory('.services.groups_factory', name='groups')

    config.include('.views')

    config.add_route('group_create', '/new')

    config.add_route('group_edit',
                     '/{pubid}/edit',
                     factory='h.groups.models:GroupFactory',
                     traverse='/{pubid}')

    config.add_route('group_leave',
                     '/{pubid}/leave',
                     factory='h.groups.models:GroupFactory',
                     traverse='/{pubid}')

    # Match "/<pubid>/": we redirect to the version with the slug.
    config.add_route('group_read',
                     '/{pubid}/{slug:[^/]*}',
                     factory='h.groups.models:GroupFactory',
                     traverse='/{pubid}')
    config.add_route('group_read_noslug',
                     '/{pubid}',
                     factory='h.groups.models:GroupFactory',
                     traverse='/{pubid}')
