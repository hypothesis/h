import datetime
import pytest

from h.activity import bucketing
from tests.common import factories


UTCNOW = datetime.datetime(year=1970, month=2, day=21, hour=19, minute=30)
FIVE_MINS_AGO = UTCNOW - datetime.timedelta(minutes=5)
YESTERDAY = UTCNOW - datetime.timedelta(days=1)
THIRD_MARCH_1968 = datetime.datetime(year=1968, month=3, day=3)
FIFTH_NOVEMBER_1969 = datetime.datetime(year=1969, month=11, day=5)


class TimeframeMatcher(object):

    def __init__(self, label, document_buckets):
        self.label = label
        self.document_buckets = document_buckets

    def __eq__(self, timeframe):
        return (self.label == timeframe.label and
                self.document_buckets == timeframe.document_buckets)

    def __repr__(self):
        return '{class_} "{label}" with {n} document buckets'.format(
            class_=self.__class__, label=self.label,
            n=len(self.document_buckets))


@pytest.mark.usefixtures('factories', 'utcnow')
class TestBucket(object):

    def test_no_annotations(self):
        assert bucketing.bucket([]) == []

    @pytest.mark.parametrize('annotation_datetime,timeframe_label', [
        (FIVE_MINS_AGO, 'Last 7 days'),
        (THIRD_MARCH_1968, 'Mar 1968'),
    ])
    def test_one_annotation(self, annotation_datetime, timeframe_label):
        document = factories.Document()
        results = [self.result(document=document, updated=annotation_datetime)]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher(timeframe_label, {document: results})
        ]

    @pytest.mark.parametrize('annotation_datetime,timeframe_label', [
        (FIVE_MINS_AGO, 'Last 7 days'),
        (THIRD_MARCH_1968, 'Mar 1968'),
    ])
    def test_multiple_annotations_of_one_document_in_one_timeframe(
            self, annotation_datetime, timeframe_label):
        document = factories.Document()
        results = [
            self.result(document=document, updated=annotation_datetime)
            for _ in range(3)]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher(timeframe_label, {document: results}),
        ]

    @pytest.mark.parametrize("annotation_datetime,timeframe_label", [
        (YESTERDAY, "Last 7 days"),
        (THIRD_MARCH_1968, "Mar 1968"),
    ])
    def test_annotations_of_multiple_documents_in_one_timeframe(
            self, annotation_datetime, timeframe_label):
        document_1 = factories.Document()
        document_2 = factories.Document()
        document_3 = factories.Document()
        results = [
            self.result(document=document_1, updated=annotation_datetime),
            self.result(document=document_2, updated=annotation_datetime),
            self.result(document=document_3, updated=annotation_datetime),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher(timeframe_label, {
                document_1: [results[0]],
                document_2: [results[1]],
                document_3: [results[2]],
            }),
        ]

    def test_annotations_of_the_same_document_in_different_timeframes(self):
        document = factories.Document()
        results = [
            self.result(document=document),
            self.result(document=document, updated=FIFTH_NOVEMBER_1969),
            self.result(document=document, updated=THIRD_MARCH_1968),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher('Last 7 days', {document: [results[0]]}),
            TimeframeMatcher('Nov 1969', {document: [results[1]]}),
            TimeframeMatcher('Mar 1968', {document: [results[2]]}),
        ]

    def test_recent_and_older_annotations_together(self):
        document_1 = factories.Document()
        document_2 = factories.Document()
        document_3 = factories.Document()
        document_4 = factories.Document()
        document_5 = factories.Document()
        document_6 = factories.Document()
        results = [
            self.result(document=document_1),
            self.result(document=document_2),
            self.result(document=document_3),
            self.result(document=document_4, updated=THIRD_MARCH_1968),
            self.result(document=document_5, updated=THIRD_MARCH_1968),
            self.result(document=document_6, updated=THIRD_MARCH_1968),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher('Last 7 days', {
                document_1: [results[0]],
                document_2: [results[1]],
                document_3: [results[2]],
            }),
            TimeframeMatcher('Mar 1968', {
                document_4: [results[3]],
                document_5: [results[4]],
                document_6: [results[5]],
            }),
        ]

    def test_annotations_from_different_days_in_same_month(self):
        """
        Test bucketing multiple annotations from different days of same month.

        Annotations from different days of the same month should go into one
        bucket.

        """
        document = factories.Document()
        one_month_ago = UTCNOW - datetime.timedelta(days=30)
        results = [
            self.result(document=document, updated=one_month_ago),
            self.result(document=document,
                        updated=one_month_ago - datetime.timedelta(days=1)),
            self.result(document=document,
                        updated=one_month_ago - datetime.timedelta(days=2)),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher('Jan 1970', {document: results})]


    def result(self, *args, **kwargs):
        return {'annotation': factories.Annotation(*args, **kwargs)}

    @pytest.fixture
    def utcnow(self, patch):
        utcnow = patch('h.activity.bucketing.utcnow')
        utcnow.return_value = UTCNOW
        return utcnow
