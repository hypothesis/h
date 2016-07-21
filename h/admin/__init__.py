# -*- coding: utf-8 -*-


def includeme(config):
    config.register_service_factory('.services.user.rename_user_factory', name='rename_user')

    config.include('.views')

    config.add_route('admin_index', '/')
    config.add_route('admin_admins', '/admins')
    config.add_route('admin_badge', '/badge')
    config.add_route('admin_features', '/features')
    config.add_route('admin_cohorts', '/features/cohorts')
    config.add_route('admin_cohorts_edit', '/features/cohorts/{id}')
    config.add_route('admin_groups', '/groups')
    config.add_route('admin_groups_csv', '/groups.csv')
    config.add_route('admin_nipsa', '/nipsa')
    config.add_route('admin_staff', '/staff')
    config.add_route('admin_users', '/users')
    config.add_route('admin_users_activate', '/users/activate')
    config.add_route('admin_users_delete', '/users/delete')
    config.add_route('admin_users_rename', '/users/rename')
