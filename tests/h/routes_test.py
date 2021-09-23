from unittest.mock import Mock, call

from h.routes import includeme


def test_includeme():
    config = Mock(spec_set=["add_route"])

    includeme(config)

    # This may look like a ridiculous test, but the cost of keeping it
    # up-to-date is hopefully pretty low (run the tests with -vv, copy the new
    # expected value, strip out any Unicode prefixes) and it serves as a check
    # to ensure that any changes made to the routes were intended.
    calls = [
        call("index", "/"),
        call("robots", "/robots.txt"),
        call("via_redirect", "/via"),
        call("login", "/login"),
        call("logout", "/logout"),
        call("signup", "/signup"),
        call("activate", "/activate/{id}/{code}"),
        call("forgot_password", "/forgot-password"),
        call("account_reset", "/account/reset"),
        call("account_reset_with_code", "/account/reset/{code}"),
        call("account", "/account/settings"),
        call("account_profile", "/account/profile"),
        call("account_notifications", "/account/settings/notifications"),
        call("account_developer", "/account/developer"),
        call("claim_account_legacy", "/claim_account/{token}"),
        call("dismiss_sidebar_tutorial", "/app/dismiss_sidebar_tutorial"),
        call("activity.search", "/search"),
        call(
            "activity.user_search",
            "/users/{username}",
            factory="h.traversal.UserByNameRoot",
            traverse="/{username}",
        ),
        call("admin.index", "/admin/"),
        call("admin.admins", "/admin/admins"),
        call("admin.badge", "/admin/badge"),
        call("admin.features", "/admin/features"),
        call("admin.cohorts", "/admin/features/cohorts"),
        call("admin.cohorts_edit", "/admin/features/cohorts/{id}"),
        call("admin.groups", "/admin/groups"),
        call("admin.groups_create", "/admin/groups/new"),
        call(
            "admin.groups_delete",
            "/admin/groups/delete/{id}",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{id}",
        ),
        call(
            "admin.groups_edit",
            "/admin/groups/{id}",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{id}",
        ),
        call("admin.mailer", "/admin/mailer"),
        call("admin.mailer_test", "/admin/mailer/test"),
        call("admin.nipsa", "/admin/nipsa"),
        call("admin.oauthclients", "/admin/oauthclients"),
        call("admin.oauthclients_create", "/admin/oauthclients/new"),
        call("admin.oauthclients_edit", "/admin/oauthclients/{id}"),
        call("admin.organizations", "/admin/organizations"),
        call("admin.organizations_create", "/admin/organizations/new"),
        call(
            "admin.organizations_delete",
            "/admin/organizations/delete/{pubid}",
            factory="h.traversal.OrganizationRoot",
            traverse="/{pubid}",
        ),
        call(
            "admin.organizations_edit",
            "/admin/organizations/{pubid}",
            factory="h.traversal.OrganizationRoot",
            traverse="/{pubid}",
        ),
        call("admin.staff", "/admin/staff"),
        call("admin.users", "/admin/users"),
        call("admin.users_activate", "/admin/users/activate"),
        call("admin.users_delete", "/admin/users/delete"),
        call("admin.users_rename", "/admin/users/rename"),
        call("admin.search", "/admin/search"),
        call(
            "annotation",
            "/a/{id}",
            factory="h.traversal:AnnotationRoot",
            traverse="/{id}",
        ),
        call("stream", "/stream"),
        call("stream.user_query", "/u/{user}"),
        call("stream.tag_query", "/t/{tag}"),
        call("assets", "/assets/*subpath"),
        call("api.index", "/api/"),
        call("api.links", "/api/links"),
        call(
            "api.annotations", "/api/annotations", factory="h.traversal:AnnotationRoot"
        ),
        call(
            "api.annotation",
            "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}",
            factory="h.traversal:AnnotationRoot",
            traverse="/{id}",
        ),
        call(
            "api.annotation_flag",
            "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}/flag",
            factory="h.traversal:AnnotationRoot",
            traverse="/{id}",
        ),
        call(
            "api.annotation_hide",
            "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}/hide",
            factory="h.traversal:AnnotationRoot",
            traverse="/{id}",
        ),
        call(
            "api.annotation.jsonld",
            "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}.jsonld",
            factory="h.traversal:AnnotationRoot",
            traverse="/{id}",
        ),
        call("api.bulk", "/api/bulk", request_method="POST"),
        call("api.groups", "/api/groups", factory="h.traversal.GroupRoot"),
        call(
            "api.group_upsert",
            "/api/groups/{id}",
            request_method="PUT",
            factory="h.traversal.GroupRoot",
            traverse="/{id}",
        ),
        call(
            "api.group",
            "/api/groups/{id}",
            request_method=("GET", "PATCH"),
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{id}",
        ),
        call("api.profile", "/api/profile"),
        call("api.profile_groups", "/api/profile/groups"),
        call("api.debug_token", "/api/debug-token"),
        call(
            "api.group_members",
            "/api/groups/{pubid}/members",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{pubid}",
        ),
        call(
            "api.group_member",
            "/api/groups/{pubid}/members/{userid}",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{pubid}",
        ),
        call("api.search", "/api/search"),
        call("api.users", "/api/users", factory="h.traversal.UserRoot"),
        call(
            "api.user_read",
            "/api/users/{userid}",
            request_method="GET",
            factory="h.traversal.UserByIDRoot",
            traverse="/{userid}",
        ),
        call(
            "api.user",
            "/api/users/{username}",
            factory="h.traversal.UserByNameRoot",
            traverse="/{username}",
        ),
        call("badge", "/api/badge"),
        call("token", "/api/token"),
        call("oauth_authorize", "/oauth/authorize"),
        call("oauth_revoke", "/oauth/revoke"),
        call("sidebar_app", "/app.html"),
        call("notebook_app", "/notebook"),
        call("embed", "/embed.js"),
        call("stream_atom", "/stream.atom"),
        call("stream_rss", "/stream.rss"),
        call(
            "organization_logo",
            "/organizations/{pubid}/logo",
            factory="h.traversal.OrganizationRoot",
            traverse="/{pubid}",
        ),
        call("group_create", "/groups/new"),
        call(
            "group_edit",
            "/groups/{pubid}/edit",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{pubid}",
        ),
        call(
            "group_read",
            "/groups/{pubid}/{slug:[^/]*}",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{pubid}",
        ),
        call(
            "group_read_noslug",
            "/groups/{pubid}",
            factory="h.traversal.GroupRequiredRoot",
            traverse="/{pubid}",
        ),
        call("help", "/docs/help"),
        call("onboarding", "/welcome/"),
        call("custom_onboarding", "/welcome/{slug}"),
        call("unsubscribe", "/notification/unsubscribe/{token}"),
        call("status", "/_status"),
        call("about", "/about/", static=True),
        call("bioscience", "/bioscience/", static=True),
        call("blog", "/blog/", static=True),
        call(
            "chrome-extension",
            "https://chrome.google.com/webstore/detail/bjfhmglciegochdpefhhlphglcehbmek",
            static=True,
        ),
        call("contact", "/contact/", static=True),
        call("contribute", "/contribute/", static=True),
        call("education", "/education/", static=True),
        call("for-publishers", "/for-publishers/", static=True),
        call("fund", "/fund/", static=True),
        call("help-center", "/help/", static=True),
        call("hypothesis-github", "https://github.com/hypothesis", static=True),
        call("hypothesis-twitter", "https://twitter.com/hypothes_is", static=True),
        call("jobs", "/jobs/", static=True),
        call("press", "/press/", static=True),
        call("privacy", "/privacy/", static=True),
        call("roadmap", "/roadmap/", static=True),
        call("team", "/team/", static=True),
        call("terms-of-service", "/terms-of-service/", static=True),
        call(
            "wordpress-plugin", "https://wordpress.org/plugins/hypothesis/", static=True
        ),
    ]

    # Test each one one at a time to make it a bit easier to spot which one
    # isn't in the list
    for single_call in calls:
        assert single_call in config.add_route.mock_calls

    # Then we can assert the order here
    assert config.add_route.mock_calls == calls
