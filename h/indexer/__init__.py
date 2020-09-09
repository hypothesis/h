from h.indexer.reindexer import reindex

__all__ = ("reindex",)


def includeme(config):
    config.add_subscriber(
        "h.indexer.subscribers.subscribe_annotation_event", "h.events.AnnotationEvent"
    )
