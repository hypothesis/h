import os


bind = "localhost:5001"
timeout = 0
graceful_timeout = 0
worker_class = "h.websocket.Worker"
proc_name = "websocket"
reload = True


if "H_GUNICORN_CERTFILE" in os.environ:
    certfile = os.environ["H_GUNICORN_CERTFILE"]


if "H_GUNICORN_KEYFILE" in os.environ:
    keyfile = os.environ["H_GUNICORN_KEYFILE"]


def post_fork(server, worker):
    # Patch psycopg2 if we're asked to by the worker class.
    if getattr(server.worker_class, "use_psycogreen", False):
        import psycogreen.gevent

        psycogreen.gevent.patch_psycopg()
        worker.log.info("Made psycopg green")
