# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
from collections import namedtuple
from h._compat import unichr

import pytest
import mock
from hypothesis import strategies as st
from hypothesis import given

from pyramid import security

from h.auth import role
from h.auth import util
from h._compat import text_type


FakeUser = namedtuple('FakeUser', ['authority', 'admin', 'staff', 'groups'])
FakeGroup = namedtuple('FakeGroup', ['pubid'])

# The most recent standard covering the 'Basic' HTTP Authentication scheme is
# RFC 7617. It defines the allowable characters in usernames and passwords as
# follows:
#
#     The user-id and password MUST NOT contain any control characters (see
#     "CTL" in Appendix B.1 of [RFC5234]).
#
# RFC5234 defines CTL as:
#
#     CTL            =  %x00-1F / %x7F
#
CONTROL_CHARS = set(unichr(n) for n in range(0x00, 0x1F + 1)) | set('\x7f')

# We assume user ID and password strings are UTF-8 and surrogates are not
# allowed in UTF-8.
SURROGATE_CHARS = set(unichr(n) for n in range(0xD800, 0xDBFF + 1)) | \
                  set(unichr(n) for n in range(0xDC00, 0xDFFF + 1))
INVALID_USER_PASS_CHARS = CONTROL_CHARS | SURROGATE_CHARS

# Furthermore, from RFC 7617:
#
#     a user-id containing a colon character is invalid
#
INVALID_USERNAME_CHARS = INVALID_USER_PASS_CHARS | set(':')

# The character encoding of the user-id and password is *undefined* by
# specification for historical reasons:
#
#     The original definition of this authentication scheme failed to specify
#     the character encoding scheme used to convert the user-pass into an
#     octet sequence.  In practice, most implementations chose either a
#     locale-specific encoding such as ISO-8859-1 ([ISO-8859-1]), or UTF-8
#     ([RFC3629]).  For backwards compatibility reasons, this specification
#     continues to leave the default encoding undefined, as long as it is
#     compatible with US-ASCII (mapping any US-ASCII character to a single
#     octet matching the US-ASCII character code).
#
# In particular, Firefox still does *very* special things if you provide
# non-BMP characters in a username or password.
#
# There's not a lot we can do about this so we are going to assume UTF-8
# encoding for the user-pass string, and these tests verify that we
# successfully decode valid Unicode user-pass strings.
#
VALID_USERNAME_CHARS = st.characters(blacklist_characters=INVALID_USERNAME_CHARS)
VALID_PASSWORD_CHARS = st.characters(blacklist_characters=INVALID_USER_PASS_CHARS)


class TestBasicAuthCreds(object):

    @given(username=st.text(alphabet=VALID_USERNAME_CHARS),
           password=st.text(alphabet=VALID_PASSWORD_CHARS))
    def test_valid(self, username, password, pyramid_request):
        user_pass = username + ':' + password
        creds = ('Basic', base64.standard_b64encode(user_pass.encode('utf-8')))
        pyramid_request.authorization = creds

        assert util.basic_auth_creds(pyramid_request) == (username, password)

    def test_missing(self, pyramid_request):
        pyramid_request.authorization = None

        assert util.basic_auth_creds(pyramid_request) is None

    def test_no_password(self, pyramid_request):
        creds = ('Basic', base64.standard_b64encode('foobar'.encode('utf-8')))
        pyramid_request.authorization = creds

        assert util.basic_auth_creds(pyramid_request) is None

    def test_other_authorization_type(self, pyramid_request):
        creds = ('Digest', base64.standard_b64encode('foo:bar'.encode('utf-8')))
        pyramid_request.authorization = creds

        assert util.basic_auth_creds(pyramid_request) is None


class TestGroupfinder(object):
    def test_it_fetches_the_user(self, pyramid_request, user_service):
        util.groupfinder('acct:bob@example.org', pyramid_request)
        user_service.fetch.assert_called_once_with('acct:bob@example.org')

    def test_it_returns_principals_for_user(self,
                                            pyramid_request,
                                            user_service,
                                            principals_for_user):
        result = util.groupfinder('acct:bob@example.org', pyramid_request)

        principals_for_user.assert_called_once_with(user_service.fetch.return_value)
        assert result == principals_for_user.return_value


@pytest.mark.parametrize('user,principals', (
    # User isn't found in the database: they're not authenticated at all
    (None, None),
    # User found but not staff, admin, or a member of any groups: no additional principals
    (FakeUser(authority='example.com', admin=False, staff=False, groups=[]),
     ['authority:example.com']),
    # User is admin: role.Admin should be in principals
    (FakeUser(authority='foobar.org', admin=True, staff=False, groups=[]),
     ['authority:foobar.org', role.Admin]),
    # User is staff: role.Staff should be in principals
    (FakeUser(authority='example.com', admin=False, staff=True, groups=[]),
     ['authority:example.com', role.Staff]),
    # User is admin and staff
    (FakeUser(authority='foobar.org', admin=True, staff=True, groups=[]),
     ['authority:foobar.org', role.Admin, role.Staff]),
    # User is a member of some groups
    (FakeUser(authority='example.com', admin=False, staff=False, groups=[FakeGroup('giraffe'), FakeGroup('elephant')]),
     ['authority:example.com', 'group:giraffe', 'group:elephant']),
    # User is admin, staff, and a member of some groups
    (FakeUser(authority='foobar.org', admin=True, staff=True, groups=[FakeGroup('donkeys')]),
     ['authority:foobar.org', 'group:donkeys', role.Admin, role.Staff]),
))
def test_principals_for_user(user, principals):
    result = util.principals_for_user(user)

    if principals is None:
        assert result is None
    else:
        assert set(principals) == set(result)


@pytest.mark.parametrize("p_in,p_out", [
    # The basics
    ([], []),
    (['acct:donna@example.com'], ['acct:donna@example.com']),
    (['group:foo'], ['group:foo']),

    # Remove pyramid principals
    (['system.Everyone'], []),

    # Remap annotatator principal names
    (['group:__world__'], [security.Everyone]),

    # Normalise multiple principals
    (['me', 'myself', 'me', 'group:__world__', 'group:foo', 'system.Admins'],
     ['me', 'myself', security.Everyone, 'group:foo']),
])
def test_translate_annotation_principals(p_in, p_out):
    result = util.translate_annotation_principals(p_in)

    assert set(result) == set(p_out)


class TestAuthDomain(object):
    def test_it_returns_the_request_domain_if_authority_isnt_set(
            self, pyramid_request):
        # Make sure h.authority isn't set.
        pyramid_request.registry.settings.pop('h.authority', None)

        assert util.authority(pyramid_request) == pyramid_request.domain

    def test_it_allows_overriding_request_domain(self, pyramid_request):
        pyramid_request.registry.settings['h.authority'] = 'foo.org'
        assert util.authority(pyramid_request) == 'foo.org'

    def test_it_returns_text_type(self, pyramid_request):
        pyramid_request.domain = str(pyramid_request.domain)
        assert type(util.authority(pyramid_request)) == text_type


@pytest.fixture
def user_service(pyramid_config):
    service = mock.Mock(spec_set=['fetch'])
    service.fetch.return_value = None
    pyramid_config.register_service(service, name='user')
    return service


@pytest.fixture
def principals_for_user(patch):
    return patch('h.auth.util.principals_for_user')
