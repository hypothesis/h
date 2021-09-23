def includeme(config):  # pylint: disable=too-many-statements
    # Core
    config.add_route("index", "/")
    config.add_route("robots", "/robots.txt")
    config.add_route("via_redirect", "/via")

    # Accounts
    config.add_route("login", "/login")
    config.add_route("logout", "/logout")
    config.add_route("signup", "/signup")
    config.add_route("activate", "/activate/{id}/{code}")
    config.add_route("forgot_password", "/forgot-password")
    config.add_route("account_reset", "/account/reset")
    config.add_route("account_reset_with_code", "/account/reset/{code}")
    config.add_route("account", "/account/settings")
    config.add_route("account_profile", "/account/profile")
    config.add_route("account_notifications", "/account/settings/notifications")
    config.add_route("account_developer", "/account/developer")
    config.add_route("claim_account_legacy", "/claim_account/{token}")
    config.add_route("dismiss_sidebar_tutorial", "/app/dismiss_sidebar_tutorial")

    # Activity
    config.add_route("activity.search", "/search")
    config.add_route(
        "activity.user_search",
        "/users/{username}",
        factory="h.traversal.UserByNameRoot",
        traverse="/{username}",
    )

    # Admin
    config.add_route("admin.index", "/admin/")
    config.add_route("admin.admins", "/admin/admins")
    config.add_route("admin.badge", "/admin/badge")
    config.add_route("admin.features", "/admin/features")
    config.add_route("admin.cohorts", "/admin/features/cohorts")
    config.add_route("admin.cohorts_edit", "/admin/features/cohorts/{id}")
    config.add_route("admin.groups", "/admin/groups")
    config.add_route("admin.groups_create", "/admin/groups/new")
    config.add_route(
        "admin.groups_delete",
        "/admin/groups/delete/{id}",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{id}",
    )
    config.add_route(
        "admin.groups_edit",
        "/admin/groups/{id}",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{id}",
    )
    config.add_route("admin.mailer", "/admin/mailer")
    config.add_route("admin.mailer_test", "/admin/mailer/test")
    config.add_route("admin.nipsa", "/admin/nipsa")
    config.add_route("admin.oauthclients", "/admin/oauthclients")
    config.add_route("admin.oauthclients_create", "/admin/oauthclients/new")
    config.add_route("admin.oauthclients_edit", "/admin/oauthclients/{id}")
    config.add_route("admin.organizations", "/admin/organizations")
    config.add_route("admin.organizations_create", "/admin/organizations/new")
    config.add_route(
        "admin.organizations_delete",
        "/admin/organizations/delete/{pubid}",
        factory="h.traversal.OrganizationRoot",
        traverse="/{pubid}",
    )
    config.add_route(
        "admin.organizations_edit",
        "/admin/organizations/{pubid}",
        factory="h.traversal.OrganizationRoot",
        traverse="/{pubid}",
    )
    config.add_route("admin.staff", "/admin/staff")
    config.add_route("admin.users", "/admin/users")
    config.add_route("admin.users_activate", "/admin/users/activate")
    config.add_route("admin.users_delete", "/admin/users/delete")
    config.add_route("admin.users_rename", "/admin/users/rename")
    config.add_route("admin.search", "/admin/search")

    # Annotations & stream
    config.add_route(
        "annotation", "/a/{id}", factory="h.traversal:AnnotationRoot", traverse="/{id}"
    )
    config.add_route("stream", "/stream")
    config.add_route("stream.user_query", "/u/{user}")
    config.add_route("stream.tag_query", "/t/{tag}")

    # Assets
    config.add_route("assets", "/assets/*subpath")

    # API

    # For historical reasons, the `api` route ends with a trailing slash. This
    # is not (or should not) be necessary, but for now the client will
    # construct URLs incorrectly if its `apiUrl` setting does not end in a
    # trailing slash.
    #
    # Any new parameter names will require a corresponding change to the link
    # template generator in `h/views/api.py`
    config.add_route("api.index", "/api/")
    config.add_route("api.links", "/api/links")
    config.add_route(
        "api.annotations", "/api/annotations", factory="h.traversal:AnnotationRoot"
    )
    config.add_route(
        "api.annotation",
        "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}",
        factory="h.traversal:AnnotationRoot",
        traverse="/{id}",
    )
    config.add_route(
        "api.annotation_flag",
        "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}/flag",
        factory="h.traversal:AnnotationRoot",
        traverse="/{id}",
    )
    config.add_route(
        "api.annotation_hide",
        "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}/hide",
        factory="h.traversal:AnnotationRoot",
        traverse="/{id}",
    )
    config.add_route(
        "api.annotation.jsonld",
        "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}.jsonld",
        factory="h.traversal:AnnotationRoot",
        traverse="/{id}",
    )

    config.add_route("api.bulk", "/api/bulk", request_method="POST")
    config.add_route("api.groups", "/api/groups", factory="h.traversal.GroupRoot")
    config.add_route(
        "api.group_upsert",
        "/api/groups/{id}",
        request_method="PUT",
        factory="h.traversal.GroupRoot",
        traverse="/{id}",
    )
    config.add_route(
        "api.group",
        "/api/groups/{id}",
        request_method=("GET", "PATCH"),
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{id}",
    )
    config.add_route("api.profile", "/api/profile")
    config.add_route("api.profile_groups", "/api/profile/groups")
    config.add_route("api.debug_token", "/api/debug-token")
    config.add_route(
        "api.group_members",
        "/api/groups/{pubid}/members",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{pubid}",
    )
    config.add_route(
        "api.group_member",
        "/api/groups/{pubid}/members/{userid}",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{pubid}",
    )
    config.add_route("api.search", "/api/search")
    config.add_route("api.users", "/api/users", factory="h.traversal.UserRoot")
    config.add_route(
        "api.user_read",
        "/api/users/{userid}",
        request_method="GET",
        factory="h.traversal.UserByIDRoot",
        traverse="/{userid}",
    )
    config.add_route(
        "api.user",
        "/api/users/{username}",
        factory="h.traversal.UserByNameRoot",
        traverse="/{username}",
    )
    config.add_route("badge", "/api/badge")
    config.add_route("token", "/api/token")
    config.add_route("oauth_authorize", "/oauth/authorize")
    config.add_route("oauth_revoke", "/oauth/revoke")

    # Client
    config.add_route("sidebar_app", "/app.html")
    config.add_route("notebook_app", "/notebook")
    config.add_route("embed", "/embed.js")

    # Feeds
    config.add_route("stream_atom", "/stream.atom")
    config.add_route("stream_rss", "/stream.rss")

    # Organizations
    config.add_route(
        "organization_logo",
        "/organizations/{pubid}/logo",
        factory="h.traversal.OrganizationRoot",
        traverse="/{pubid}",
    )

    # Groups
    config.add_route("group_create", "/groups/new")
    config.add_route(
        "group_edit",
        "/groups/{pubid}/edit",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{pubid}",
    )
    # Match "/<pubid>/": we redirect to the version with the slug.
    config.add_route(
        "group_read",
        "/groups/{pubid}/{slug:[^/]*}",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{pubid}",
    )
    config.add_route(
        "group_read_noslug",
        "/groups/{pubid}",
        factory="h.traversal.GroupRequiredRoot",
        traverse="/{pubid}",
    )

    # Help
    config.add_route("help", "/docs/help")
    config.add_route("onboarding", "/welcome/")
    config.add_route("custom_onboarding", "/welcome/{slug}")

    # Notification
    config.add_route("unsubscribe", "/notification/unsubscribe/{token}")

    # Health check
    config.add_route("status", "/_status")

    # Static
    config.add_route("about", "/about/", static=True)
    config.add_route("bioscience", "/bioscience/", static=True)
    config.add_route("blog", "/blog/", static=True)
    config.add_route(
        "chrome-extension",
        "https://chrome.google.com/webstore/detail/bjfhmglciegochdpefhhlphglcehbmek",
        static=True,
    )
    config.add_route("contact", "/contact/", static=True)
    config.add_route("contribute", "/contribute/", static=True)
    config.add_route("education", "/education/", static=True)
    config.add_route("for-publishers", "/for-publishers/", static=True)
    config.add_route("fund", "/fund/", static=True)
    config.add_route("help-center", "/help/", static=True)
    config.add_route("hypothesis-github", "https://github.com/hypothesis", static=True)
    config.add_route(
        "hypothesis-twitter", "https://twitter.com/hypothes_is", static=True
    )
    config.add_route("jobs", "/jobs/", static=True)
    config.add_route("press", "/press/", static=True)
    config.add_route("privacy", "/privacy/", static=True)
    config.add_route("roadmap", "/roadmap/", static=True)
    config.add_route("team", "/team/", static=True)
    config.add_route("terms-of-service", "/terms-of-service/", static=True)
    config.add_route(
        "wordpress-plugin", "https://wordpress.org/plugins/hypothesis/", static=True
    )
