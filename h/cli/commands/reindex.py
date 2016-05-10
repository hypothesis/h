# -*- coding: utf-8 -*-

import click
import elasticsearch.helpers

from h.api.search import config


@click.command()
@click.option('-u', '--update-alias/--no-update-alias',
              help='Whether to update the current index alias on completion.')
@click.argument('target')
@click.pass_context
def reindex(ctx, target, update_alias):
    """
    Reindex the annotations into a new Elasticsearch index.

    You must specify the name of a target index. Annotations will be indexed
    from the current configured index into this target index name. If
    `--update-alias` is specified, this command will assume that the current
    configured index is an alias and when the reindex is completed will attempt
    to update it to point to `target`.
    """
    request = ctx.obj['bootstrap']()

    # Configure the new index
    config.configure_index(request.legacy_es, target)

    # Reindex the annotations
    elasticsearch.helpers.reindex(client=request.legacy_es.conn,
                                  source_index=request.legacy_es.index,
                                  target_index=target)

    if update_alias:
        request.legacy_es.conn.indices.update_aliases(body={'actions': [
            # Remove all existing aliases
            {"remove": {"index": "*", "alias": request.legacy_es.index}},
            # Alias current index name to new target
            {"add": {"index": target, "alias": request.legacy_es.index}},
        ]})
