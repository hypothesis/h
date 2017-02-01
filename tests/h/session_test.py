import pytest
import mock

from h import session


class FakeGroup(object):
    def __init__(self, pubid, name, is_public=False):
        self.pubid = pubid
        self.name = name
        self.slug = pubid
        self.is_public = is_public


def test_model_sorts_groups(authenticated_request):
    authenticated_request.set_groups([
        FakeGroup('c', 'Group A'),
        FakeGroup('b', 'Group B'),
        FakeGroup('a', 'Group B'),
    ])
    session_model = session.model(authenticated_request)

    ids = [group['id'] for group in session_model['groups']]

    assert ids == ['__world__', 'c', 'a', 'b']


def test_world_group_is_public_in_model(authenticated_request):
    model = session.model(authenticated_request)
    world_group = [g for g in model['groups'] if g['id'] == '__world__'][0]

    assert world_group['public'] is True


def test_private_group_is_not_public_in_model(authenticated_request):
    authenticated_request.set_groups([FakeGroup('a', 'Group A')])

    model = session.model(authenticated_request)
    private_group = [g for g in model['groups'] if g['id'] == 'a'][0]

    assert private_group['public'] is False


def test_world_group_has_no_url_in_model(authenticated_request):
    model = session.model(authenticated_request)
    world_group = [g for g in model['groups'] if g['id'] == '__world__'][0]

    assert 'url' not in world_group


def test_private_group_has_url_in_model(authenticated_request):
    authenticated_request.set_groups([FakeGroup('a', 'Group A')])

    model = session.model(authenticated_request)
    private_group = [g for g in model['groups'] if g['id'] == 'a'][0]

    assert private_group['url']


def test_model_includes_features(authenticated_request):
    feature_dict = {
        'feature_one': True,
        'feature_two': False,
    }
    authenticated_request.set_features(feature_dict)

    assert session.model(authenticated_request)['features'] == feature_dict


def test_anonymous_model_hides_sidebar_tutorial(unauthenticated_request):
    preferences = session.model(unauthenticated_request)['preferences']

    assert 'show_sidebar_tutorial' not in preferences


@pytest.mark.parametrize('dismissed', [True, False])
def test_authenticated_model_sidebar_tutorial(authenticated_request, dismissed):
    authenticated_request.set_sidebar_tutorial_dismissed(dismissed)

    preferences = session.model(authenticated_request)['preferences']

    if dismissed:
        assert 'show_sidebar_tutorial' not in preferences
    else:
        assert preferences['show_sidebar_tutorial'] is True


def test_profile_userid_unauthenticated(unauthenticated_request):
    assert session.profile(unauthenticated_request)['userid'] is None


def test_profile_userid_authenticated(authenticated_request):
    profile = session.profile(authenticated_request)
    assert profile['userid'] == u'acct:user@example.com'


def test_profile_sorts_groups(authenticated_request):
    authenticated_request.set_groups([
        FakeGroup('c', 'Group A'),
        FakeGroup('b', 'Group B'),
        FakeGroup('a', 'Group B'),
    ])
    profile = session.profile(authenticated_request)

    ids = [group['id'] for group in profile['groups']]

    assert ids == ['__world__', 'c', 'a', 'b']


def test_world_group_in_authenticated_profile(authenticated_request):
    result = session.profile(authenticated_request)

    assert '__world__' in [g['id'] for g in result['groups']]


def test_world_group_in_anonymous_profile(unauthenticated_request):
    result = session.profile(unauthenticated_request)

    assert '__world__' in [g['id'] for g in result['groups']]


def test_world_group_not_in_third_party_profile(third_party_request):
    result = session.profile(third_party_request)

    assert '__world__' not in [g['id'] for g in result['groups']]


def test_world_group_is_public_in_profile(authenticated_request):
    profile = session.profile(authenticated_request)
    world_group = [g for g in profile['groups'] if g['id'] == '__world__'][0]

    assert world_group['public'] is True


def test_private_group_is_not_public_in_profile(authenticated_request):
    authenticated_request.set_groups([FakeGroup('a', 'Group A')])

    profile = session.profile(authenticated_request)
    private_group = [g for g in profile['groups'] if g['id'] == 'a'][0]

    assert private_group['public'] is False


def test_publisher_group_is_public_in_profile(third_party_request, publisher_group):
    profile = session.profile(third_party_request)
    group = [g for g in profile['groups'] if g['id'] == publisher_group.pubid][0]

    assert group['public'] is True


def test_world_group_has_no_url_in_profile(authenticated_request):
    profile = session.profile(authenticated_request)
    world_group = [g for g in profile['groups'] if g['id'] == '__world__'][0]

    assert 'url' not in world_group


def test_private_group_has_url_in_profile(authenticated_request):
    authenticated_request.set_groups([FakeGroup('a', 'Group A')])

    profile = session.profile(authenticated_request)
    private_group = [g for g in profile['groups'] if g['id'] == 'a'][0]

    assert private_group['url']


def test_publisher_group_has_no_url_in_profile(third_party_request, publisher_group):
    profile = session.profile(third_party_request)
    group = [g for g in profile['groups'] if g['id'] == publisher_group.pubid][0]

    assert 'url' not in group


def test_profile_includes_features(authenticated_request):
    feature_dict = {
        'feature_one': True,
        'feature_two': False,
    }
    authenticated_request.set_features(feature_dict)

    assert session.profile(authenticated_request)['features'] == feature_dict


def test_anonymous_profile_hides_sidebar_tutorial(unauthenticated_request):
    preferences = session.profile(unauthenticated_request)['preferences']

    assert 'show_sidebar_tutorial' not in preferences


@pytest.mark.parametrize('dismissed', [True, False])
def test_authenticated_profile_sidebar_tutorial(authenticated_request, dismissed):
    authenticated_request.set_sidebar_tutorial_dismissed(dismissed)

    preferences = session.profile(authenticated_request)['preferences']

    if dismissed:
        assert 'show_sidebar_tutorial' not in preferences
    else:
        assert preferences['show_sidebar_tutorial'] is True


def test_authority_in_anonymous_profile(unauthenticated_request, auth_domain):
    assert session.profile(unauthenticated_request)['authority'] == auth_domain


def test_authority_override(unauthenticated_request):
    unauthenticated_request.set_public_groups({'foo.com': []})

    profile = session.profile(unauthenticated_request, 'foo.com')

    assert profile['authority'] == 'foo.com'


def test_authority_in_authenticated_profile(authenticated_request, auth_domain):
    assert session.profile(authenticated_request)['authority'] == auth_domain


def test_authority_ignored_for_authenticated_profile(authenticated_request, auth_domain):
    profile = session.profile(authenticated_request, 'foo.com')

    assert profile['authority'] == auth_domain


def test_authority_in_third_party_profile(third_party_request, third_party_domain):
    assert session.profile(third_party_request)['authority'] == third_party_domain


def test_authority_ignored_for_third_party_profile(third_party_request, third_party_domain):
    profile = session.profile(third_party_request, 'foo.com')

    assert profile['authority'] == third_party_domain


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
            self.authenticated_user = mock.Mock(groups=[], authority=user_authority)

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
def third_party_domain():
    return u'thirdparty.example.org'


@pytest.fixture
def world_group():
    return FakeGroup('__world__', 'Public', is_public=True)


@pytest.fixture
def publisher_group():
    return FakeGroup('abcdef', 'Publisher group', is_public=True)


@pytest.fixture
def unauthenticated_request(auth_domain, world_group):
    return FakeRequest(auth_domain, None, None, {auth_domain: [world_group]})


@pytest.fixture
def authenticated_request(auth_domain, world_group):
    return FakeRequest(auth_domain,
                       u'acct:user@{}'.format(auth_domain),
                       auth_domain,
                       {auth_domain: [world_group]})


@pytest.fixture
def third_party_request(auth_domain, third_party_domain, publisher_group):
    return FakeRequest(auth_domain,
                       u'acct:user@{}'.format(third_party_domain),
                       third_party_domain,
                       {third_party_domain: [publisher_group]})
