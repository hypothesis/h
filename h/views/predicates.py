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


def includeme(config):
    config.add_view_predicate('has_feature_flag', HasFeatureFlagPredicate)
