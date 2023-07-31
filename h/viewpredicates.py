"""Custom Pyramid view predicates."""


class FeaturePredicate:
    """True if the request has the given feature flag enabled."""

    def __init__(self, feature, _config):
        self.feature = feature

    def text(self):
        return f"feature = {self.feature}"

    phash = text

    def __call__(self, _context, request):
        return request.feature(self.feature)


def includeme(config):  # pragma: nocover
    config.add_view_predicate("feature", FeaturePredicate)
