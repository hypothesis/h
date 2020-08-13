import os


bind = "unix:/tmp/gunicorn-websocket.sock"
worker_class = "h.websocket.Worker"
graceful_timeout = 0
worker_connections = 4096
proc_name = "websocket"


if "GUNICORN_TIMEOUT" in os.environ:
    timeout = int(os.environ["GUNICORN_TIMEOUT"])


if "WEBSOCKET_NUM_WORKERS" in os.environ:
    num_workers = int(os.environ["WEBSOCKET_NUM_WORKERS"])


def post_fork(server, worker):
    # Patch psycopg2 if we're asked to by the worker class.
    if getattr(server.worker_class, "use_psycogreen", False):
        import psycogreen.gevent

        psycogreen.gevent.patch_psycopg()
        worker.log.info("Made psycopg green")
