# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    # Core
    config.add_route('index', '/')
    config.add_route('robots', '/robots.txt')
    config.add_route('via_redirect', '/via')

    # Accounts
    config.add_route('logout', '/session/logout')
    config.add_route('login', '/deprecated/login')
    config.add_route('signup', '/deprecated/signup')
    config.add_route('assigntoken', '/session/assigntoken')
    
    config.add_route('logingoogle', '/login/google')
    config.add_route('stream_login', '/login')
    config.add_route('stream_logout', '/logout')
    config.add_route('activate', '/activate/{id}/{code}')
    config.add_route('forgot_password', '/forgot-password')
    config.add_route('account_reset', '/account/reset')
    config.add_route('account_reset_with_code', '/account/reset/{code}')
    config.add_route('account', '/account/settings')
    config.add_route('account_profile', '/account/profile')
    config.add_route('account_notifications', '/account/settings/notifications')
    config.add_route('account_developer', '/account/developer')
    config.add_route('claim_account_legacy', '/claim_account/{token}')
    config.add_route('dismiss_sidebar_tutorial', '/app/dismiss_sidebar_tutorial')

    # Activity
    config.add_route('activity.search', '/search')
    config.add_route('activity.group_search', '/groups/{pubid}/search')
    config.add_route('activity.user_search', '/users/{username}/search')

    # Admin
    config.add_route('admin_index', '/admin/')
    config.add_route('admin_admins', '/admin/admins')
    config.add_route('admin_badge', '/admin/badge')
    config.add_route('admin_features', '/admin/features')
    config.add_route('admin_cohorts', '/admin/features/cohorts')
    config.add_route('admin_cohorts_edit', '/admin/features/cohorts/{id}')
    config.add_route('admin_groups', '/admin/groups')
    config.add_route('admin_groups_csv', '/admin/groups.csv')
    config.add_route('admin_nipsa', '/admin/nipsa')
    config.add_route('admin_staff', '/admin/staff')
    config.add_route('admin_users', '/admin/users')
    config.add_route('admin_users_activate', '/admin/users/activate')
    config.add_route('admin_users_delete', '/admin/users/delete')
    config.add_route('admin_users_rename', '/admin/users/rename')

    # Annotations & stream
    config.add_route('annotation',
                     '/a/{id}',
                     factory='memex.resources:AnnotationFactory',
                     traverse='/{id}')
    config.add_route('stream', '/stream')
    config.add_route('stream.user_query', '/u/{user}')
    config.add_route('stream.tag_query', '/t/{tag}')

    # Assets
    config.add_route('assets_client', '/assets/client/*subpath')
    config.add_route('assets', '/assets/*subpath')

    # API (other than those provided by memex)
    config.add_route('badge', '/api/badge')
    config.add_route('token', '/api/token')
    config.add_route('api.users', '/api/users')

    # Client
    config.add_route('session', '/app')
    config.add_route('widget', '/app.html')
    config.add_route('embed', '/embed.js')

    # Feeds
    config.add_route('stream_atom', '/stream.atom')
    config.add_route('stream_rss', '/stream.rss')

    # Groups
    config.add_route('group_create', '/groups/new')
    config.add_route('group_edit',
                     '/groups/{pubid}/edit',
                     factory='h.models.group:GroupFactory',
                     traverse='/{pubid}')
    config.add_route('group_leave',
                     '/groups/{pubid}/leave',
                     factory='h.models.group:GroupFactory',
                     traverse='/{pubid}')
    # Match "/<pubid>/": we redirect to the version with the slug.
    config.add_route('group_read',
                     '/groups/{pubid}/{slug:[^/]*}',
                     factory='h.models.group:GroupFactory',
                     traverse='/{pubid}')
    config.add_route('group_read_noslug',
                     '/groups/{pubid}',
                     factory='h.models.group:GroupFactory',
                     traverse='/{pubid}')

    # Help
    config.add_route('help', '/docs/help')
    config.add_route('onboarding', '/welcome/')
    config.add_route('custom_onboarding', '/welcome/{slug}')

    # Notification
    config.add_route('unsubscribe', '/notification/unsubscribe/{token}')
