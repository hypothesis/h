"""A base presenter for common properties needed when rendering annotations."""

from h.util.datetime import utc_iso8601


class AnnotationBasePresenter:
    @classmethod
    def created(cls, annotation):
        if not annotation.created:
            return None
        return utc_iso8601(annotation.created)

    @classmethod
    def updated(cls, annotation):
        if not annotation.updated:
            return None
        return utc_iso8601(annotation.updated)

    @classmethod
    def format_date(cls, date):
        return

    @classmethod
    def text(cls, annotation):
        return annotation.text or ""

    @classmethod
    def tags(cls, annotation):
        return annotation.tags or []

    @classmethod
    def target(cls, annotation):
        target = {"source": annotation.target_uri}
        if annotation.target_selectors:
            target["selector"] = annotation.target_selectors

        return [target]
