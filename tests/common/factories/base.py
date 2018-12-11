# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import factory
import faker

FAKER = faker.Factory.create()
SESSION = None


def set_session(value):
    global SESSION

    SESSION = value


class ModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # We override SQLAlchemyModelFactory's default _create classmethod so
        # that rather than fetching the session from cls._meta (which is
        # created at parse time... ugh) we fetch it from the SESSION global,
        # which is dynamically filled out by the `factories` fixture when
        # used.
        if SESSION is None:
            raise RuntimeError("no session: did you use the factories fixture?")
        obj = model_class(*args, **kwargs)
        SESSION.add(obj)
        if cls._meta.sqlalchemy_session_persistence == "flush":
            SESSION.flush()
        return obj
