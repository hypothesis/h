"""Code for generating feeds (e.g. Atom and RSS feeds)."""
from h.feeds.render import render_atom
from h.feeds.render import render_rss


def includeme(config):
    config.include('.views')
