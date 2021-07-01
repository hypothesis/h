from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.traversal.contexts import UserContext


class TestUserContext:
    def test_acl_assigns_read_to_AuthClient_with_user_authority(self, factories):
        user = factories.User(username="fiona", authority="myauthority.com")
        res = UserContext(user)
        actual = res.__acl__()
        expect = [(security.Allow, "client_authority:myauthority.com", "read")]
        assert actual == expect

    def test_acl_matching_authority_allows_read(self, factories):
        policy = ACLAuthorizationPolicy()

        user = factories.User(username="fiona", authority="myauthority.com")
        res = UserContext(user)

        assert policy.permits(res, ["client_authority:myauthority.com"], "read")
        assert not policy.permits(res, ["client_authority:example.com"], "read")
