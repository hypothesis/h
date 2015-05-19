# pylint: disable=no-self-use
"""Unit tests for h/test/factories.py."""
import datetime

import h.test.factories as factories


class TestAnnotation(object):

    """Unit tests for the Annotation factory class."""

    def test_id(self):
        """Each test annotation should be created with a unique ID."""
        annotation_1 = factories.Annotation()
        annotation_2 = factories.Annotation()

        assert annotation_1.get("id")
        assert annotation_2.get("id")
        assert annotation_1["id"] != annotation_2["id"]

    def test_text(self):
        """Each annotation should have unique note text."""
        annotation_1 = factories.Annotation()
        annotation_2 = factories.Annotation()

        assert annotation_1.get("text")
        assert annotation_2.get("text")
        assert annotation_1["text"] != annotation_2["text"]

    def test_custom_user(self):
        """A custom username should be used in the user field."""
        annotation = factories.Annotation(username="bobo")
        assert "bobo" in annotation["user"]
        assert "username" not in annotation

    def test_created_date(self):
        """Annotations should have a created date from the current time."""
        before = datetime.datetime.now()

        annotation = factories.Annotation()

        after = datetime.datetime.now()
        created = datetime.datetime.strptime(
            annotation["created"], "%Y-%m-%dT%H:%M:%S.%f")

        assert before < created < after

    def test_updated_date(self):
        """Annotations should have an updated date from the current time."""
        before = datetime.datetime.now()

        annotation = factories.Annotation()

        after = datetime.datetime.now()
        updated = datetime.datetime.strptime(
            annotation["updated"], "%Y-%m-%dT%H:%M:%S.%f")

        assert before < updated < after

    def test_tags(self):
        """It should be possible to choose the number of tags with num_tags."""
        # If num_tags isn't passed the factory chooses a random number of tags.
        # Here we choose a num_tags higher than the upper range of this random
        # choice, so there's no chance of random false positive test passes.
        annotation = factories.Annotation(num_tags=20)
        assert len(annotation["tags"]) == 20
        assert "num_tags" not in annotation

    def test_custom_tags(self):
        assert factories.Annotation(tags=["foo", "bar", "gar"])["tags"] == [
            "foo", "bar", "gar"]

    def test_uri(self):
        annotation = factories.Annotation(random_number=3)
        assert annotation["uri"] == "http://example.com/document_3"
        assert "random_number" not in annotation

    def test_source(self):
        annotation = factories.Annotation(random_number=3)
        assert annotation["target"][0]["source"] == (
            "http://example.com/document_3")

    def test_permissions(self):
        annotation = factories.Annotation(username="test_user")
        assert "test_user" in annotation["permissions"]["admin"][0]
        assert "test_user" in annotation["permissions"]["update"][0]
        assert "test_user" in annotation["permissions"]["delete"][0]

    def test_document_title(self):
        assert factories.Annotation(random_number=30)["document"]["title"] == (
            "Example Document 30")

    def test_document_link(self):
        annotation = factories.Annotation(random_number=30)
        assert annotation["document"]["link"][0]["href"] == (
            "http://example.com/document_30")
