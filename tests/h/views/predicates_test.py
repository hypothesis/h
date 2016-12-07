import mock

from h.views import predicates


class TestHasFeatureFlagPredicate(object):

    def test_text(self):
        predicate = predicates.HasFeatureFlagPredicate('foo',
                                                       mock.sentinel.config)

        assert predicate.text() == 'has_feature_flag = foo'

    def test_phash(self):
        predicate = predicates.HasFeatureFlagPredicate('foo',
                                                       mock.sentinel.config)

        assert predicate.phash() == 'has_feature_flag = foo'

    def test__call__(self):
        request = mock.Mock(spec_set=['feature'])
        predicate = predicates.HasFeatureFlagPredicate('bar',
                                                       mock.sentinel.config)

        result = predicate(mock.sentinel.context, request)

        request.feature.assert_called_once_with('bar')
        assert result == request.feature.return_value


class TestHasPermissionPredicate(object):

    def test_text(self):
        predicate = predicates.HasPermissionPredicate('foo',
                                                      mock.sentinel.config)

        assert predicate.text() == 'has_permission = foo'

    def test_phash(self):
        predicate = predicates.HasPermissionPredicate('foo',
                                                      mock.sentinel.config)

        assert predicate.phash() == 'has_permission = foo'

    def test__call__(self):
        request = mock.Mock(spec_set=['has_permission'])
        predicate = predicates.HasPermissionPredicate('bar',
                                                      mock.sentinel.config)

        result = predicate(mock.sentinel.context, request)

        request.has_permission.assert_called_once_with('bar')
        assert result == request.has_permission.return_value
