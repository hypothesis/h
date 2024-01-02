from os import environ


bind = "0.0.0.0:5000"
worker_class = "h.streamer.Worker"
graceful_timeout = 0
workers = environ["WEBSOCKET_NUM_WORKERS"]
worker_connections = 8192
