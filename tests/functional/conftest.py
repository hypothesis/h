import multiprocessing

from gunicorn import config, util
from gunicorn.app import pasterapp, wsgiapp
import pytest


class TestApplication(wsgiapp.WSGIApplication):

    """A Gunicorn Paster Application suitable for use in tests.

    Extends the base :class:`gunicorn.app.base.Application` class to skip
    processing of command line arguments and directly load a configuration
    from the test.ini file.
    """

    def load_config(self):
        self.cfgurl = 'config:test.ini'
        self.cfg = config.Config()
        self.cfg.set('paste', self.cfgurl)
        self.cfg.set('logconfig', 'test.ini')
        self.relpath = util.getcwd()

        cfg = pasterapp.paste_config(self.cfg, self.cfgurl, self.relpath)

        for k, v in cfg.items():
            self.cfg.set(k.lower(), v)


def run(start):
    start.acquire()
    start.notify()
    app = TestApplication()
    app.cfg.set('post_worker_init', lambda worker: start.release())
    app.run()


@pytest.fixture(scope="session", autouse=True)
def server():
    start = multiprocessing.Condition()
    start.acquire()

    srv = multiprocessing.Process(target=run, args=(start,))
    srv.daemon = True
    srv.start()

    start.wait()
    start.release()
