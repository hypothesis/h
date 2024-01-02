bind = "unix:/tmp/gunicorn-websocket.sock"
worker_class = "h.streamer.Worker"
graceful_timeout = 0
workers = 2
worker_connections = 8192
