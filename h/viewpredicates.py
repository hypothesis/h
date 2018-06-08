# -*- coding: utf-8 -*-

"""Custom Pyramid view predicates."""
from __future__ import unicode_literals


class FeaturePredicate(object):
    """True if the request has the given feature flag enabled."""

    def __init__(self, feature, config):
        self.feature = feature

    def text(self):
        return "feature = {feature}".format(feature=self.feature)

    phash = text

    def __call__(self, context, request):
        return request.feature(self.feature)


def includeme(config):
    config.add_view_predicate("feature", FeaturePredicate)
