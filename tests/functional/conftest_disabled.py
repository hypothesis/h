import multiprocessing

from pyramid import authorization
from pyramid.testing import testConfig
import pytest

from h.script import Application, assets


def run(start, settings):
    def prepare(worker):
        assets(settings)
        start.release()

    start.acquire()
    start.notify()

    app = Application('development.ini', settings)
    app.cfg.set('post_worker_init', prepare)
    app.cfg.set('logconfig', None)

    app.run()


@pytest.fixture(scope="session", autouse=True)
def server(settings):
    start = multiprocessing.Condition()
    start.acquire()

    srv = multiprocessing.Process(target=run, args=(start, settings))
    srv.daemon = True
    srv.start()

    start.wait()
    start.release()


@pytest.fixture(scope="function", autouse=True)
def wipe(settings):
    with testConfig(settings=settings) as config:
        authz = authorization.ACLAuthorizationPolicy()
        config.set_authorization_policy(authz)
        config.include('h.api')
        config.include('h.auth.local.models')
