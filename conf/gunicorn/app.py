import os


bind = "unix:/tmp/gunicorn-web.sock"
proc_name = "web"


if "GUNICORN_TIMEOUT" in os.environ:
    timeout = int(os.environ["GUNICORN_TIMEOUT"])


if "WEB_NUM_WORKERS" in os.environ:
    num_workers = int(os.environ["WEB_NUM_WORKERS"])
