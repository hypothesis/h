# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock, call

from h.routes import includeme


def test_includeme():
    config = Mock(spec_set=['add_route'])

    includeme(config)

    # This may look like a ridiculous test, but the cost of keeping it
    # up-to-date is hopefully pretty low (run the tests with -vv, copy the new
    # expected value) and it serves as a check to ensure that any changes made
    # to the routes were intended.
    assert config.add_route.mock_calls == [
        call('index', '/'),
        call('robots', '/robots.txt'),
        call('via_redirect', '/via'),
        call('login', '/login'),
        call('logout', '/logout'),
        call('signup', '/signup'),
        call('activate', '/activate/{id}/{code}'),
        call('forgot_password', '/forgot-password'),
        call('account_reset', '/account/reset'),
        call('account_reset_with_code', '/account/reset/{code}'),
        call('account', '/account/settings'),
        call('account_profile', '/account/profile'),
        call('account_notifications', '/account/settings/notifications'),
        call('account_developer', '/account/developer'),
        call('claim_account_legacy', '/claim_account/{token}'),
        call('dismiss_sidebar_tutorial', '/app/dismiss_sidebar_tutorial'),
        call('activity.search', '/search'),
        call('activity.group_search', '/groups/{pubid}/search'),
        call('activity.user_search', '/users/{username}'),
        call('admin_index', '/admin/'),
        call('admin_admins', '/admin/admins'),
        call('admin_badge', '/admin/badge'),
        call('admin_features', '/admin/features'),
        call('admin_cohorts', '/admin/features/cohorts'),
        call('admin_cohorts_edit', '/admin/features/cohorts/{id}'),
        call('admin_groups', '/admin/groups'),
        call('admin_groups_csv', '/admin/groups.csv'),
        call('admin_nipsa', '/admin/nipsa'),
        call('admin_staff', '/admin/staff'),
        call('admin_users', '/admin/users'),
        call('admin_users_activate', '/admin/users/activate'),
        call('admin_users_delete', '/admin/users/delete'),
        call('admin_users_rename', '/admin/users/rename'),
        call('annotation', '/a/{id}', factory='memex.resources:AnnotationFactory', traverse='/{id}'),
        call('stream', '/stream'),
        call('stream.user_query', '/u/{user}'),
        call('stream.tag_query', '/t/{tag}'),
        call('assets_client', '/assets/client/*subpath'),
        call('assets', '/assets/*subpath'),
        call('badge', '/api/badge'),
        call('token', '/api/token'),
        call('api.users', '/api/users'),
        call('session', '/app'),
        call('widget', '/app.html'),
        call('embed', '/embed.js'),
        call('stream_atom', '/stream.atom'),
        call('stream_rss', '/stream.rss'),
        call('group_create', '/groups/new'),
        call('group_edit', '/groups/{pubid}/edit', factory='h.models.group:GroupFactory', traverse='/{pubid}'),
        call('group_leave', '/groups/{pubid}/leave', factory='h.models.group:GroupFactory', traverse='/{pubid}'),
        call('group_read', '/groups/{pubid}/{slug:[^/]*}', factory='h.models.group:GroupFactory', traverse='/{pubid}'),
        call('group_read_noslug', '/groups/{pubid}', factory='h.models.group:GroupFactory', traverse='/{pubid}'),
        call('help', '/docs/help'),
        call('onboarding', '/welcome/'),
        call('custom_onboarding', '/welcome/{slug}'),
        call('unsubscribe', '/notification/unsubscribe/{token}'),
    ]
