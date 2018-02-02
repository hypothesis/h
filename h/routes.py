# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    # Core
    config.add_route('index', '/')
    config.add_route('robots', '/robots.txt')
    config.add_route('via_redirect', '/via')

    # Accounts
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('signup', '/signup')
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
    config.add_route('activity.user_search',
                     '/users/{username}',
                     factory='h.models.user:UserFactory',
                     traverse='/{username}')

    # Admin
    config.add_route('admin_index', '/admin/')
    config.add_route('admin_admins', '/admin/admins')
    config.add_route('admin_badge', '/admin/badge')
    config.add_route('admin_features', '/admin/features')
    config.add_route('admin_cohorts', '/admin/features/cohorts')
    config.add_route('admin_cohorts_edit', '/admin/features/cohorts/{id}')
    config.add_route('admin_groups', '/admin/groups')
    config.add_route('admin_mailer', '/admin/mailer')
    config.add_route('admin_mailer_test', '/admin/mailer/test')
    config.add_route('admin_nipsa', '/admin/nipsa')
    config.add_route('admin_oauthclients', '/admin/oauthclients')
    config.add_route('admin_oauthclients_create', '/admin/oauthclients/new')
    config.add_route('admin_oauthclients_edit',
                     '/admin/oauthclients/{id}',
                     factory='h.resources.AuthClientFactory',
                     traverse='/{id}')
    config.add_route('admin_staff', '/admin/staff')
    config.add_route('admin_users', '/admin/users')
    config.add_route('admin_users_activate', '/admin/users/activate')
    config.add_route('admin_users_delete', '/admin/users/delete')
    config.add_route('admin_users_rename', '/admin/users/rename')

    # Annotations & stream
    config.add_route('annotation',
                     '/a/{id}',
                     factory='h.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('stream', '/stream')
    config.add_route('stream.user_query', '/u/{user}')
    config.add_route('stream.tag_query', '/t/{tag}')

    # Assets
    config.add_route('assets', '/assets/*subpath')

    # API

    # For historical reasons, the `api` route ends with a trailing slash. This
    # is not (or should not) be necessary, but for now the client will
    # construct URLs incorrectly if its `apiUrl` setting does not end in a
    # trailing slash.
    #
    # Any new parameter names will require a corresponding change to the link
    # template generator in `h/views/api.py`
    config.add_route('api.index', '/api/')
    config.add_route('api.links', '/api/links')
    config.add_route('api.annotations', '/api/annotations')
    config.add_route('api.annotation',
                     '/api/annotations/{id:[A-Za-z0-9_-]{20,22}}',
                     factory='h.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('api.annotation_flag',
                     '/api/annotations/{id:[A-Za-z0-9_-]{20,22}}/flag',
                     factory='h.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('api.annotation_hide',
                     '/api/annotations/{id:[A-Za-z0-9_-]{20,22}}/hide',
                     factory='h.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('api.annotation.jsonld',
                     '/api/annotations/{id:[A-Za-z0-9_-]{20,22}}.jsonld',
                     factory='h.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('api.profile', '/api/profile')
    config.add_route('api.debug_token', '/api/debug-token')
    config.add_route('api.group_member',
                     '/api/groups/{pubid}/members/{user}',
                     factory='h.models.group:GroupFactory',
                     traverse='/{pubid}')
    config.add_route('api.search', '/api/search')
    config.add_route('api.users', '/api/users')
    config.add_route('api.user', '/api/users/{username}')
    config.add_route('badge', '/api/badge')
    config.add_route('token', '/api/token')
    config.add_route('oauth_authorize', '/oauth/authorize')
    config.add_route('oauth_revoke', '/oauth/revoke')

    # Client
    config.add_route('sidebar_app', '/app.html')
    config.add_route('embed', '/embed.js')

    # Feeds
    config.add_route('stream_atom', '/stream.atom')
    config.add_route('stream_rss', '/stream.rss')

    # Groups
    config.add_route('api.groups', '/api/groups')
    config.add_route('group_create', '/groups/new')
    config.add_route('group_edit',
                     '/groups/{pubid}/edit',
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

    # Health check
    config.add_route('status', '/_status')

    # Static
    config.add_route('about', '/about/', static=True)
    config.add_route('bioscience', '/bioscience/', static=True)
    config.add_route('blog', '/blog/', static=True)
    config.add_route(
        'chrome-extension',
        'https://chrome.google.com/webstore/detail/bjfhmglciegochdpefhhlphglcehbmek',
        static=True)
    config.add_route('contact', '/contact/', static=True)
    config.add_route('contribute', '/contribute/', static=True)
    config.add_route('education', '/education/', static=True)
    config.add_route('for-publishers', '/for-publishers/', static=True)
    config.add_route('fund', '/fund/', static=True)
    config.add_route(
        'help-center', 'https://hypothesis.zendesk.com/hc/en-us', static=True)
    config.add_route(
        'hypothesis-github', 'https://github.com/hypothesis', static=True)
    config.add_route(
        'hypothesis-twitter', 'https://twitter.com/hypothes_is', static=True)
    config.add_route('jobs', '/jobs/', static=True)
    config.add_route('press', '/press/', static=True)
    config.add_route('privacy', '/privacy/', static=True)
    config.add_route('roadmap', '/roadmap/', static=True)
    config.add_route('team', '/team/', static=True)
    config.add_route('terms-of-service', '/terms-of-service/', static=True)
    config.add_route(
        'wordpress-plugin', 'https://wordpress.org/plugins/hypothesis/',
        static=True)
