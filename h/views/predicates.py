"""Custom Pyramid view predicates."""


class HasFeatureFlagPredicate(object):
    """True if the request has the given feature flag enabled."""

    def __init__(self, feature_flag, config):
        self.feature_flag = feature_flag

    def text(self):
        return 'has_feature_flag = {feature_flag}'.format(
            feature_flag=self.feature_flag)

    phash = text

    def __call__(self, context, request):
        return request.feature(self.feature_flag)


class HasPermissionPredicate(object):
    """True if the request has the given permission on the context object."""

    def __init__(self, permission, config):
        self.permission = permission

    def text(self):
        return 'has_permission = {permission}'.format(
            permission=self.permission)

    phash = text

    def __call__(self, context, request):
        return request.has_permission(self.permission)


def includeme(config):
    config.add_view_predicate('has_feature_flag', HasFeatureFlagPredicate)
    config.add_view_predicate('has_permission', HasPermissionPredicate)
