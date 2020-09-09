from unittest import mock

from h.viewpredicates import FeaturePredicate


class TestFeaturePredicate:
    def test_text(self):
        predicate = FeaturePredicate("foo", mock.sentinel.config)

        assert predicate.text() == "feature = foo"

    def test_phash(self):
        predicate = FeaturePredicate("foo", mock.sentinel.config)

        assert predicate.phash() == "feature = foo"

    def test__call__(self):
        request = mock.Mock(spec_set=["feature"])
        predicate = FeaturePredicate("bar", mock.sentinel.config)

        result = predicate(mock.sentinel.context, request)

        request.feature.assert_called_once_with("bar")
        assert result == request.feature.return_value
