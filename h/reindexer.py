from elasticsearch import helpers
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
