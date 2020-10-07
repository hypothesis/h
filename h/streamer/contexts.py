from pyramid.security import DENY_ALL

from h.traversal import AnnotationContext


class AnnotationNotificationContext(AnnotationContext):
    """Context for getting notifications about annotations (e.g. websocket)."""

    def __acl__(self):
        acl = list(self._read_principals())

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(DENY_ALL)

        return acl
