# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sqlalchemy.orm import subqueryload

from h import formatters
from h import models
from h import presenters
from h import resources
from h import storage
from h.interfaces import IGroupService
from h.services.annotation_moderation import PreloadedAnnotationModerationService
from h.services.flag_count import PreloadedFlagCountService
from h.services.flag import PreloadedFlagService


class AnnotationJSONPresentationService(object):
    def __init__(self, session, user, group_svc, links_svc, flag_svc, flag_count_svc, moderation_svc, has_permission):
        self.session = session
        self.user = user
        self.group_svc = group_svc
        self.links_svc = links_svc
        self.flag_svc = flag_svc
        self.flag_count_svc = flag_count_svc
        self.moderation_svc = moderation_svc
        self.has_permission = has_permission


    def _moderator_check(group):
        return self.has_permission('admin', group)

    def _formatters(self, preload_ids=None):
        return [
            formatters.AnnotationFlagFormatter(
                self._flag_svc(preload_ids),
                self.user
            ),
            formatters.AnnotationHiddenFormatter(
                self._moderation_svc(preload_ids),
                self._moderator_check,
                self.user
            ),
            formatters.AnnotationModerationFormatter(
                self._flag_count_svc(preload_ids),
                self.user,
                self.has_permission
            )
        ]

    def _flag_svc(self, preload_ids):
        if preload_ids:
            return PreloadedFlagService(self.flag_svc, self.user, preload_ids)
        else:
            return self.flag_svc

    def _flag_count_svc(self, preload_ids):
        if preload_ids:
            return PreloadedFlagCountService(self.flag_count_svc, preload_ids)
        else:
            return self.flag_count_svc

    def _moderation_svc(self, preload_ids):
        if preload_ids:
            return PreloadedAnnotationModerationService(self.moderation_svc,
                                                        preload_ids)
        else:
            return self.moderation_svc

    def present(self, annotation_resource):
        presenter = self._get_presenter(annotation_resource, self._formatters())
        return presenter.asdict()

    def present_all(self, annotation_ids):
        def eager_load_documents(query):
            return query.options(
                subqueryload(models.Annotation.document))

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_documents)

        formatters = self._formatters(preload_ids=annotation_ids)

        ars = [resources.AnnotationResource(ann, self.group_svc, self.links_svc)
                     for ann in annotations]
        return [self._get_presenter(r, formatters).asdict() for r in ars]

    def _get_presenter(self, annotation_resource, formatters):
        return presenters.AnnotationJSONPresenter(annotation_resource,
                                                  formatters)


def annotation_json_presentation_service_factory(context, request):
    group_svc = request.find_service(IGroupService)
    links_svc = request.find_service(name='links')
    flag_svc = request.find_service(name='flag')
    flag_count_svc = request.find_service(name='flag_count')
    moderation_svc = request.find_service(name='annotation_moderation')
    return AnnotationJSONPresentationService(session=request.db,
                                             user=request.user,
                                             group_svc=group_svc,
                                             links_svc=links_svc,
                                             flag_svc=flag_svc,
                                             flag_count_svc=flag_count_svc,
                                             moderation_svc=moderation_svc,
                                             has_permission=request.has_permission)
