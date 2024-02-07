from os import environ


bind = "0.0.0.0:5000"
reload = True
reload_extra_files = "h/templates"
timeout = 0


max_requests = 100
max_requests_jitter = 10


if "H_GUNICORN_CERTFILE" in environ:
    certfile = environ["H_GUNICORN_CERTFILE"]

if "H_GUNICORN_KEYFILE" in environ:
    keyfile = environ["H_GUNICORN_KEYFILE"]
