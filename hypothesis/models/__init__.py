from pyramid.decorator import reify

from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

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
    DBSession.configure(bind=engine)

    # Set up the SQLAlchemy declarative configuration
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine)

    # Reify the database session maker on the request object
    config.set_request_property(lambda request: maker(), 'db', reify=True)

    # Add settings for apex authentication system
    config.add_settings({
        'apex.apex_template': 'hypothesis:templates/forms/auth.jinja2',
        'apex.register_form_class': 'hypothesis.forms.auth.RegisterForm',
        'apex.use_request_factory': False
    })
    config.include('apex', route_prefix='/auth')

    # Reify the authenticated user on the request object
    config.set_request_property(
        'apex.RequestFactory.user.wrapped', 'user', reify=True)

    # Scan for all the models
    config.scan(__name__)
