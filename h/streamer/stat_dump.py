"""This should be moved to the metrics file when we have that working again."""

import os
from logging import getLogger

from gevent import sleep

from h.streamer.worker import WSGIServer

DUMP_INTERVAL = 60
LOG = getLogger(__name__)


def dump_stats():  # pragma: no cover
    while True:
        # There really only should be one server per instance
        for server in WSGIServer.instances:
            pool = server.connection_pool

            free = pool.free_count()
            in_progress = pool.size - free

            stats = f"has ~{in_progress} workers occupied with ~{free}/{pool.size} free"
            is_full = " (Pool is full!)" if pool.full() else ""
            LOG.info(f"Web socket PID:{os.getpid()} {stats}{is_full}")

        sleep(DUMP_INTERVAL)
