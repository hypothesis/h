import multiprocessing

import pytest

from h.script import Application, assets, get_config


def run(start):
    def prepare(worker):
        settings = get_config(['test.ini'])['settings']
        assets(settings)
        start.release()

    start.acquire()
    start.notify()

    app = Application('test.ini')
    app.cfg.set('post_worker_init', prepare)

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
