import os


bind = "localhost:5000"
timeout = 0
graceful_timeout = 0
proc_name = "web"
reload = True


if "H_GUNICORN_CERTFILE" in os.environ:
    certfile = os.environ["H_GUNICORN_CERTFILE"]


if "H_GUNICORN_KEYFILE" in os.environ:
    keyfile = os.environ["H_GUNICORN_KEYFILE"]
