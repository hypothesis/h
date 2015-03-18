"""Factory classes for easily generating test objects."""
import random
import datetime

import factory


class Annotation(factory.Factory):

    """A factory class that generates test annotation dicts.

    Usage:

        annotation_1 = Annotation()
        annotation_2 = Annotation()

    A unique "id" and "text", "created" and "updated" strings based on the
    current time, etc. are generated for each annotation dict returned.

    You can override the value of any attribute by passing in named arguments,
    for example:

        annotation = Annotation(text="My annotation text")

    There are some special params that don't appear in the annotation dicts
    themselves but influence the values that do appear in the dicts.

    For example:

        annotation = Annotation(username="my_user")

    will create an annotation with "user": "acct:my_user@127.0.0.1".

        annotation = Annotation(num_tags=3)

    will create an annotation with 3 (randomly generated) tags.
    Without this argument the number of tags is chosen at random (and may be
    zero).

    To choose the actual values of the tags do:

        annotation = Annotation(tags=["foo", "bar"])

    A random number is generated for each annotation and used in the URI
    ("http://example.com/document_3"), document title ("Example Document 3"),
    etc. To choose this number do:

        annotation = Annotation(random_number=7)


    """

    class Meta:
        model = dict
        exclude = ["username", "random_number", "num_tags"]

    username = "seanh"
    random_number = factory.LazyAttribute(lambda n: random.randint(1, 10))
    num_tags = None

    id = factory.Sequence(lambda n: "test_id_{n}".format(n=n + 1))
    text = factory.Sequence(lambda n: "Test annotation {n}".format(n=n + 1))
    user = factory.LazyAttribute(
        lambda n: "acct:{username}@127.0.0.1".format(username=n.username))
    consumer = "nosuchid"

    @factory.LazyAttribute
    def created(stub):
        return datetime.datetime.now().isoformat()

    updated = factory.SelfAttribute('created')

    @factory.LazyAttribute
    def tags(stub):
        num = (stub.num_tags if stub.num_tags is not None else
               random.randint(1, 11))
        return ["tag_{n}".format(n=n) for n in range(1, num + 1)]

    @factory.LazyAttribute
    def uri(stub):
        return "http://example.com/document_{n}".format(n=stub.random_number)

    @factory.LazyAttribute
    def target(stub):
        return [{
            "source": stub.uri,
            "pos": {"top": 200.00, "height": 20},
            "selector": [
                {"type": "RangeSelector",
                 "startContainer": "/div[1]/article[1]/",
                 "endContainer": "/div[1]/article[1]/section[1]",
                 "startOffset": 0,
                 "endOffset": 43},
                {"start": 211,
                 "end": 254,
                 "type": "TextPositionSelector"},
                {"type": "TextQuoteSelector",
                 "prefix": "text quote prefix",
                 "exact": "The exact text that was selected",
                 "suffix": "text quote suffix"},
                {"type": "FragmentSelector",
                 "value": ""}
            ]
        }]

    @factory.LazyAttribute
    def permissions(stub):
        return {
            "admin": [stub.user],
            "read": ["group:__world__"],
            "update": [stub.user],
            "delete": [stub.user]
        }

    @factory.LazyAttribute
    def document(stub):
        return {
            "eprints": {},
            "title": "Example Document {n}".format(n=stub.random_number),
            "twitter": {},
            "dc": {},
            "prism": {},
            "highwire": {},
            "facebook": {},
            "link": [{"href": stub.uri}]
        }
