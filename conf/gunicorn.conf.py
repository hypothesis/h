from os import environ


bind = "unix:/tmp/gunicorn-web.sock"
worker_tmp_dir = "/dev/shm"
workers = environ["WEB_NUM_WORKERS"]

max_requests = environ.get("GUNICORN_MAX_REQUESTS", 500_000)
max_requests_jitter = environ.get("GUNICORN_MAX_REQUESTS_JITTER", 100_000)
