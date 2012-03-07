from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Base = declarative_base()

def includeme(config):
    """Binds the SQLAlchemy engine and the ORM models to the application"""

    # Create a SQLAlchemy engine based on the Pyramid Configurator's settings
    engine = engine_from_config(config.get_settings(), 'sqlalchemy.')
    config.add_settings({'db.session_factory': sessionmaker(bind=engine)})

    # Set up the SQLAlchemy declarative configuration
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    # Scan for all the models
    config.scan(__name__)
