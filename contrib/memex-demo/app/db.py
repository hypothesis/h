# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from memex.db import init

Session = sessionmaker()


def db(request):
    engine = request.registry['sqlalchemy.engine']
    session = Session(bind=engine)

    def cleanup(request):
        if request.exception is not None:
            session.rollback()
        else:
            session.commit()
        session.close()
    request.add_finished_callback(cleanup)

    return session


def includeme(config):
    settings = config.registry.settings

    engine = create_engine(settings['sqlalchemy.url'])
    config.registry['sqlalchemy.engine'] = engine

    config.add_request_method(db, reify=True)

    config.action(None,
                  init,
                  args=(engine,),
                  kw={'should_create': True},
                  order=10)
