import datetime
import random
import uuid

import factory
from sqlalchemy import orm

from h import models
from h.db.types import URLSafeUUID
from h.models.document import update_document_metadata

from .base import FAKER, ModelFactory
from .document import Document, DocumentMeta, DocumentURI


class Annotation(ModelFactory):
    class Meta:
        model = models.Annotation
        sqlalchemy_session_persistence = (
            "flush"  # Always flush the db to generate annotation.id.
        )

    tags = factory.LazyFunction(
        lambda: list(FAKER.words(nb=random.randint(0, 5)))  # pylint:disable=no-member
    )
    target_uri = factory.Faker("uri")
    text = factory.Faker("paragraph")
    userid = factory.LazyFunction(
        lambda: f"acct:{FAKER.user_name()}@localhost"  # pylint:disable=no-member
    )
    document = factory.SubFactory(Document)
    groupid = "__world__"

    @factory.lazy_attribute
    def target_selectors(self):
        return [
            {
                "endContainer": "/div[1]/article[1]/section[1]/div[1]/div[2]/div[1]",
                "endOffset": 76,
                "startContainer": "/div[1]/article[1]/section[1]/div[1]/div[2]/div[1]",
                "startOffset": 0,
                "type": "RangeSelector",
            },
            {"end": 362, "start": 286, "type": "TextPositionSelector"},
            {
                # pylint: disable=line-too-long
                "exact": "If you wish to install Hypothesis on your own site then head over to GitHub.",
                "prefix": " browser extension.\n            ",
                "suffix": "\n          \n        \n      \n    ",
                "type": "TextQuoteSelector",
            },
        ]

    @factory.post_generation
    def make_metadata(  # pylint:disable=unused-argument
        self, create, extracted, **kwargs
    ):
        """Create associated document metadata for the annotation."""
        # The metadata objects are going to be added to the db, so if we're not
        # using the create strategy then simply don't make any.
        if not create:
            return

        def document_uri_dict():
            """
            Return a randomly generated DocumentURI dict for this annotation.

            This doesn't add anything to the database session yet.
            """
            document_uri = DocumentURI.build(
                document=None, claimant=self.target_uri, uri=self.target_uri
            )
            return dict(
                claimant=document_uri.claimant,
                uri=document_uri.uri,
                type=document_uri.type,
                content_type=document_uri.content_type,
            )

        document_uri_dicts = [document_uri_dict() for _ in range(random.randint(1, 3))]

        def document_meta_dict(type_=None):
            """
            Return a randomly generated DocumentMeta dict for this annotation.

            This doesn't add anything to the database session yet.
            """
            kwargs = {"document": None, "claimant": self.target_uri}

            if type_ is not None:
                kwargs["type"] = type_

            document_meta = DocumentMeta.build(**kwargs)

            return dict(
                claimant=document_meta.claimant,
                type=document_meta.type,
                value=document_meta.value,
            )

        document_meta_dicts = [
            document_meta_dict() for _ in range(random.randint(1, 3))
        ]

        # Make sure that there's always at least one DocumentMeta with
        # type='title', so that we never get annotation.document.title is None:
        if "title" not in [m["type"] for m in document_meta_dicts]:
            document_meta_dicts.append(document_meta_dict(type_="title"))

        self.document = update_document_metadata(
            orm.object_session(self),
            self.target_uri,
            document_meta_dicts=document_meta_dicts,
            document_uri_dicts=document_uri_dicts,
            created=self.created,
            updated=self.updated,
        )

    @factory.post_generation
    def make_id(self, create, extracted, **kwargs):  # pylint:disable=unused-argument
        """Add a randomly ID if the annotation doesn't have one yet."""
        # If using the create strategy don't generate an id.
        # models.Annotation.id's server_default function will generate one
        # when the annotation is saved to the DB.
        if create:
            return

        # Don't generate an id if the user passed in one of their own.
        if getattr(self, "id", None):
            return

        # Ids in the DB are in hex, but in the code they should be URL safe
        self.id = URLSafeUUID().process_result_value(  # pylint:disable=attribute-defined-outside-init,invalid-name
            uuid.uuid4().hex, None
        )

    @factory.post_generation
    def timestamps(self, create, extracted, **kwargs):  # pylint:disable=unused-argument
        # If using the create strategy let sqlalchemy set the created and
        # updated times when saving to the DB.
        if create:
            return

        # When using the build or stub strategy sqlalchemy won't set created or updated
        # times for us, so do it ourselves instead.
        #
        # We're generating created and updated separately (calling now() twice
        # instead of just once) so created and updated won't be exactly the
        # same. This is consistent with how models.Annotation does it when
        # saving to the DB.
        # pylint:disable=attribute-defined-outside-init
        self.created = self.created or datetime.datetime.now()
        self.updated = self.updated or datetime.datetime.now()
