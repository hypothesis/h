# -*- coding: utf-8 -*-

import mock

from h.views import predicates


class TestFeaturePredicate(object):

    def test_text(self):
        predicate = predicates.FeaturePredicate('foo', mock.sentinel.config)

        assert predicate.text() == 'feature = foo'

    def test_phash(self):
        predicate = predicates.FeaturePredicate('foo', mock.sentinel.config)

        assert predicate.phash() == 'feature = foo'

    def test__call__(self):
        request = mock.Mock(spec_set=['feature'])
        predicate = predicates.FeaturePredicate('bar', mock.sentinel.config)

        result = predicate(mock.sentinel.context, request)

        request.feature.assert_called_once_with('bar')
        assert result == request.feature.return_value
