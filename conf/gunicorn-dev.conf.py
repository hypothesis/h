from os import environ


bind = "0.0.0.0:5000"
graceful_timeout = 0
timeout = 0


if 'H_GUNICORN_CERTFILE' in environ:
    certfile = environ['H_GUNICORN_CERTFILE']

if 'H_GUNICORN_KEYFILE' in environ:
    keyfile = environ['H_GUNICORN_KEYFILE']
