"""
A base presenter for common properties needed when rendering annotations.
"""

from h.util.datetime import utc_iso8601


class AnnotationBasePresenter:
    def __init__(self, annotation_context):
        self.annotation_context = annotation_context
        self.annotation = annotation_context.annotation

    @property
    def created(self):
        if not self.annotation.created:
            return None
        return utc_iso8601(self.annotation.created)

    @property
    def updated(self):
        if not self.annotation.updated:
            return None
        return utc_iso8601(self.annotation.updated)

    @property
    def links(self):
        """A dictionary of named hypermedia links for this annotation."""
        return self.annotation_context.links

    @property
    def text(self):
        if self.annotation.text:
            return self.annotation.text
        return ""

    @property
    def tags(self):
        if self.annotation.tags:
            return self.annotation.tags
        return []

    @property
    def target(self):
        target = {"source": self.annotation.target_uri}
        if self.annotation.target_selectors:
            target["selector"] = self.annotation.target_selectors

        return [target]
