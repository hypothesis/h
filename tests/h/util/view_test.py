# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from mock import Mock

from h.util.view import handle_exception, json_view


class TestHandleException(object):
    def test_sets_response_status_500(self, pyramid_request):
        handle_exception(pyramid_request, Mock())

        assert pyramid_request.response.status_int == 500

    def test_triggers_sentry_capture(self, pyramid_request):
        exception = Mock()
        handle_exception(pyramid_request, exception)

        pyramid_request.sentry.captureException.assert_called_once_with(exception)

    def test_reraises_in_debug_mode(self, pyramid_request):
        pyramid_request.debug = True
        dummy_exc = ValueError('dummy')

        try:
            raise dummy_exc
        except:
            with pytest.raises(ValueError) as exc:
                handle_exception(pyramid_request, Mock())
            assert exc.value == dummy_exc

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        sentry = Mock(spec_set=['captureException'])
        pyramid_request.sentry = sentry
        pyramid_request.debug = False
        return pyramid_request


@pytest.mark.usefixtures('view_config')
class TestJsonView(object):
    def test_sets_accept(self):
        result = json_view()

        assert result['accept'] == 'application/json'

    def test_sets_renderer(self):
        result = json_view()

        assert result['renderer'] == 'json'

    def test_passes_through_other_kwargs(self):
        result = json_view(foo='bar', baz='qux')

        assert result['foo'] == 'bar'
        assert result['baz'] == 'qux'

    def test_allows_overriding_accept(self):
        result = json_view(accept='application/ld+json')

        assert result['accept'] == 'application/ld+json'

    def test_allows_overriding_renderer(self):
        result = json_view(renderer='h:some/template.json.jinja2')

        assert result['renderer'] == 'h:some/template.json.jinja2'

    @pytest.fixture
    def view_config(self, patch):
        def _return_kwargs(**kwargs):
            return kwargs
        view_config = patch('h.util.view.view_config')
        view_config.side_effect = _return_kwargs
        return view_config
