import pytest
import mock

from h import session


class FakeGroup(object):
    def __init__(self, pubid, name, is_public=False):
        self.pubid = pubid
        self.name = name
        self.slug = pubid
        self.is_public = is_public


class TestModel(object):
    def test_sorts_groups(self, authenticated_request):
        authenticated_request.set_groups([
            FakeGroup('c', 'Group A'),
            FakeGroup('b', 'Group B'),
            FakeGroup('a', 'Group B'),
        ])
        session_model = session.model(authenticated_request)

        ids = [group['id'] for group in session_model['groups']]

        assert ids == ['__world__', 'c', 'a', 'b']

    def test_world_group_is_public(self, authenticated_request):
        model = session.model(authenticated_request)
        world_group = [g for g in model['groups'] if g['id'] == '__world__'][0]

        assert world_group['public'] is True

    def test_private_group_is_not_public(self, authenticated_request):
        authenticated_request.set_groups([FakeGroup('a', 'Group A')])

        model = session.model(authenticated_request)
        private_group = [g for g in model['groups'] if g['id'] == 'a'][0]

        assert private_group['public'] is False

    def test_world_group_has_no_url(self, authenticated_request):
        model = session.model(authenticated_request)
        world_group = [g for g in model['groups'] if g['id'] == '__world__'][0]

        assert 'url' not in world_group

    def test_private_group_has_url(self, authenticated_request):
        authenticated_request.set_groups([FakeGroup('a', 'Group A')])

        model = session.model(authenticated_request)
        private_group = [g for g in model['groups'] if g['id'] == 'a'][0]

        assert private_group['url']

    def test_includes_features(self, authenticated_request):
        feature_dict = {
            'feature_one': True,
            'feature_two': False,
        }
        authenticated_request.set_features(feature_dict)

        assert session.model(authenticated_request)['features'] == feature_dict

    def test_anonymous_hides_sidebar_tutorial(self, unauthenticated_request):
        preferences = session.model(unauthenticated_request)['preferences']

        assert 'show_sidebar_tutorial' not in preferences

    @pytest.mark.parametrize('dismissed', [True, False])
    def test_authenticated_sidebar_tutorial(self, authenticated_request, dismissed):
        authenticated_request.set_sidebar_tutorial_dismissed(dismissed)

        preferences = session.model(authenticated_request)['preferences']

        if dismissed:
            assert 'show_sidebar_tutorial' not in preferences
        else:
            assert preferences['show_sidebar_tutorial'] is True


class TestProfile(object):
    def test_userid_unauthenticated(self, unauthenticated_request):
        assert session.profile(unauthenticated_request)['userid'] is None

    def test_userid_authenticated(self, authenticated_request):
        profile = session.profile(authenticated_request)
        assert profile['userid'] == u'acct:user@example.com'

    def test_sorts_groups(self, authenticated_request):
        authenticated_request.set_groups([
            FakeGroup('c', 'Group A'),
            FakeGroup('b', 'Group B'),
            FakeGroup('a', 'Group B'),
        ])
        profile = session.profile(authenticated_request)

        ids = [group['id'] for group in profile['groups']]

        assert ids == ['__world__', 'c', 'a', 'b']

    def test_authenticated_world_group(self, authenticated_request):
        result = session.profile(authenticated_request)

        assert '__world__' in [g['id'] for g in result['groups']]

    def test_anonymous_world_group(self, unauthenticated_request):
        result = session.profile(unauthenticated_request)

        assert '__world__' in [g['id'] for g in result['groups']]

    def test_third_party_missing_world_group(self, third_party_request):
        result = session.profile(third_party_request)

        assert '__world__' not in [g['id'] for g in result['groups']]

    def test_world_group_is_public(self, authenticated_request):
        profile = session.profile(authenticated_request)
        world_group = [g for g in profile['groups'] if g['id'] == '__world__'][0]

        assert world_group['public'] is True

    def test_private_group_is_not_public(self, authenticated_request):
        authenticated_request.set_groups([FakeGroup('a', 'Group A')])

        profile = session.profile(authenticated_request)
        private_group = [g for g in profile['groups'] if g['id'] == 'a'][0]

        assert private_group['public'] is False

    def test_publisher_group_is_public(self, third_party_request, publisher_group):
        profile = session.profile(third_party_request)
        group = [g for g in profile['groups'] if g['id'] == publisher_group.pubid][0]

        assert group['public'] is True

    def test_world_group_has_no_url(self, authenticated_request):
        profile = session.profile(authenticated_request)
        world_group = [g for g in profile['groups'] if g['id'] == '__world__'][0]

        assert 'url' not in world_group

    def test_private_group_has_url(self, authenticated_request):
        authenticated_request.set_groups([FakeGroup('a', 'Group A')])

        profile = session.profile(authenticated_request)
        private_group = [g for g in profile['groups'] if g['id'] == 'a'][0]

        assert private_group['url']

    def test_publisher_group_has_no_url(self, third_party_request, publisher_group):
        profile = session.profile(third_party_request)
        group = [g for g in profile['groups'] if g['id'] == publisher_group.pubid][0]

        assert 'url' not in group

    def test_includes_features(self, authenticated_request):
        feature_dict = {
            'feature_one': True,
            'feature_two': False,
        }
        authenticated_request.set_features(feature_dict)

        assert session.profile(authenticated_request)['features'] == feature_dict

    def test_anonymous_hides_sidebar_tutorial(self, unauthenticated_request):
        preferences = session.profile(unauthenticated_request)['preferences']

        assert 'show_sidebar_tutorial' not in preferences

    @pytest.mark.parametrize('dismissed', [True, False])
    def test_authenticated_sidebar_tutorial(self, authenticated_request, dismissed):
        authenticated_request.set_sidebar_tutorial_dismissed(dismissed)

        preferences = session.profile(authenticated_request)['preferences']

        if dismissed:
            assert 'show_sidebar_tutorial' not in preferences
        else:
            assert preferences['show_sidebar_tutorial'] is True

    def test_anonymous_authority(self, unauthenticated_request, authority):
        assert session.profile(unauthenticated_request)['authority'] == authority

    def test_authority_override(self, unauthenticated_request):
        unauthenticated_request.set_public_groups({'foo.com': []})

        profile = session.profile(unauthenticated_request, 'foo.com')

        assert profile['authority'] == 'foo.com'

    def test_authenticated_authority(self, authenticated_request, authority):
        assert session.profile(authenticated_request)['authority'] == authority

    def test_authenticated_ignores_authority_override(self, authenticated_request, authority):
        profile = session.profile(authenticated_request, 'foo.com')

        assert profile['authority'] == authority

    def test_third_party_authority(self, third_party_request, third_party_domain):
        assert session.profile(third_party_request)['authority'] == third_party_domain

    def test_third_party_ingores_authority_override(self, third_party_request, third_party_domain):
        profile = session.profile(third_party_request, 'foo.com')

        assert profile['authority'] == third_party_domain

    @pytest.fixture
    def third_party_domain(self):
        return u'thirdparty.example.org'

    @pytest.fixture
    def third_party_request(self, authority, third_party_domain, publisher_group):
        return FakeRequest(authority,
                           u'acct:user@{}'.format(third_party_domain),
                           third_party_domain,
                           {third_party_domain: [publisher_group]})

    @pytest.fixture
    def publisher_group(self):
        return FakeGroup('abcdef', 'Publisher group', is_public=True)


class FakeAuthorityGroupService(object):

    def __init__(self, public_groups):
        self._public_groups = public_groups

    def public_groups(self, authority):
        return self._public_groups[authority]


class FakeRequest(object):

    def __init__(self, authority, userid, user_authority, public_groups):
        self.authority = authority
        self.authenticated_userid = userid

        if userid is None:
            self.user = None
        else:
            self.user = mock.Mock(groups=[], authority=user_authority)

        self.feature = mock.Mock(spec_set=['all'])
        self.route_url = mock.Mock(return_value='/group/a')
        self.session = mock.Mock(get_csrf_token=lambda: '__CSRF__')

        self._authority_group_service = FakeAuthorityGroupService(public_groups)

    def set_groups(self, groups):
        self.user.groups = groups

    def set_features(self, feature_dict):
        self.feature.all.return_value = feature_dict

    def set_sidebar_tutorial_dismissed(self, dismissed):
        self.user.sidebar_tutorial_dismissed = dismissed

    def set_public_groups(self, public_groups):
        self._authority_group_service = FakeAuthorityGroupService(public_groups)

    def find_service(self, **kwargs):
        if kwargs == {'name': 'authority_group'}:
            return self._authority_group_service
        else:
            raise AssertionError('find_service called with unrecognised args '
                                 '{}'.format(kwargs))


@pytest.fixture
def authority():
    return u'example.com'


@pytest.fixture
def world_group():
    return FakeGroup('__world__', 'Public', is_public=True)


@pytest.fixture
def unauthenticated_request(authority, world_group):
    return FakeRequest(authority, None, None, {authority: [world_group]})


@pytest.fixture
def authenticated_request(authority, world_group):
    return FakeRequest(authority,
                       u'acct:user@{}'.format(authority),
                       authority,
                       {authority: [world_group]})
