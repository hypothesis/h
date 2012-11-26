# Custom authorization module for Hypothes.is
#
# Implements the following policy:
#
# 1. Actions are first authorized by the default mechanism.
#    (See annotator.authz.aothorize)
#    If this fails, the action is rejected.
#
# 2. "delete" actions are allowed if the annotation is private.
#
# 3. For non-"delete" actions, the default decision is accepted.

from annotator.authz import _annotation_owner
from annotator.authz import authorize as authorize_default

GROUP_WORLD = 'group:__world__'
GROUP_AUTHENTICATED = 'group:__authenticated__'
GROUP_CONSUMER = 'group:__consumer__'

def authorize(annotation, action, user=None):
    #first check basic conditions
    if authorize_default(annotation, action, user):
        if action == "delete": 
            # If this is a deletion, only allow it
            # if the annotation is private
            view_permission = annotation.get('permissions', {}).get("view", [])
            return GROUP_CONSUMER in view_permission
        else:
            # For other actions, the default permissions are fine
            return True
    else:
        # Default authorization failed, nothing to do
        return False

