# -*- coding: utf-8 -*-

from pyramid.decorator import reify
from pyramid.security import Allow, Deny
from pyramid.security import Authenticated, Everyone

from h.api import models


class Resource(dict):
    """
    Resource is an entry in the traversal tree.
    """
    __name__ = None
    __parent__ = None

    def add(self, name, obj):
        """
        Adds obj as a child resource with the given name. Automatically sets
        the __name__ and __parent__ properties of the child resource object.
        """
        obj.__name__ = name
        obj.__parent__ = self
        self[name] = obj


class Collection(Resource):
    """
    A collection of other resources.
    """

    def __getitem__(self, key):
        if key not in self and callable(self.factory):
            self.add(key, self.factory(key))
        return super(Collection, self).__getitem__(key)

    def factory(self, key):
        raise NotImplementedError


class Annotation(Resource):
    """
    A Resource representing an annotation.
    """

    def __acl__(self):
        acl = []

        model = self.model

        # Convert annotator-store roles to pyramid principals
        for action, roles in model.get('permissions', {}).items():
            for role in roles:
                if role.startswith('system.'):
                    raise ValueError('{} is a reserved role.'.format(role))
                elif role.startswith('group:'):
                    if role == 'group:__world__':
                        principal = Everyone
                    elif role == 'group:__authenticated__':
                        principal = Authenticated
                    else:
                        principal = role
                else:
                    principal = role

                # Append the converted rule tuple to the ACL
                rule = (Allow, principal, action)
                acl.append(rule)

        return acl

    @reify
    def model(self):
        if 'id' in self:
            instance = models.Annotation.fetch(self['id'])
            return instance or models.Annotation(id=self['id'])
        else:
            return models.Annotation()


class Annotations(Collection):
    """
    A collection of Annotation resources.
    """

    def __init__(self, request, **kwargs):
        super(Annotations, self).__init__(**kwargs)
        self.request = request

    def __acl__(self):
        aces = []
        try:
            group = self.request.json_body.get('group') or '__world__'
        except ValueError:
            pass
        else:
            aces.append((Allow, 'group:' + group, 'create'))
        return aces + [(Deny, Everyone, 'create')]

    def factory(self, key):
        return Annotation(id=key)


class Root(Resource):
    pass


def create_root(request):
    """
    Returns a new traversal tree root.
    """
    r = Root()
    r.add('annotations', Annotations(request))
    return r
