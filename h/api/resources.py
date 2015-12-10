# -*- coding: utf-8 -*-

from pyramid.decorator import reify
from pyramid.security import Allow, Deny
from pyramid.security import Authenticated, Everyone

from h.api import auth
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
            principals = auth.translate_annotation_principals(roles)

            for principal in principals:
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
        deny = (Deny, Everyone, 'create')
        group = '__world__'  # Unless we find otherwise, assume public.
        payload = None

        # Ignore invalid JSON. It will get rejected by validation later.
        try:
            payload = self.request.json_body
        except ValueError:
            pass

        if isinstance(payload, dict) and 'group' in payload:
            group = payload['group']

        if group == '__world__':
            return [(Allow, Authenticated, 'create'), deny]

        return [(Allow, 'group:' + group, 'create'), deny]

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
