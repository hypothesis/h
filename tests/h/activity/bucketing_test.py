import datetime
from unittest.mock import Mock

import pytest

from h.activity import bucketing
from tests.common import factories

UTCNOW = datetime.datetime(year=1970, month=2, day=21, hour=19, minute=30)
FIVE_MINS_AGO = UTCNOW - datetime.timedelta(minutes=5)
YESTERDAY = UTCNOW - datetime.timedelta(days=1)
THIRD_MARCH_1968 = datetime.datetime(year=1968, month=3, day=3)
FIFTH_NOVEMBER_1969 = datetime.datetime(year=1969, month=11, day=5)


class timeframe_with:
    def __init__(self, label, document_buckets):
        self.label = label
        self.document_buckets = document_buckets

    def __eq__(self, timeframe):
        return (
            self.label == timeframe.label
            and self.document_buckets == timeframe.document_buckets
        )

    # pragma: nocover
    def __repr__(self):  # pragma: nocover
        return f'{self.__class__} "{self.label}" with {len(self.document_buckets)} document buckets'  # pragma: nocover


@pytest.mark.usefixtures("factories")
class TestDocumentBucket:
    def test_init_sets_the_document_title(self, db_session, document):
        title_meta = factories.DocumentMeta(
            type="title", value=["The Document Title"], document=document
        )
        document.title = "The Document Title"
        db_session.add(title_meta)
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.title == "The Document Title"

    def test_init_uses_the_document_web_uri(self, document):
        document.web_uri = "http://example.com"

        bucket = bucketing.DocumentBucket(document)
        assert bucket.uri == "http://example.com"

    def test_init_sets_None_uri_when_no_http_or_https_can_be_found(self, document):
        document.web_uri = None

        bucket = bucketing.DocumentBucket(document)
        assert bucket.uri is None

    def test_init_sets_the_domain_from_the_extracted_uri(self, document):
        document.web_uri = "https://www.example.com/foobar.html"

        bucket = bucketing.DocumentBucket(document)
        assert bucket.domain == "www.example.com"

    def test_init_sets_domain_to_local_file_when_no_uri_is_set(
        self, db_session, document
    ):
        docuri_pdf = factories.DocumentURI(
            uri="urn:x-pdf:fingerprint", document=document
        )
        db_session.add(docuri_pdf)
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.domain == "Local file"

    def test_annotations_count_returns_count_of_annotations(self, document):
        bucket = bucketing.DocumentBucket(document)

        for _ in range(7):
            annotation = factories.Annotation()
            bucket.append(annotation)

        assert bucket.annotations_count == 7

    def test_append_appends_the_annotation(self, document):
        bucket = bucketing.DocumentBucket(document)

        annotations = []
        for _ in range(7):
            annotation = factories.Annotation()
            annotations.append(annotation)
            bucket.append(annotation)

        assert bucket.annotations == annotations

    def test_append_adds_unique_annotation_tag_to_bucket(self, document):
        ann_1 = factories.Annotation(tags=["foo", "bar"])
        ann_2 = factories.Annotation(tags=["foo", "baz"])

        bucket = bucketing.DocumentBucket(document)
        bucket.append(ann_1)
        bucket.append(ann_2)
        assert bucket.tags == {"foo", "bar", "baz"}

    def test_append_adds_unique_annotation_user_to_bucket(self, document):
        ann_1 = factories.Annotation(userid="luke")
        ann_2 = factories.Annotation(userid="alice")
        ann_3 = factories.Annotation(userid="luke")

        bucket = bucketing.DocumentBucket(document)
        bucket.append(ann_1)
        bucket.append(ann_2)
        bucket.append(ann_3)
        assert bucket.users == {"luke", "alice"}

    def test_eq(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        for _ in range(5):
            annotation = factories.Annotation()
            bucket_1.append(annotation)
            bucket_2.append(annotation)

        assert bucket_1 == bucket_2

    def test_eq_annotations_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.annotations = [1, 2, 3]
        bucket_2.annotations = [2, 3, 4]

        assert bucket_1 != bucket_2

    def test_eq_tags_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.tags.update(["foo", "bar"])
        bucket_2.tags.update(["foo", "baz"])

        assert bucket_1 != bucket_2

    def test_eq_users_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.users.update(["alice", "luke"])
        bucket_2.users.update(["luke", "paula"])

        assert bucket_1 != bucket_2

    def test_eq_uri_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.uri = "http://example.com"
        bucket_2.uri = "http://example.org"

        assert bucket_1 != bucket_2

    def test_eq_domain_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.domain = "example.com"
        bucket_2.domain = "example.org"

        assert bucket_1 != bucket_2

    def test_eq_title_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.title = "First Title"
        bucket_2.title = "Second Title"

        assert bucket_1 != bucket_2

    def test_incontext_link_returns_link_to_first_annotation(self, document, patch):
        incontext_link = patch("h.links.incontext_link")
        bucket = bucketing.DocumentBucket(document)
        ann = factories.Annotation()
        bucket.append(ann)
        request = Mock()

        assert bucket.incontext_link(request) == incontext_link.return_value

    def test_incontext_link_returns_none_if_bucket_empty(self, document, patch):
        patch("h.links.incontext_link")
        bucket = bucketing.DocumentBucket(document)
        request = Mock()

        assert bucket.incontext_link(request) is None

    @pytest.fixture
    def document(self, db_session):
        document = factories.Document()
        db_session.add(document)
        db_session.flush()
        return document


@pytest.mark.usefixtures("factories", "utcnow")
class TestBucket:
    def test_no_annotations(self):
        assert not bucketing.bucket([])

    @pytest.mark.parametrize(
        "annotation_datetime,timeframe_label",
        [(FIVE_MINS_AGO, "Last 7 days"), (THIRD_MARCH_1968, "Mar 1968")],
    )
    def test_one_annotation(self, annotation_datetime, timeframe_label):
        annotation = factories.Annotation(
            document=factories.Document(), updated=annotation_datetime
        )

        timeframes = bucketing.bucket([annotation])

        assert timeframes == [
            timeframe_with(
                timeframe_label,
                {
                    annotation.document: bucketing.DocumentBucket(
                        annotation.document, [annotation]
                    )
                },
            )
        ]

    @pytest.mark.parametrize(
        "annotation_datetime,timeframe_label",
        [(FIVE_MINS_AGO, "Last 7 days"), (THIRD_MARCH_1968, "Mar 1968")],
    )
    def test_multiple_annotations_of_one_document_in_one_timeframe(
        self, annotation_datetime, timeframe_label
    ):
        results = [
            factories.Annotation(
                target_uri="https://example.com", updated=annotation_datetime
            )
            for _ in range(3)
        ]

        timeframes = bucketing.bucket(results)

        document = results[0].document
        assert timeframes == [
            timeframe_with(
                timeframe_label, {document: bucketing.DocumentBucket(document, results)}
            )
        ]

    @pytest.mark.parametrize(
        "annotation_datetime,timeframe_label",
        [(YESTERDAY, "Last 7 days"), (THIRD_MARCH_1968, "Mar 1968")],
    )
    def test_annotations_of_multiple_documents_in_one_timeframe(
        self, annotation_datetime, timeframe_label
    ):
        annotation_1 = factories.Annotation(
            target_uri="http://example1.com", updated=annotation_datetime
        )
        annotation_2 = factories.Annotation(
            target_uri="http://example2.com", updated=annotation_datetime
        )
        annotation_3 = factories.Annotation(
            target_uri="http://example3.com", updated=annotation_datetime
        )

        timeframes = bucketing.bucket([annotation_1, annotation_2, annotation_3])

        assert timeframes == [
            timeframe_with(
                timeframe_label,
                {
                    annotation_1.document: bucketing.DocumentBucket(
                        annotation_1.document, [annotation_1]
                    ),
                    annotation_2.document: bucketing.DocumentBucket(
                        annotation_2.document, [annotation_2]
                    ),
                    annotation_3.document: bucketing.DocumentBucket(
                        annotation_3.document, [annotation_3]
                    ),
                },
            )
        ]

    def test_annotations_of_the_same_document_in_different_timeframes(self):
        results = [
            factories.Annotation(),
            factories.Annotation(updated=FIFTH_NOVEMBER_1969),
            factories.Annotation(updated=THIRD_MARCH_1968),
        ]
        document = factories.Document()
        for annotation in results:
            annotation.document = document

        timeframes = bucketing.bucket(results)

        expected_bucket_1 = bucketing.DocumentBucket(document, [results[0]])
        expected_bucket_2 = bucketing.DocumentBucket(document, [results[1]])
        expected_bucket_3 = bucketing.DocumentBucket(document, [results[2]])

        assert timeframes == [
            timeframe_with("Last 7 days", {document: expected_bucket_1}),
            timeframe_with("Nov 1969", {document: expected_bucket_2}),
            timeframe_with("Mar 1968", {document: expected_bucket_3}),
        ]

    def test_recent_and_older_annotations_together(self):
        results = [
            factories.Annotation(target_uri="http://example1.com"),
            factories.Annotation(target_uri="http://example2.com"),
            factories.Annotation(target_uri="http://example3.com"),
            factories.Annotation(
                target_uri="http://example4.com", updated=THIRD_MARCH_1968
            ),
            factories.Annotation(
                target_uri="http://example5.com", updated=THIRD_MARCH_1968
            ),
            factories.Annotation(
                target_uri="http://example6.com", updated=THIRD_MARCH_1968
            ),
        ]

        timeframes = bucketing.bucket(results)

        expected_bucket_1 = bucketing.DocumentBucket(results[0].document, [results[0]])
        expected_bucket_2 = bucketing.DocumentBucket(results[1].document, [results[1]])
        expected_bucket_3 = bucketing.DocumentBucket(results[2].document, [results[2]])
        expected_bucket_4 = bucketing.DocumentBucket(results[3].document, [results[3]])
        expected_bucket_5 = bucketing.DocumentBucket(results[4].document, [results[4]])
        expected_bucket_6 = bucketing.DocumentBucket(results[5].document, [results[5]])

        assert timeframes == [
            timeframe_with(
                "Last 7 days",
                {
                    results[0].document: expected_bucket_1,
                    results[1].document: expected_bucket_2,
                    results[2].document: expected_bucket_3,
                },
            ),
            timeframe_with(
                "Mar 1968",
                {
                    results[3].document: expected_bucket_4,
                    results[4].document: expected_bucket_5,
                    results[5].document: expected_bucket_6,
                },
            ),
        ]

    def test_annotations_from_different_days_in_same_month(self):
        """
        Test bucketing multiple annotations from different days of same month.

        Annotations from different days of the same month should go into one
        bucket.

        """
        one_month_ago = UTCNOW - datetime.timedelta(days=30)
        annotations = [
            factories.Annotation(
                target_uri="http://example.com", updated=one_month_ago
            ),
            factories.Annotation(
                target_uri="http://example.com",
                updated=one_month_ago - datetime.timedelta(days=1),
            ),
            factories.Annotation(
                target_uri="http://example.com",
                updated=one_month_ago - datetime.timedelta(days=2),
            ),
        ]

        timeframes = bucketing.bucket(annotations)

        expected_bucket = bucketing.DocumentBucket(annotations[0].document)
        expected_bucket.update(annotations)

        assert timeframes == [
            timeframe_with("Jan 1970", {annotations[0].document: expected_bucket})
        ]

    @pytest.fixture
    def utcnow(self, patch):
        utcnow = patch("h.activity.bucketing.utcnow")
        utcnow.return_value = UTCNOW
        return utcnow
