from pyramid.decorator import reify

from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker())
Base = declarative_base()

def includeme(config):
    """
    Configures the sqlalchemy engine from the application configuration, scans
    the package for ORM models, sets up the apex authentication system
    and configures the pyramid request factory.
    """

    # Create a SQLAlchemy engine based on the Pyramid Configurator's settings
    engine = engine_from_config(config.get_settings(), 'sqlalchemy.')

    # Set up the SQLAlchemy declarative configuration
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    # Set up request transaction management
    config.include('pyramid_tm')

    # Reify a database session on the request object
    maker = sessionmaker(bind=engine, extension=ZopeTransactionExtension)
    config.set_request_property(lambda request: maker(), 'db', reify=True)

    # Scan for all the models
    config.scan(__name__)
