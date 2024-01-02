from os import environ


bind = "unix:/tmp/gunicorn-websocket.sock"
worker_class = "h.streamer.Worker"
graceful_timeout = 0
workers = environ["WEBSOCKET_NUM_WORKERS"]
worker_connections = 8192
