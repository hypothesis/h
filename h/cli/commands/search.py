import click

from h.search import config


@click.group()
def search():
    """Manage search index."""


@search.command("update-settings")
@click.pass_context
def update_settings(ctx):
    """
    Attempt to update mappings and settings in elasticsearch.

    Attempts to update mappings and index settings. This may fail if the
    pending changes to mappings are not compatible with the current index. In
    this case you will likely need to reindex.
    """
    request = ctx.obj["bootstrap"]()

    try:
        config.update_index_settings(request.es)
    except RuntimeError as exc:
        raise click.ClickException(str(exc))
