from glob import glob

bind = "0.0.0.0:5000"
reload = True
reload_extra_files = glob("h/templates/**/*", recursive=True)
timeout = 0


from os import environ

max_requests = 100
max_requests_jitter = 10


if "GUNICORN_CERTFILE" in environ:
    certfile = environ["GUNICORN_CERTFILE"]

if "GUNICORN_KEYFILE" in environ:
    keyfile = environ["GUNICORN_KEYFILE"]
