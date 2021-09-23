"""
Resources for Pyramid traversal.

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
                    factory="h.traversal:UserByNameRoot",
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

from h.traversal.annotation import AnnotationContext, AnnotationRoot
from h.traversal.group import GroupRequiredRoot, GroupRoot
from h.traversal.organization import OrganizationContext, OrganizationRoot
from h.traversal.user import UserByIDRoot, UserByNameRoot, UserContext, UserRoot

__all__ = (
    "AnnotationContext",
    "AnnotationRoot",
    "GroupRequiredRoot",
    "GroupRoot",
    "OrganizationContext",
    "OrganizationRoot",
    "UserContext",
    "UserByNameRoot",
    "UserByIDRoot",
    "UserRoot",
)
