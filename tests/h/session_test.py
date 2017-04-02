import pytest
import mock

from h import session


class FakeGroup(object):
    def __init__(self, pubid, name, is_public=False, creator_id=None):
        self.pubid = pubid
        self.name = name
        self.slug = pubid
        self.is_public = is_public
        self.creator_id = creator_id


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

    def test_sets_group_moderator_true_when_creator(self, authenticated_request):
        authenticated_request.set_groups([
            FakeGroup('a', 'Group A', creator_id=authenticated_request.authenticated_user.id)])

        model = session.model(authenticated_request)
        private_group = [g for g in model['groups'] if g['id'] == 'a'][0]

        assert private_group['is_moderator'] is True

    def test_sets_group_moderator_false_when_only_member(self, authenticated_request):
        authenticated_request.set_groups([FakeGroup('a', 'Group A', creator_id=12)])

        model = session.model(authenticated_request)
        for group in model['groups']:
            assert group['is_moderator'] is False

    def test_sets_group_moderator_false_when_anonymous(self, unauthenticated_request):
        model = session.model(unauthenticated_request)
        for group in model['groups']:
            assert group['is_moderator'] is False

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

    def test_anonymous_authority(self, unauthenticated_request, auth_domain):
        assert session.profile(unauthenticated_request)['authority'] == auth_domain

    def test_authority_override(self, unauthenticated_request):
        unauthenticated_request.set_public_groups({'foo.com': []})

        profile = session.profile(unauthenticated_request, 'foo.com')

        assert profile['authority'] == 'foo.com'

    def test_authenticated_authority(self, authenticated_request, auth_domain):
        assert session.profile(authenticated_request)['authority'] == auth_domain

    def test_authenticated_ignores_authority_override(self, authenticated_request, auth_domain):
        profile = session.profile(authenticated_request, 'foo.com')

        assert profile['authority'] == auth_domain

    def test_third_party_authority(self, third_party_request, third_party_domain):
        assert session.profile(third_party_request)['authority'] == third_party_domain

    def test_third_party_ingores_authority_override(self, third_party_request, third_party_domain):
        profile = session.profile(third_party_request, 'foo.com')

        assert profile['authority'] == third_party_domain

    @pytest.fixture
    def third_party_domain(self):
        return u'thirdparty.example.org'

    @pytest.fixture
    def third_party_request(self, auth_domain, third_party_domain, publisher_group):
        return FakeRequest(auth_domain,
                           u'acct:user@{}'.format(third_party_domain),
                           third_party_domain,
                           {third_party_domain: [publisher_group]})

    @pytest.fixture
    def publisher_group(self):
        return FakeGroup(pubid='abcdef',
                         name='Publisher group',
                         is_public=True,
                         creator_id=42)


class FakeAuthorityGroupService(object):

    def __init__(self, public_groups):
        self._public_groups = public_groups

    def public_groups(self, authority):
        return self._public_groups[authority]


class FakeRequest(object):

    def __init__(self, auth_domain, userid, user_authority, public_groups):
        self.auth_domain = auth_domain
        self.authenticated_userid = userid

        if userid is None:
            self.authenticated_user = None
        else:
            self.authenticated_user = mock.Mock(id=42, groups=[], authority=user_authority)

        self.feature = mock.Mock(spec_set=['all'])
        self.route_url = mock.Mock(return_value='/group/a')
        self.session = mock.Mock(get_csrf_token=lambda: '__CSRF__')

        self._authority_group_service = FakeAuthorityGroupService(public_groups)

    def set_groups(self, groups):
        self.authenticated_user.groups = groups

    def set_features(self, feature_dict):
        self.feature.all.return_value = feature_dict

    def set_sidebar_tutorial_dismissed(self, dismissed):
        self.authenticated_user.sidebar_tutorial_dismissed = dismissed

    def set_public_groups(self, public_groups):
        self._authority_group_service = FakeAuthorityGroupService(public_groups)

    def find_service(self, **kwargs):
        if kwargs == {'name': 'authority_group'}:
            return self._authority_group_service
        else:
            raise AssertionError('find_service called with unrecognised args '
                                 '{}'.format(kwargs))


@pytest.fixture
def auth_domain():
    return u'example.com'


@pytest.fixture
def world_group():
    return FakeGroup(pubid='__world__',
                     name='Public',
                     is_public=True,
                     creator_id=None)


@pytest.fixture
def unauthenticated_request(auth_domain, world_group):
    return FakeRequest(auth_domain, None, None, {auth_domain: [world_group]})


@pytest.fixture
def authenticated_request(auth_domain, world_group):
    return FakeRequest(auth_domain,
                       u'acct:user@{}'.format(auth_domain),
                       auth_domain,
                       {auth_domain: [world_group]})
