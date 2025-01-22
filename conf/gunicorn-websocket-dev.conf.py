from os import environ


bind = "localhost:5001"
worker_class = "h.streamer.Worker"
graceful_timeout = 0
workers = 2
worker_connections = 8


if 'GUNICORN_CERTFILE' in environ:
    certfile = environ['GUNICORN_CERTFILE']

if 'GUNICORN_KEYFILE' in environ:
    keyfile = environ['GUNICORN_KEYFILE']
