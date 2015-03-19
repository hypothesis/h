"""Unit tests for h/atom_feed.py."""
import pyramid.testing

import h.atom_feed as atom_feed
import h.test.factories as factories
import h.resources
import h.app


def test_entry_id():
    """Entry IDs should be tag URIs based on domain, day and annotation ID."""
    annotation = factories.Annotation(
        id="12345",
        html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert entry["id"] == "tag:example.com,2015-03-19:12345"


def test_entry_author_name():
    """Entries should have an author name based on the annotation user name."""
    annotation = factories.Annotation(
        username="jon", html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert entry["author"]["name"] == "jon"


def test_entry_title():
    """Entries should have a title based on the annotated document's title."""
    title = "My Test Document"
    annotation = factories.Annotation(
        document_title=title, html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert entry["title"] == title


def test_entry_published_date():
    datestring = "2015-03-18T12:44:17.551191+00:00"
    annotation = factories.Annotation(
        created=datestring,
        html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert entry["published"] == datestring


def test_entry_updated_date():
    datestring = "2015-03-19T11:27:17.551191+00:00"
    annotation = factories.Annotation(
        updated=datestring,
        html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert entry["updated"] == datestring


def test_entry_content_includes_selected_text():
    """The entry content should include the selected text in a blockquote."""
    text = "Some annotated text from a web page"
    annotation = factories.Annotation(
        exact_text=text,
        html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert (
        "&lt;blockquote&gt;{text}&lt;/blockquote&gt;".format(text=text)
        in entry["content"])


def test_entry_content_includes_annotation_text():
    """The entry content should include the annotation note."""
    text = "A test annotation"
    annotation = factories.Annotation(
        text=text, html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    assert text in entry["content"]


def test_entry_content_is_escaped():
    """'&', '<' and '>' should be escaped in entry contents."""
    text = "An annotation with <code>HTML</code> in it, &#374;"
    exact_text = "Some <b>web page</b> text &#355;"
    annotation = factories.Annotation(
        text=text, exact_text=exact_text,
        html_url="http://example.com/annotations/12345")

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    for s in ["<code>", "</code>", "<b>", "</b>", "&#374;", "&#355;"]:
        assert s not in entry["content"]


def test_html_link():
    """Entries should have links to their HTML representation."""
    html_url = "http://example.com/annotations/12345"
    annotation = factories.Annotation(html_url=html_url)

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    matching_links = [l for l in entry["links"]
                      if l["href"] == html_url]
    assert len(matching_links) == 1
    matching_link = matching_links[0]
    assert matching_link["rel"] == "alternate"
    assert matching_link["type"] == "text/html"


def test_json_link():
    """Entries should have links to their JSON representation."""
    html_url = "http://example.com/annotations/12345"
    json_url = "http://example.com/annotations/12345.json"
    annotation = factories.Annotation(html_url=html_url, json_url=json_url)

    feed = atom_feed._feed_from_annotations(
        [annotation], atom_url="http://www.example.com/annotations.atom")

    entry = feed["entries"][0]
    matching_links = [l for l in entry["links"]
                      if l["href"] == json_url]
    assert len(matching_links) == 1
    matching_link = matching_links[0]
    assert matching_link["rel"] == "alternate"
    assert matching_link["type"] == "application/json"


def test_feed_entries():
    """Feeds should contain the right entries in the right order."""
    html_url = "http://example.com/annotations/12345"
    annotations = [
        factories.Annotation(html_url=html_url, random_number=n)
        for n in range(1, 4)]

    feed = atom_feed._feed_from_annotations(
        annotations, atom_url="http://www.example.com/annotations.atom")

    assert [entry["title"] for entry in feed["entries"]] == [
        "Example Document 1", "Example Document 2", "Example Document 3"]


def test_feed_id():
    """The feed should use its own URL as its id."""
    atom_url = "http://example.com/annotations.atom"

    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url=atom_url)

    assert feed["id"] == atom_url


def test_feed_title():
    """A custom title should be used as the feed title if given."""
    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url="http://www.example.com/annotations.atom",
        title="My Custom Feed Title")

    assert feed["title"] == "My Custom Feed Title"


def test_default_feed_title():
    """It should fall back to the default feed title if none is given."""
    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url="http://www.example.com/annotations.atom")

    assert feed["title"] == "Hypothesis Stream"


def test_feed_subtitle():
    """A custom subtitle should be used as the feed subtitle if given."""
    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url="http://www.example.com/annotations.atom",
        subtitle="My Custom Feed Subtitle")

    assert feed["subtitle"] == "My Custom Feed Subtitle"


def test_default_feed_subtitle():
    """It should fall back to the default feed subtitle if none is given."""
    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url="http://www.example.com/annotations.atom")

    assert feed["subtitle"] == "The Web. Annotated"


def test_feed_self_link():
    """The given atom_url should be used in a rel="self" link."""
    atom_url = "http://www.example.com/annotations.atom"
    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url=atom_url)

    assert feed["links"][0]["href"] == atom_url
    assert feed["links"][0]["rel"] == "self"
    assert feed["links"][0]["type"] == "application/atom+xml"


def test_feed_html_link():
    """The given html_url should be used in a rel="alternate" link."""
    html_url = "http://www.example.com/annotations.html"
    feed = atom_feed._feed_from_annotations(
        annotations=factories.Annotation.create_batch(
            3, html_url="http://example.com/annotations/12345"),
        atom_url="http://www.example.com/annotations.atom",
        html_url=html_url)

    assert feed["links"][1]["href"] == html_url
    assert feed["links"][1]["rel"] == "alternate"
    assert feed["links"][1]["type"] == "text/html"


def test_render_feed_with_no_annotations():
    feed = atom_feed._feed_from_annotations(
        annotations=[],
        atom_url="http://www.example.com/annotations.atom")

    assert feed["entries"] == []


class TestAugmentAnnotations(object):

    def setup(self):
        self.request = pyramid.testing.DummyRequest()
        self.request.root = h.resources.create_root(self.request)

    def teardown(self):
        pyramid.testing.tearDown()

    def test_that_augment_annotations_adds_the_html_url(self):
        annotations = factories.Annotation.create_batch(3)

        augmented_annotations = atom_feed.augment_annotations(
            self.request, annotations)

        for annotation in augmented_annotations:
            assert annotation["html_url"] == (
                "http://example.com/a/{id_}".format(
                    id_=annotation["id"]))

    def test_that_augment_annotations_adds_the_json_url(self):
        annotations = factories.Annotation.create_batch(3)

        augmented_annotations = atom_feed.augment_annotations(
            self.request, annotations)

        for annotation in augmented_annotations:
            assert annotation["json_url"] == (
                "http://example.com/api/annotation/{id_}".format(
                    id_=annotation["id"]))
