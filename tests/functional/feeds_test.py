import pytest

pytestmark = pytest.mark.usefixtures("init_elasticsearch")


def test_atom_feed(app):
    app.get("/stream.atom")


def test_rss_feed(app):
    app.get("/stream.rss")
