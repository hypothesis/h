from pyramid.decorator import reify

from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from apex import RequestFactory

DBSession = scoped_session(sessionmaker())
Base = declarative_base()

class HypothesisRequestFactory(RequestFactory):
    @reify
    def db(self):
        self.registry.settings['db.sessionmaker']()
    

def includeme(config):
    """
    Configures the sqlalchemy engine from the application configuration, scans
    the package for ORM models, sets up the apex authentication system
    and configures the pyramid request factory.
    """

    # Create a SQLAlchemy engine based on the Pyramid Configurator's settings
    engine = engine_from_config(config.get_settings(), 'sqlalchemy.')
    DBSession.configure(bind=engine)

    # Add a setting to the registry for easy access to the sessionmaker
    config.add_settings({'db.sessionmaker': sessionmaker(bind=engine)})

    # Set up the SQLAlchemy declarative configuration
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    # Scan for all the models
    config.scan(__name__)

    # Set up the apex system
    config.add_settings({
        'apex.apex_template': 'hypothesis:templates/forms/auth.jinja2',
        'apex.register_form_class': 'hypothesis.models.auth.RegisterForm',
        'apex.use_request_factory': False
    })
    config.include('apex', route_prefix='/auth')

    # Register the request factory
    config.set_request_factory(HypothesisRequestFactory)
