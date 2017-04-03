# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models


class AnnotationModerationService(object):
    def __init__(self, session):
        self.session = session

    def hide(self, annotation):
        """
        Hide an annotation from other users.

        This hides the given annotation from anybody except its author and the
        group moderators.

        In case the given annotation already has a moderation flag, this method
        is a no-op.

        :param annotation: The annotation to hide from others.
        :type annotation: h.models.Annotation
        """

        query = self.session.query(models.AnnotationModeration) \
                            .filter_by(annotation=annotation)

        if query.count() > 0:
            return

        mod = models.AnnotationModeration(annotation=annotation)
        self.session.add(mod)


def annotation_moderation_service_factory(context, request):
    return AnnotationModerationService(request.db)
