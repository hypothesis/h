# -*- coding: utf-8 -*-
"""
Root resources for Pyramid traversal.

Root resources are reusable components that can handle things like looking up a
model object in the database, raising :py:exc:`KeyError` if the object doesn't
exist in the database, and checking whether the request has permission to
access the object.

In this app we use combined traversal and URL dispatch. For documentation of
this approach see:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hybrid.html

Usage:

.. code-block:: python

   config.add_route("activity.user_search", "/users/{username}",
                    factory="h.traversal:UserRoot",
                    traverse="/{username}")

When configuring a route in :py:mod:`h.routes` you can use the ``factory``
argument to tell it to use one of the root resource factories in this class
instead of the default root resource factory.

In this app we also always use the ``traverse`` argument to specify a traversal
pattern that Pyramid should use to find the ``context`` object to pass to the
view. And we always use a traversal path of length 1 (only one ``/`` in the
``traverse`` pattern, at the start).

For documentation of ``factory`` and ``traverse`` see
https://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator.add_route

The intended pattern in this app is that all root resources **should return
context objects** from :py:mod:`h.traversal.contexts` (or raise
:py:exc:`KeyError`), they shouldn't return other types of object (e.g. they
shouldn't return model objects directly).

.. note::

   Technically the *classes* in this module are Pyramid "root factories"
   (hence the ``factory`` argument to :py:func:`pyramid.config.Configurator.add_route`)
   and the *object instances* of these classes are the Pyramid "root resources"
   that the factories return when called (instantiated).

.. note::

   In order to encapsulate SQLAlchemy in the models and services, root
   resources should look up objects in the DB by calling a ``@classmethod`` of
   a :py:mod:`h.models` class or a method of a service from
   :py:mod:`h.services`, rather than by doing DB queries directly.

.. seealso::

   The Pyramid documentation on traversal:

   * https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hellotraversal.html
   * https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/muchadoabouttraversal.html
   * https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html

"""
from __future__ import unicode_literals


from pyramid.security import (
    ALL_PERMISSIONS,
    DENY_ALL,
    Allow,
)
import sqlalchemy.exc
import sqlalchemy.orm.exc

from h import storage
from h.models import AuthClient
from h.models import Group
from h.models import Organization
from h.auth import role
from h.interfaces import IGroupService
from h.traversal import contexts


class Root(object):
    """This app's default root factory."""
    __acl__ = [
        (Allow, role.Staff, 'admin_index'),
        (Allow, role.Staff, 'admin_groups'),
        (Allow, role.Staff, 'admin_mailer'),
        (Allow, role.Staff, 'admin_organizations'),
        (Allow, role.Staff, 'admin_users'),
        (Allow, role.Admin, ALL_PERMISSIONS),
        DENY_ALL
    ]

    def __init__(self, request):
        self.request = request


class AnnotationRoot(object):
    """Root factory for routes whose context is an :py:class:`h.traversal.AnnotationContext`."""
    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        annotation = storage.fetch_annotation(self.request.db, id)
        if annotation is None:
            raise KeyError()

        group_service = self.request.find_service(IGroupService)
        links_service = self.request.find_service(name='links')
        return contexts.AnnotationContext(annotation, group_service, links_service)


class AuthClientRoot(object):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.AuthClientContext`.

    FIXME: This class should return AuthClientContext objects, not AuthClient
    objects.

    """
    def __init__(self, request):
        self.request = request

    def __getitem__(self, client_id):
        try:
            client = self.request.db.query(AuthClient).filter_by(id=client_id).one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise KeyError()
        except sqlalchemy.exc.DataError:  # Happens when client_id is not a valid UUID.
            raise KeyError()

        # Add the default root factory to this resource's lineage so that the default
        # ACL is applied. This is needed so that permissions required by auth client
        # admin views (e.g. the "admin_oauthclients" permission) are granted to admin
        # users.
        #
        # For details on how ACLs work see the docs for Pyramid's ACLAuthorizationPolicy:
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/authorization.html
        client.__parent__ = Root(self.request)

        return client


class OrganizationRoot(object):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.OrganizationContext`.

    FIXME: This class should return OrganizationContext objects, not Organization
    objects.

    """
    def __init__(self, request):
        self.request = request

    def __getitem__(self, pubid):
        try:
            org = self.request.db.query(Organization).filter_by(pubid=pubid).one()

            # Inherit global ACL. See comments in :py:class`h.traversal.AuthClientRoot`.
            org.__parent__ = Root(self.request)

            return org
        except sqlalchemy.orm.exc.NoResultFound:
            raise KeyError()


class OrganizationLogoRoot(object):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.OrganizationLogoContext`.

    FIXME: This class should return OrganizationLogoContext objects, not
    organization logos.

    """
    def __init__(self, request):
        self.request = request
        self.organization_factory = OrganizationRoot(self.request)

    def __getitem__(self, pubid):
        # This will raise KeyError if the organization doesn't exist.
        organization = self.organization_factory[pubid]

        if not organization.logo:
            raise KeyError()

        return organization.logo


class GroupRoot(object):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.GroupContext`.

    FIXME: This class should return GroupContext objects, not Group objects.

    """
    def __init__(self, request):
        self.request = request

    def __getitem__(self, pubid):
        try:
            return self.request.db.query(Group).filter_by(pubid=pubid).one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise KeyError()


class UserRoot(object):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.UserContext`.

    FIXME: This class should return UserContext objects, not User objects.

    """
    __acl__ = [
        (Allow, role.AuthClient, 'create'),
    ]

    def __init__(self, request):
        self.request = request
        self.user_svc = self.request.find_service(name='user')

    def __getitem__(self, username):
        # FIXME: At present, this fetch would never work for third-party users
        user = self.user_svc.fetch(username, self.request.default_authority)

        if not user:
            raise KeyError()

        return user
