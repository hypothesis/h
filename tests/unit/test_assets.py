from mock import Mock
from pyramid.testing import DummyRequest, testConfig

from h import assets
from . import AppTestCase


class DummyEvent(object):
    def __init__(self, request):
        self.request = request


class DummyRoute(object):
    pass


class AssetsTest(AppTestCase):
    def test_asset_request_subscriber_predicate(self):
        m1 = Mock()
        m2 = Mock()

        with testConfig(settings=self.settings) as config:
            config.include(assets)
            config.add_subscriber(m1, DummyEvent, asset_request=False)
            config.add_subscriber(m2, DummyEvent, asset_request=True)

            r1 = DummyRequest('/')
            r1.matched_route = None

            r2 = DummyRequest(config.get_webassets_env().url + '/i/t.png')
            r2.matched_route = DummyRoute()
            r2.matched_route.pattern = config.get_webassets_env().url

            e1 = DummyEvent(r1)
            e2 = DummyEvent(r2)

            config.registry.notify(e1)
            config.registry.notify(e2)

            m1.assert_called_once_with(e1)
            m2.assert_called_once_with(e2)
