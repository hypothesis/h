from h.session import user_info


class AnnotationUserInfoFormatter:
    def preload(self, annotation_ids):
        ...

    def format(self, annotation):
        return user_info(annotation.user)
