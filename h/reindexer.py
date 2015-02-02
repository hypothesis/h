import annotator.reindexer

from h.models import Annotation, Document


class Reindexer(annotator.reindexer.Reindexer):
    es_models = Annotation, Document

    def get_index_config(self):
        analysis = {}
        for model in self.es_models:
            for section, items in model.get_analysis().items():
                existing_items = analysis.setdefault(section, {})
                for name in items:
                    if name in existing_items:
                        fmt = "Duplicate definition of 'index.analysis.{}.{}'."
                        msg = fmt.format(section, name)
                        raise RuntimeError(msg)
                existing_items.update(items)

        index_config = super(Reindexer, self).get_index_config()
        index_config['settings'] = {'analysis': analysis}

        return index_config
