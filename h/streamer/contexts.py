from contextlib import contextmanager

from pyramid.scripting import prepare


@contextmanager
def request_context(registry):
    """Convert a registry into a fake, but working Pyramid request."""

    with prepare(registry=registry) as env:
        yield env["request"]
