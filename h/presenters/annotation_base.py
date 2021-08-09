"""A base presenter for common properties needed when rendering annotations."""

from h.util.datetime import utc_iso8601


class AnnotationBasePresenter:
    def __init__(self, annotation):
        self.annotation = annotation

    @property
    def created(self):
        return utc_iso8601(self.annotation.created)

    @property
    def updated(self):
        return utc_iso8601(self.annotation.updated)

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
