# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.groups.auth import annotation_group_write_permitted
from h.models.group import WriteableBy


class TestAnnotationGroupWritePermitted(object):
    def test_allows_for_world_group_with_correct_authority(self, pyramid_config, pyramid_request):
        pyramid_request.auth_domain = 'example.com'
        pyramid_config.testing_securitypolicy('acct:testuser@example.com',
                                              groupids=['authority:example.com'])

        assert annotation_group_write_permitted(pyramid_request, '__world__') \
            is True

    def test_disallows_for_world_group_with_wrong_authority(self, pyramid_config, pyramid_request):
        pyramid_request.auth_domain = 'foobar.com'
        pyramid_config.testing_securitypolicy('acct:testuser@example.com',
                                              groupids=['authority:example.com'])

        assert annotation_group_write_permitted(pyramid_request, '__world__') \
            is False

    def test_disallows_when_group_missing(self, pyramid_request):
        assert annotation_group_write_permitted(pyramid_request, 'bogus') \
            is False

    def test_disallows_when_group_non_writeable(self, pyramid_request, factories):
        group = factories.Group(writeable_by=None)

        assert annotation_group_write_permitted(pyramid_request, group.pubid) \
            is False

    def test_allows_for_authority_when_match(self, pyramid_config, pyramid_request, factories):
        group = factories.Group(writeable_by=WriteableBy.authority)
        pyramid_config.testing_securitypolicy('acct:testuser@example.com',
                                              groupids=['authority:%s' % group.authority])

        assert annotation_group_write_permitted(pyramid_request, group.pubid) \
            is True

    def test_disallows_for_authority_when_mismatch(self, pyramid_config, pyramid_request, factories):
        group = factories.Group(writeable_by=WriteableBy.authority)
        pyramid_config.testing_securitypolicy('acct:testuser@example.com',
                                              groupids=['authority:foobar.net'])

        assert annotation_group_write_permitted(pyramid_request, group.pubid) \
            is False

    def test_allows_for_group_member(self, pyramid_config, pyramid_request, factories):
        group = factories.Group(writeable_by=WriteableBy.members)
        pyramid_config.testing_securitypolicy('acct:testuser@example.com',
                                              groupids=['group:%s' % group.pubid])

        assert annotation_group_write_permitted(pyramid_request, group.pubid) \
            is True

    def test_disallows_for_non_group_members(self, pyramid_config, pyramid_request, factories):
        group = factories.Group(writeable_by=WriteableBy.members)
        pyramid_config.testing_securitypolicy('acct:testuser@example.com',
                                              groupids=['group:foobar'])

        assert annotation_group_write_permitted(pyramid_request, group.pubid) \
            is False
