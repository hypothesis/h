# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import Interface


class IGroupService(Interface):
    def find(self, id_):
        """
        Finds and returns a group based on the given id.

        :param id_: The group id.
        :type id_: unicode

        :returns A group object with:
          * an ``__acl__()`` method
          * a ``scopes`` property (``list``)
        """
