"""Service definitions that handle business logic."""
from h.services.auth_cookie import AuthCookieService
from h.services.subscription import SubscriptionService


def includeme(config):  # pragma: no cover
    config.register_service_factory(".annotation_json.factory", name="annotation_json")
    config.register_service_factory(
        ".annotation_moderation.annotation_moderation_service_factory",
        name="annotation_moderation",
    )
    config.register_service_factory(
        ".annotation_stats.annotation_stats_factory", name="annotation_stats"
    )
    config.register_service_factory(".auth_cookie.factory", iface=AuthCookieService)
    config.register_service_factory(
        ".auth_token.auth_token_service_factory", name="auth_token"
    )
    config.register_service_factory(
        ".annotation_delete.annotation_delete_service_factory", name="annotation_delete"
    )
    config.register_service_factory(
        ".delete_group.delete_group_service_factory", name="delete_group"
    )
    config.register_service_factory(
        ".delete_user.delete_user_service_factory", name="delete_user"
    )
    config.register_service_factory(
        ".developer_token.developer_token_service_factory", name="developer_token"
    )
    config.register_service_factory(
        ".document.document_service_factory", name="document"
    )
    config.register_service_factory(".feature.feature_service_factory", name="feature")
    config.register_service_factory(".flag.flag_service_factory", name="flag")
    config.register_service_factory(".group.groups_factory", name="group")
    config.register_service_factory(
        ".group_create.group_create_factory", name="group_create"
    )
    config.register_service_factory(
        ".group_update.group_update_factory", name="group_update"
    )
    config.register_service_factory(
        ".group_links.group_links_factory", name="group_links"
    )
    config.register_service_factory(
        ".group_members.group_members_factory", name="group_members"
    )
    config.register_service_factory(".links.links_factory", name="links")
    config.register_service_factory(".group_list.group_list_factory", name="group_list")
    config.register_service_factory(
        ".group_scope.group_scope_factory", name="group_scope"
    )
    config.register_service_factory(
        ".job_queue.metrics.factory", name="job_queue_metrics"
    )
    config.register_service_factory(
        ".list_organizations.list_organizations_factory", name="list_organizations"
    )
    config.register_service_factory(".nipsa.nipsa_factory", name="nipsa")
    config.register_service_factory(".oauth.service.factory", name="oauth_provider")
    config.register_service_factory(
        ".organization.organization_factory", name="organization"
    )
    config.register_service_factory(
        ".rename_user.rename_user_factory", name="rename_user"
    )
    config.register_service_factory(".search_index.factory", name="search_index")
    config.register_service_factory(".settings.settings_factory", name="settings")
    config.register_service_factory(".user.user_service_factory", name="user")
    config.register_service_factory(
        ".user_unique.user_unique_factory", name="user_unique"
    )
    config.register_service_factory(
        ".user_password.user_password_service_factory", name="user_password"
    )
    config.register_service_factory(
        ".user_signup.user_signup_service_factory", name="user_signup"
    )
    config.register_service_factory(
        ".user_update.user_update_factory", name="user_update"
    )
    config.register_service_factory(
        "h.services.subscription.service_factory", iface=SubscriptionService
    )

    config.add_directive(
        "add_annotation_link_generator", ".links.add_annotation_link_generator"
    )
    config.add_request_method(
        ".feature.FeatureRequestProperty", name="feature", reify=True
    )
