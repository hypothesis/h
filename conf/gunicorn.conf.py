from os import environ


bind = "unix:/tmp/gunicorn-web.sock"
workers = environ["WEB_NUM_WORKERS"]
