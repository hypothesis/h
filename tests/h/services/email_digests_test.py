import datetime

import pytest
from h_matchers import Any

from h.services.email_digests import EmailDigestsService


def test_it(svc, group_service, factories):
    since = datetime.datetime(year=2023, month=2, day=7)
    until = datetime.datetime(year=2023, month=2, day=8)

    user = factories.User()
    groups = factories.Group.create_batch(size=2, members=[user])
    group_service.groupids_readable_by.return_value = groups

    other_user = factories.User()
    other_group = factories.Group()

    nipsad_user = factories.User(nipsa=True)

    class AnnotationFactory(factories.Annotation):
        """A factory that creates matching annotations by default."""
        userid = other_user.userid
        shared = True
        deleted = False
        groupid = groups[0].pubid
        updated = since + ((until - since) / 2)

    # Create some annotations that *should* be counted.
    # The first group should have a count of one annotation.
    AnnotationFactory()
    # The second group should have a count of two annotations.
    AnnotationFactory.create_batch(size=2, groupid=groups[1].pubid)

    # Create some annotations that should *not* be counted.
    AnnotationFactory(deleted=True)
    AnnotationFactory(shared=False)
    AnnotationFactory(userid=user.userid)
    AnnotationFactory(groupid=other_group.pubid)
    AnnotationFactory(updated=until + datetime.timedelta(seconds=1))
    AnnotationFactory(updated=since - datetime.timedelta(seconds=1))
    AnnotationFactory(userid=nipsad_user.userid)

    # An annotation that shouldn't be counted because it has been hidden by moderation.
    hidden_annotation = AnnotationFactory()
    hidden_annotation.moderation = factories.AnnotationModeration(
        annotation=hidden_annotation
    )

    result = svc.get(user, since, until)

    assert (
        result
        == Any.iterable.containing([(groups[0].pubid, 1), (groups[1].pubid, 2)]).only()
    )
    group_service.groupids_readable_by.assert_called_once_with(user)
    assert False


@pytest.fixture
def svc(db_session, group_service):
    return EmailDigestsService(db_session, group_service)
