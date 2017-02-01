import pytest
import mock

from h import session


class FakeGroup(object):
    def __init__(self, pubid, name):
        self.pubid = pubid
        self.name = name
        self.slug = pubid


def test_model_sorts_groups(authenticated_request):
    authenticated_request.set_groups([
        FakeGroup('c', 'Group A'),
        FakeGroup('b', 'Group B'),
        FakeGroup('a', 'Group B'),
    ])
    session_model = session.model(authenticated_request)

    ids = [group['id'] for group in session_model['groups']]

    assert ids == ['__world__', 'c', 'a', 'b']


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


class FakeRequest(object):

    def __init__(self, auth_domain, userid, user_authority):
        self.auth_domain = auth_domain
        self.authenticated_userid = userid

        if userid is None:
            self.authenticated_user = None
        else:
            self.authenticated_user = mock.Mock(groups=[], authority=user_authority)

        self.feature = mock.Mock(spec_set=['all'])
        self.route_url = mock.Mock(return_value='/group/a')
        self.session = mock.Mock(get_csrf_token=lambda: '__CSRF__')

    def set_groups(self, groups):
        self.authenticated_user.groups = groups

    def set_features(self, feature_dict):
        self.feature.all.return_value = feature_dict

    def set_sidebar_tutorial_dismissed(self, dismissed):
        self.authenticated_user.sidebar_tutorial_dismissed = dismissed


@pytest.fixture
def auth_domain():
    return u'example.com'


@pytest.fixture
def unauthenticated_request(auth_domain):
    return FakeRequest(auth_domain, None, None)


@pytest.fixture
def authenticated_request(auth_domain):
    return FakeRequest(auth_domain,
                       u'acct:user@{}'.format(auth_domain),
                       auth_domain)
