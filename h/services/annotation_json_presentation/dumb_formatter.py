from h.services.annotation_json_presentation._presenter import \
    AnnotationJSONPresenter
from h.session import user_info


class AnnotationAnswers:
    def __init__(self, _flag_count_service):
        ...

    def flag_count(self, annotation_id):
        ...

    def prime(self, annotation_ids):
        ...


class UserAnswers:
    def __init__(self):
        # User service already has caching!
        # ??? Not sure how to do this one, maybe look at websocket
        # Might need to provide the principals per user here to make this work
        # or look up "current" if it's only one
        ...

    def is_moderator(self, user):
        ...

    def prime(self, user_ids):
        ...


class UserAnnotationAnswers:
    def __init__(self, _flag_service):
        ...

    def user_has_flagged(self, user, annotation):
        ...

    def prime(self, user_ids, annotation_ids):
        ...


class DumbPresenterService:
    def __init__(self):
        self._flag_service = None
        self._flag_count_service = None
        self._user_service = None

    def present(self, annotation_resource, user=None):
        annotation = annotation_resource.annotation

        # This depends only on the annotation
        data = AnnotationJSONPresenter(annotation_resource).asdict()
        data.update(user_info(self._user_service.fetch(annotation.userid)))

        user_is_moderator = request.has_permission("moderate", annotation_resource.group)

        # Did this user flag the annotation?
        data['flagged'] = self._flag_service.flagged(user=user, annotation=annotation)

        self._set_hidden(data, annotation, user, user_is_moderator)

        if user_is_moderator:
            flag_count = self._flag_count_service.flag_count(annotation)
            data["moderation"] = {"flagCount": flag_count}

    def _set_hidden(self, data, annotation, user, is_moderator):
        # We never hide things from the person who wrote them
        user_is_author = user and user.userid == annotation.userid
        data["hidden"] = False if user_is_author else bool(annotation.moderation)

        # Blank the contents for non-moderators
        if not is_moderator and data["hidden"]:
            data.update(text="", tags=[])
