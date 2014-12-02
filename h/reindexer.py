from elasticsearch import helpers
import annotator.reindexer

from h.models import Annotation, Document


class Reindexer(annotator.reindexer.Reindexer):
    es_models = Annotation, Document

    def get_index_config(self):
        index_config = super(Reindexer, self).get_index_config()
        index_config['settings'] = Annotation.__settings__
        return index_config
