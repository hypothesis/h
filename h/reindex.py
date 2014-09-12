import sys
import argparse

from elasticsearch import Elasticsearch, helpers
import annotator.reindexer

from h.models import Annotation, Document


class Reindexer(annotator.reindexer.Reindexer):
    # This class slighty modifies annotator's Reindexer. Besides mappings, it
    # also sets the index settings, and does both directly at index creation.
    # And, of course, it uses our own models instead of annotator's.

    es_models = Annotation, Document

    def reindex(self, old_index, new_index):
        """Reindex documents using the current mappings."""
        conn = self.conn

        if not conn.indices.exists(old_index):
            raise ValueError("Index {0} does not exist!".format(old_index))

        if conn.indices.exists(new_index):
            raise ValueError("Index {0} already exists!".format(new_index))

        # Configure index mapping and settings
        index_config = {'mappings': {}, 'settings': {}}
        for model in self.es_models:
            index_config['mappings'].update(model.get_mapping())
            if hasattr(model, '__settings__'):
                index_config['settings'] = model.__settings__

        # Create the new index
        conn.indices.create(new_index, body=index_config)

        # Do the actual reindexing.
        self._print("Reindexing {0} to {1}..".format(old_index, new_index))
        helpers.reindex(conn, old_index, new_index)
        self._print("Reindexing done.")


description = """
Reindex an elasticsearch index.

WARNING: Documents that are created while reindexing may be lost!
"""


def main(argv):
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('old_index', help="Index to read from")
    argparser.add_argument('new_index', help="Index to write to")
    argparser.add_argument('--host', help="Elasticsearch server, host[:port]")
    argparser.add_argument('--alias', help="Alias for the new index")
    args = argparser.parse_args()

    host = args.host
    old_index = args.old_index
    new_index = args.new_index
    alias = args.alias

    if host:
        conn = Elasticsearch([host])
    else:
        conn = Elasticsearch()

    reindexer = Reindexer(conn, interactive=True)

    reindexer.reindex(old_index, new_index)

    if alias:
        reindexer.alias(new_index, alias)

if __name__ == '__main__':
    main(sys.argv)
