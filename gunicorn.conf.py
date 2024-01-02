import os


if 'H_GUNICORN_CERTFILE' in os.environ:
    certfile = os.environ['H_GUNICORN_CERTFILE']

if 'H_GUNICORN_KEYFILE' in os.environ:
    keyfile = os.environ['H_GUNICORN_KEYFILE']


def when_ready(server):
    name = server.proc_name
    if name == 'web' and 'WEB_NUM_WORKERS' in os.environ:
        server.num_workers = int(os.environ['WEB_NUM_WORKERS'])
    elif name == 'websocket' and 'WEBSOCKET_NUM_WORKERS' in os.environ:
        server.num_workers = int(os.environ['WEBSOCKET_NUM_WORKERS'])
