# -*- coding: utf-8 -*-

# Types representing events stored in the notification queue
# (see queue.py)

class Event(object):
    def __init__(self, request):
        self.request = request

class AnnotationEvent(Event):
    """An event representing an action on an annotation."""

    def __init__(self, request, annotation, action):
        Event.__init__(self, request)
        self.annotation = annotation
        self.action = action

class UserStatusEvent(Event):
    """An event representing a change in a user's status."""

    def __init__(self, request, user_id, type, group_id = None):
        assert type in ['group-joined', 'group-left']

        Event.__init__(self, request)

        self.user_id = user_id
        """ The ID of the user affected by the event """

        self.type = type
        """ The type of action (eg. joined a group, left a group) """

        self.group_id = group_id
        """ Optional. For group membership events, the hash ID of the group """
