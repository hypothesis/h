import os


bind = "localhost:5000"
proc_name = "web"

# Specific to dev
timeout = 0
graceful_timeout = 0
reload = True


if "H_GUNICORN_CERTFILE" in os.environ:
    certfile = os.environ["H_GUNICORN_CERTFILE"]


if "H_GUNICORN_KEYFILE" in os.environ:
    keyfile = os.environ["H_GUNICORN_KEYFILE"]
