"""
AppTestCase is a subclass of unittest.TestCase for writing unit tests
that will have access to a clean h database.
"""

from unittest import TestCase

from paste.deploy.loadwsgi import appconfig
from pyramid import testing
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from h.models import Base
from h import api
from annotator import annotation, document, es

settings = appconfig('config:test.ini', relative_to='.')

class AppTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = engine_from_config(settings)
        cls.Session = sessionmaker(autoflush=False, autocommit=True)
        #config = testing.setUp(settings=settings)
        #self.app = api.includeme(config)

    def setUp(self):
        self.connection = self.engine.connect()
        self.session = self.Session(bind=self.connection)
        Base.metadata.bind = self.connection
        Base.metadata.create_all(self.engine)

        #annotation.Annotation.drop_all()
        #annotation.Annotation.create_all()
        #document.Document.drop_all()
        #document.Document.create_all()

    def tearDown(self):
        # empty out the database
        for table in reversed(Base.metadata.sorted_tables):
            self.connection.execute(table.delete())
        self.session.close()


