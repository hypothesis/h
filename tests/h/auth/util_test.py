# -*- coding: utf-8 -*-

import base64
from collections import namedtuple

import pytest
import mock
from hypothesis import strategies as st
from hypothesis import given

from pyramid import security

from h.auth import role
from h.auth import util


FakeUser = namedtuple('FakeUser', ['admin', 'staff', 'groups'])
FakeGroup = namedtuple('FakeGroup', ['pubid'])

# RFC 2617 defines the valid format of an HTTP Basic access authentication
# header as follows:
#
#     credentials = "Basic" basic-credentials
#     basic-credentials = base64-user-pass
#     base64-user-pass  = <base64 encoding of user-pass, except not limited to 76 char/line>
#     user-pass   = userid ":" password
#     userid      = *<TEXT excluding ":">
#     password    = *TEXT
#
# Where TEXT is earlier defined as follows:
#
#     OCTET          = <any 8-bit sequence of data>
#     CR             = <US-ASCII CR, carriage return (13)>
#     LF             = <US-ASCII LF, linefeed (10)>
#     SP             = <US-ASCII SP, space (32)>
#     HT             = <US-ASCII HT, horizontal-tab (9)>
#     CTL            = <any US-ASCII control character (octets 0 - 31) and DEL (127)>
#     LWS            = [CRLF] 1*( SP | HT )
#     TEXT           = <any OCTET except CTLs, but including LWS>
#
# When combined with other rules about header folding, this basically means
# that all of ISO-8859-1 is allowed except for non-LWS control characters.
#
# Unfortunately for us, it's not as simple as that, because while the RFCs
# clearly imply that only 8-bit encodings are valid in these credentials, this
# is in practice not the case, and it appears that Chrome and curl UTF-8
# encode the text provided by the user, while Firefox UTF-8 encodes the text
# and then discards all but the last byte (having the effect that only text in
# the ISO-8859-1 character set survives unscathed.)
#
# In practice this won't matter if we never issue usernames and passwords with
# characters outside the ISO-8859-1 character set, but here we test that we
# can correctly handle arbitrary Unicode.
INVALID_CONTROL_CHARS = set(chr(n)
                            for n in range(32)
                            if chr(n) not in ' \t')
INVALID_CONTROL_CHARS.add('\x7f')  # DEL (127)
INVALID_USERNAME_CHARS = INVALID_CONTROL_CHARS | set(':')
VALID_USERNAME_CHARS = st.characters(blacklist_characters=INVALID_USERNAME_CHARS)
VALID_PASSWORD_CHARS = st.characters(blacklist_characters=INVALID_CONTROL_CHARS)


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
    (FakeUser(admin=False, staff=False, groups=[]),
     []),
    # User is admin: role.Admin should be in principals
    (FakeUser(admin=True, staff=False, groups=[]),
     [role.Admin]),
    # User is staff: role.Staff should be in principals
    (FakeUser(admin=False, staff=True, groups=[]),
     [role.Staff]),
    # User is admin and staff
    (FakeUser(admin=True, staff=True, groups=[]),
     [role.Admin, role.Staff]),
    # User is a member of some groups
    (FakeUser(admin=False, staff=False, groups=[FakeGroup('giraffe'), FakeGroup('elephant')]),
     ['group:giraffe', 'group:elephant']),
    # User is admin, staff, and a member of some groups
    (FakeUser(admin=True, staff=True, groups=[FakeGroup('donkeys')]),
     ['group:donkeys', role.Admin, role.Staff]),
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


@pytest.fixture
def user_service(pyramid_config):
    service = mock.Mock(spec_set=['fetch'])
    service.fetch.return_value = None
    pyramid_config.register_service(service, name='user')
    return service

@pytest.fixture
def principals_for_user(patch):
    return patch('h.auth.util.principals_for_user')
