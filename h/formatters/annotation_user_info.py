from h import models
from h.session import user_info


class AnnotationUserInfoFormatter:
    def __init__(self, session, user_svc):
        self.session = session
        self.user_svc = user_svc

    def preload(self, annotation_ids):
        if not annotation_ids:
            return

        userids = {
            t[0]
            for t in self.session.query(models.Annotation.userid).filter(
                models.Annotation.id.in_(annotation_ids)
            )
        }
        self.user_svc.fetch_all(userids)

    def format(self, annotation):
        user = self.user_svc.fetch(annotation.userid)
        return user_info(user)
