from os import environ


bind = "unix:/tmp/gunicorn-web.sock"
worker_tmp_dir = "/dev/shm"
workers = environ["WEB_NUM_WORKERS"]
